"""Verified Bytefray Spectator presentations for completed V6 alpha1 matches.

Bytefray owns the interpretation of its own match artifacts; Bytefray
Spectator (a separate Godot application) only plays the files this module
writes. A presentation directory holds three files:

* ``broadcast.json`` - the omniscient presentation, one frame per verified
  exchange fact, built from ``SensingCursor(entrant_id=None)``;
* ``agent_a.json``   - Agent A's presentation, built *only* from the
  receipt-only ``SensingView`` objects of ``SensingCursor(entrant_id="A")``;
* ``manifest.json``  - provenance, verification outcome and SHA-256 digests.

The source is an ordinary completed match directory (``result.json``, the
replay it references and the sibling ``trace.jsonl``), exactly what Designer
and ``bytefray run --trace`` write. Its provenance is the canonical result
envelope itself: the result binds the replay by digest, the trace's binding
footer binds the same replay, and both are re-verified here by the same
preflight Designer uses (``preflight_result_replay``) and by the authoritative
sensing reconstruction. Nothing is fabricated after the fact, no agent code
runs, and the source files are never written.

Manifest ``schema_version`` 2 identifies this production contract. Version 1
remains the frozen contract of Spectator's own pinned prototype exporter; the
``broadcast.json``/``agent_a.json`` documents keep their version-1 shape
because they are produced by the same projection.

Every failure is fail-closed: output is staged and only renamed into place once
complete, so a failed export never leaves a manifest vouching for anything.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import os
import re
import shutil
import stat
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPORTER_NAME = "battle_client.spectator_export"
EXPORTER_VERSION = 1
MANIFEST_SCHEMA = "bytefray.spectator.manifest"
MANIFEST_SCHEMA_VERSION = 2
BROADCAST_SCHEMA = "bytefray.spectator.broadcast"
AGENT_SCHEMA = "bytefray.spectator.agent_view"
DOCUMENT_SCHEMA_VERSION = 1
PROVENANCE = "bytefray_match"

RESULT_FILENAME = "result.json"
TRACE_FILENAME = "trace.jsonl"
MANIFEST_FILENAME = "manifest.json"
PRESENTATION_FILES = {"broadcast": "broadcast.json", "agent_a": "agent_a.json"}
DOCUMENT_SCHEMAS = {"broadcast": BROADCAST_SCHEMA, "agent_a": AGENT_SCHEMA}
# Spectator's legend, colours and qualification cover exactly two entrants.
SUPPORTED_ENTRANTS = ("A", "B")
AGENT_ID = "A"
PHASE_CODES = {"OBSERVATION": 0, "ACTION": 1, "TICK_END": 2}
PACKAGES = ("battle_engine", "battle_client")

# Designer's presentation cache: rebuildable, outside runs/ so Replay History
# never indexes it, and bounded.
CACHE_RELATIVE = Path("cache") / "spectator" / "presentations"
CACHE_LIMIT = 16
# A staging directory is only abandoned once no export could still be writing
# it; export time grows with the square of match length, so allow a full day.
STALE_STAGING_SECONDS = 24 * 3600
CACHE_OWNER = ".bytefray-spectator-cache.json"
CACHE_OWNER_SCHEMA = "bytefray.spectator.cache"
CACHE_KEY_PATTERN = r"[\w-]{1,48}-[0-9a-f]{16}"

# Every key that may appear anywhere in agent_a.json. Anything else is a leak.
AGENT_ALLOWED_KEYS = frozenset(
    {
        "schema", "schema_version", "entrant_id", "name", "label", "arena_size",
        "core_base", "core_size", "opponent_activity", "phase_codes", "frames",
        "t", "cb", "p", "processes", "contacts", "receipt", "events", "samples",
        "reads", "address", "sampled", "received", "age_ticks", "age_callbacks",
        "stale_since", "kind", "process", "operand", "value", "cost", "status",
        "sample_status", "message", "center", "half_width", "addresses", "owner",
        *PHASE_CODES,
    }
)  # fmt: skip

# Stable failure codes (Designer maps them to messages; tests assert them).
SOURCE_UNAVAILABLE = "source_unavailable"
RESULT_UNVERIFIED = "result_unverified"
UNSUPPORTED_RULESET = "unsupported_ruleset"
UNSUPPORTED_ROSTER = "unsupported_roster"
TRACE_MISSING = "trace_missing"
EVIDENCE_UNVERIFIED = "evidence_unverified"
OUTCOME_UNVERIFIED = "outcome_unverified"
AGENT_VIEW_LEAK = "agent_view_leak"
SOURCE_CHANGED = "source_changed"
OUTPUT_UNSAFE = "output_unsafe"
OUTPUT_FAILED = "output_failed"
PRESENTATION_INVALID = "presentation_invalid"

Progress = Callable[[str], None]


class SpectatorExportError(RuntimeError):
    """The match could not be verified or exported; nothing usable was written."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SpectatorSupport:
    """Whether a completed match is eligible for Spectator (no verification)."""

    supported: bool
    code: str | None = None
    message: str = ""


@dataclass(frozen=True)
class PreparedPresentation:
    directory: Path
    reused: bool
    manifest: dict[str, Any]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(document: Any) -> bytes:
    """Deterministic encoding: sorted keys, no whitespace, ASCII, LF end."""
    text = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return (text + "\n").encode("ascii")


# --------------------------------------------------------------------------
# Source location and eligibility
# --------------------------------------------------------------------------


def resolve_result_path(source: Path) -> Path:
    """Accept a match directory or its ``result.json``; return the result path."""
    path = Path(source).expanduser()
    try:
        path = path.resolve()
    except OSError as exc:
        raise SpectatorExportError(SOURCE_UNAVAILABLE, f"cannot resolve {source}: {exc}") from None
    if path.is_dir():
        path = path / RESULT_FILENAME
    if not path.is_file():
        raise SpectatorExportError(SOURCE_UNAVAILABLE, f"no {RESULT_FILENAME} found at {path}")
    return path


def spectator_support(result_path: Path) -> SpectatorSupport:
    """Cheap eligibility check from the canonical result alone.

    This never authorizes anything: export re-verifies every artifact. It only
    tells Designer whether to try Spectator or keep its existing viewer.
    """
    from battle_engine.paths import contained_path
    from battle_engine.result_model import read_result
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID

    try:
        envelope = read_result(result_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return SpectatorSupport(False, SOURCE_UNAVAILABLE, f"the match result could not be read: {exc}")
    if envelope.ruleset_id != BYTEFRAY_RULESET_V6_ALPHA1_ID:
        return SpectatorSupport(
            False,
            UNSUPPORTED_RULESET,
            f"Spectator plays {BYTEFRAY_RULESET_V6_ALPHA1_ID} matches; this match used {envelope.ruleset_id}",
        )
    roster = tuple(str(entrant.get("agent_id")) for entrant in envelope.entrants)
    if roster != SUPPORTED_ENTRANTS:
        return SpectatorSupport(
            False, UNSUPPORTED_ROSTER, f"Spectator plays two-entrant A/B matches; this match has {list(roster)}"
        )
    if envelope.replay is None or not isinstance(envelope.replay.filename, str):
        return SpectatorSupport(False, RESULT_UNVERIFIED, "the match result references no replay")
    replay = contained_path(Path(result_path).parent, envelope.replay.filename)
    if replay is None:
        return SpectatorSupport(False, RESULT_UNVERIFIED, "the match result's replay reference is unsafe")
    if not replay.with_name(TRACE_FILENAME).is_file():
        return SpectatorSupport(False, TRACE_MISSING, f"the match has no {TRACE_FILENAME} beside its replay")
    return SpectatorSupport(True)


# --------------------------------------------------------------------------
# Exporter identity
# --------------------------------------------------------------------------


def _package_files() -> list[tuple[str, Path]]:
    import battle_engine

    import battle_client

    files: list[tuple[str, Path]] = []
    for module in (battle_engine, battle_client):
        root = Path(module.__file__ or "").resolve().parent
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if "__pycache__" not in path.parts:
                files.append((f"{module.__name__}/{path.relative_to(root).as_posix()}", path))
    return sorted(files)


@functools.lru_cache(maxsize=1)
def _identity() -> tuple[str, int, str | None]:
    from battle_engine.project_info import get_project_info

    listing = hashlib.sha256()
    files = _package_files()
    for name, path in files:
        listing.update(f"{name}\0{sha256_file(path)}\n".encode())
    return get_project_info().version, len(files), listing.hexdigest() if files else None


def exporter_identity() -> dict[str, Any]:
    """The exporting Bytefray: product version plus a digest of the package sources it ran.

    A frozen build carries no ``.py`` sources, so its digest is ``None`` and
    only the version identifies it.
    """
    version, files, digest = _identity()
    return {"version": version, "packages": list(PACKAGES), "files": files, "packages_sha256": digest}


# --------------------------------------------------------------------------
# Verification helpers (ported unchanged from Spectator's pinned exporter)
# --------------------------------------------------------------------------


def _tick_zero_regions(replay_path: Path) -> dict[str, int]:
    with replay_path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") == "tick" and record.get("tick") == 0:
                return {agent["id"]: agent["region"][0] for agent in record["agents"]}
    raise SpectatorExportError(EVIDENCE_UNVERIFIED, "replay has no tick-0 snapshot")


def _replay_terminal(replay_path: Path) -> dict[str, Any]:
    with replay_path.open(encoding="utf-8") as handle:
        lines = [line for line in handle if line.strip()]
    terminal = json.loads(lines[-1]) if lines else {}
    if terminal.get("record_type") != "result":
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, "replay has no terminal result record")
    return terminal


def verify_outcome(playback: Any, terminal: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """Re-derive the outcome from verified state and refuse any disagreeing record.

    The final alive set comes from the reconstructed world (checked against every
    replay snapshot); the replay's terminal result record is bound by the replay
    digest. result.json must agree with both, and both must follow the engine's
    rule (process_runtime): one survivor wins by last_agent_standing, none is a
    tie by all_agents_dead, otherwise tick_limit with the unique top score among
    the living (else a tie).
    """
    final = playback.facts[-1]
    if final.world_state is None or final.phase.value != "TICK_END":
        raise SpectatorExportError(OUTCOME_UNVERIFIED, "verified facts do not end on a tick boundary")
    try:
        alive = sorted(final.world_state.alive_entrants)
        ticks = final.tick
        tick_limit = int(result["reproducibility"]["tick_limit"])
        score = terminal["score"]
        result_score = result["score"]
        # JSON booleans compare equal to 0/1 in Python; coercion would also
        # admit strings, NaN and infinity. Only finite JSON numbers qualify.
        def valid_score(value: Any) -> bool:
            return type(value) is int or (type(value) is float and math.isfinite(value))

        if not isinstance(score, dict) or set(score) != set(SUPPORTED_ENTRANTS):
            raise ValueError("terminal score must name exactly A and B")
        if not isinstance(result_score, dict) or set(result_score) != set(score):
            raise ValueError("result score must name exactly the terminal entrants")
        for entrant_id in score:
            if not valid_score(score[entrant_id]) or not valid_score(result_score[entrant_id]):
                raise ValueError(f"malformed score for {entrant_id}")
        entrants = result["entrants"]
        if [e["agent_id"] for e in entrants] != list(SUPPORTED_ENTRANTS):
            raise ValueError("entrant scores must name exactly A and B")
        for entrant in entrants:
            value = entrant["score"]
            if not valid_score(value) or value != score[entrant["agent_id"]]:
                raise ValueError(f"entrant score disagrees with terminal score for {entrant['agent_id']}")
        if len(alive) == 1:
            expected = (alive[0], "last_agent_standing")
        elif not alive:
            expected = ("tie", "all_agents_dead")
        else:
            top = max(score[entrant] for entrant in alive)
            leaders = [entrant for entrant in alive if score[entrant] == top]
            expected = (leaders[0] if len(leaders) == 1 else "tie", "tick_limit")
        terminal_outcome = (terminal["winner"] or "tie", terminal["termination_reason"])
        result_outcome = (result["winner"], result["termination_reason"])
        checks = {
            "outcome follows the engine rule": terminal_outcome == expected,
            "result.json outcome equals the replay": result_outcome == terminal_outcome,
            "tick count": result["ticks"] == terminal["ticks"] == ticks,
            "tick limit": ticks == tick_limit if expected[1] == "tick_limit" else ticks <= tick_limit,
            "identity": (result["match_id"], result["result_id"]) == (terminal["match_id"], terminal["result_id"]),
            "score": result["score"] == score,
            "alive flags": [(e["agent_id"], e["alive"]) for e in result["entrants"]]
            == [(a["id"], a["alive"]) for a in terminal["agents"]]
            == [(e["agent_id"], e["agent_id"] in alive) for e in result["entrants"]],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise SpectatorExportError(OUTCOME_UNVERIFIED, f"match outcome records are incomplete: {exc!r}") from None
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SpectatorExportError(OUTCOME_UNVERIFIED, f"match outcome does not verify: {', '.join(failed)}")
    return {
        "winner": expected[0],
        "termination_reason": expected[1],
        "ticks": ticks,
        "tick_limit": tick_limit,
        "alive": alive,
    }


# --------------------------------------------------------------------------
# Projection (the same projection as Spectator's pinned exporter)
# --------------------------------------------------------------------------


def _broadcast(
    playback: Any, cursor: Any, core_cells: dict[str, list[int]], result: Mapping[str, Any], outcome: dict[str, Any]
) -> dict[str, Any]:
    facts = playback.facts
    if len(cursor.positions) != len(facts):
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, "broadcast positions do not match the verified facts")
    entrants = [
        {
            "id": entrant["agent_id"],
            "name": entrant["name"],
            "alive": entrant["alive"],
            "score": entrant["score"],
            "core": core_cells[entrant["agent_id"]],
        }
        for entrant in result["entrants"]
    ]
    frames: list[dict[str, Any]] = []
    previous: tuple[str | None, ...] | None = None
    view = cursor.restart()
    for index, fact in enumerate(facts):
        if index:
            view = cursor.step_forward()  # TICK_END steps re-check the replay boundary
        if (view.tick, view.global_decision_index, view.phase) != (fact.tick, fact.decision_index, fact.phase):
            raise SpectatorExportError(
                EVIDENCE_UNVERIFIED, f"broadcast frame {index} is out of order with the verified facts"
            )
        frame: dict[str, Any] = {
            "t": view.tick,
            "d": view.global_decision_index,
            "p": PHASE_CODES[view.phase.value],
            "anchors": [[entrant, process, anchor] for entrant, process, anchor in view.anchors],
            "disrupted": [[entrant, process] for entrant, process in view.disrupted_processes],
            "alive": list(view.alive_entrants),
            "actor": fact.actor_id,
            "process": fact.process_id,
            "kind": fact.action_kind,
            "status": fact.status,
            "address": fact.normalized_address,
            "operand": fact.operand,
            "sensed": None if fact.sensed_anchors is None else list(fact.sensed_anchors),
        }
        if previous is None:
            frame["owners"] = list(view.owners)
        else:
            frame["owner_changes"] = [
                [cell, owner] for cell, (old, owner) in enumerate(zip(previous, view.owners, strict=True)) if old != owner
            ]
        previous = view.owners
        frames.append(frame)
    return {
        "schema": BROADCAST_SCHEMA,
        "schema_version": DOCUMENT_SCHEMA_VERSION,
        "label": "Broadcast - full world state",
        "match_id": playback.match_id,
        "ruleset_id": playback.ruleset_id,
        "arena_size": playback.arena_size,
        "entrants": entrants,
        "result": {
            "termination_reason": outcome["termination_reason"],
            "ticks": outcome["ticks"],
            "winner": outcome["winner"],
        },
        "phase_codes": PHASE_CODES,
        "frames": frames,
    }


def _point(point: Any) -> list[Any]:
    return [point.tick, point.callback, point.process_id]


def _agent(cursor: Any, name: str) -> dict[str, Any]:
    """Serialize SensingView objects only; never the playback, facts or world."""
    from battle_client.sensing import SensingView

    frames: list[dict[str, Any]] = []
    seen = {"events": 0, "samples": 0, "reads": 0}
    first: Any = None
    view = cursor.restart()
    for index in range(len(cursor.positions)):
        if index:
            view = cursor.step_forward()
        if not isinstance(view, SensingView) or view.entrant_id != AGENT_ID:
            raise SpectatorExportError(AGENT_VIEW_LEAK, "agent cursor produced a non-entrant view")
        first = first or view
        events = view.events[seen["events"] :]
        samples = view.samples[seen["samples"] :]
        reads = view.reads[seen["reads"] :]
        seen = {"events": len(view.events), "samples": len(view.samples), "reads": len(view.reads)}
        frames.append(
            {
                "t": view.position.tick,
                "cb": view.position.callback,
                "p": PHASE_CODES[view.position.phase.value],
                "processes": [[p.process_id, p.anchor, p.reach] for p in view.own_processes],
                "contacts": [
                    {
                        "address": c.address,
                        "sampled": _point(c.sampled_at),
                        "received": _point(c.received_at),
                        "age_ticks": c.age_ticks,
                        "age_callbacks": c.age_callbacks,
                        "stale_since": None if c.not_present_in_newer_sample is None else _point(c.not_present_in_newer_sample),
                    }
                    for c in view.contacts
                ],
                "receipt": view.receipt_status.value,
                "events": [
                    {
                        "kind": e.kind,
                        "process": e.process_id,
                        "address": e.address,
                        "operand": e.operand,
                        "value": e.value,
                        "cost": e.cost,
                        "status": e.status,
                        "sample_status": e.sample_status.value,
                        "message": e.message,
                    }
                    for e in events
                ],
                "samples": [
                    {
                        "center": s.center,
                        "half_width": s.half_width,
                        "status": s.status.value,
                        "addresses": list(s.addresses),
                        "sampled": _point(s.sampled_at),
                        "received": _point(s.received_at),
                    }
                    for s in samples
                ],
                "reads": [
                    {
                        "address": r.address,
                        "value": r.value,
                        "owner": r.owner,
                        "sampled": _point(r.sampled_at),
                        "received": _point(r.received_at),
                    }
                    for r in reads
                ],
            }
        )
    if first is None:
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, "agent view has no permitted phases")
    document = {
        "schema": AGENT_SCHEMA,
        "schema_version": DOCUMENT_SCHEMA_VERSION,
        "entrant_id": AGENT_ID,
        "name": name,
        "label": first.label,
        "arena_size": first.arena_size,
        "core_base": first.own_core_base,
        "core_size": first.own_core_size,
        "opponent_activity": first.opponent_activity,
        "phase_codes": PHASE_CODES,
        "frames": frames,
    }
    check_agent_allowlist(document)
    return document


def check_agent_allowlist(node: Any, path: str = "$") -> None:
    """Fail closed if the agent document carries any key outside the allowlist."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key not in AGENT_ALLOWED_KEYS:
                raise SpectatorExportError(AGENT_VIEW_LEAK, f"agent view leak: unexpected key {path}.{key}")
            check_agent_allowlist(value, f"{path}.{key}")
    elif isinstance(node, list):
        for item in node:
            check_agent_allowlist(item, path + "[]")


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------


def _source_records(paths: Mapping[str, Path]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        try:
            records[name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        except OSError as exc:
            raise SpectatorExportError(SOURCE_UNAVAILABLE, f"cannot read {name}: {exc}") from None
    return records


@dataclass(frozen=True)
class _Sources:
    result: Path
    replay: Path
    trace: Path

    def named(self) -> dict[str, Path]:
        return {path.name: path for path in (self.result, self.replay, self.trace)}


@dataclass(frozen=True)
class Expectation:
    """The identity a caller already verified, re-enforced by the export's own preflight.

    ``artifact_root`` is the directory the result must stay beneath; the
    expected ids are the result/match ids the caller's own preflight accepted.
    """

    artifact_root: Path | None = None
    match_id: str | None = None
    result_id: str | None = None


def _verified_sources(result_path: Path, expectation: Expectation | None = None) -> _Sources:
    """Run Designer's authoritative replay preflight and locate the bound trace."""
    from battle_engine.replay_integrity import ResultReplayRequest, preflight_result_replay

    expect = expectation or Expectation()
    request = ResultReplayRequest(
        result_path=result_path,
        artifact_root=Path(expect.artifact_root) if expect.artifact_root is not None else result_path.parent,
        expected_result_id=expect.result_id,
        expected_match_id=expect.match_id,
    )
    outcome = preflight_result_replay(request)
    if not outcome.verified or outcome.replay_path is None:
        reason = outcome.failure.value if outcome.failure is not None else "unknown"
        raise SpectatorExportError(RESULT_UNVERIFIED, f"replay preflight failed ({reason}): {outcome.diagnostic}")
    replay = Path(outcome.replay_path)
    trace = replay.with_name(TRACE_FILENAME)
    if not trace.is_file():
        raise SpectatorExportError(TRACE_MISSING, f"the match has no {TRACE_FILENAME} beside its replay")
    if len({result_path.name, replay.name, trace.name}) != 3:
        raise SpectatorExportError(RESULT_UNVERIFIED, "the result, replay and trace must be distinct files")
    return _Sources(result_path, replay, trace)


def _build_documents(
    sources: _Sources, progress: Progress
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    from battle_engine.python_runtime import core_addresses
    from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
    from battle_engine.sensing_playback import reconstruct_sensing_playback

    from battle_client.sensing import SensingCursor, SensingProjectionError
    from battle_client.session import ReplaySession

    result_path, replay_path, trace_path = sources.result, sources.replay, sources.trace
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SpectatorExportError(SOURCE_UNAVAILABLE, f"cannot read {result_path.name}: {exc}") from None
    if not isinstance(result, dict):
        raise SpectatorExportError(SOURCE_UNAVAILABLE, f"{result_path.name} is not a JSON object")
    if result.get("ruleset_id") != BYTEFRAY_RULESET_V6_ALPHA1_ID:
        raise SpectatorExportError(UNSUPPORTED_RULESET, f"unsupported ruleset {result.get('ruleset_id')!r}")
    roster = tuple(str(entrant.get("agent_id")) for entrant in result.get("entrants", ()))
    if roster != SUPPORTED_ENTRANTS:
        raise SpectatorExportError(UNSUPPORTED_ROSTER, f"unsupported roster {list(roster)}; expected A and B")

    progress("reconstructing")
    try:
        playback = reconstruct_sensing_playback(replay_path, trace_path, result_path=result_path)
    except Exception as exc:  # any verifier refusal: the evidence is unusable
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, f"match evidence did not verify: {exc}") from None
    if playback.ruleset_id != BYTEFRAY_RULESET_V6_ALPHA1_ID:
        raise SpectatorExportError(UNSUPPORTED_RULESET, f"unsupported ruleset {playback.ruleset_id}")
    outcome = verify_outcome(playback, _replay_terminal(replay_path), result)
    session = ReplaySession()
    session.load(replay_path)

    progress("projecting broadcast")
    try:
        broadcast_cursor = SensingCursor(playback, session, None)
    except SensingProjectionError as exc:
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, str(exc)) from None
    report = broadcast_cursor.verification_report()
    if not (report.artifact_pair_consistent and report.exchange_reconstructed):
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, "match did not verify")
    regions = _tick_zero_regions(replay_path)
    core_cells = {entrant: list(core_addresses(start, playback.arena_size)) for entrant, start in regions.items()}
    broadcast = _broadcast(playback, broadcast_cursor, core_cells, result, outcome)

    progress("projecting agent view")
    agent_name = next(e["name"] for e in result["entrants"] if e["agent_id"] == AGENT_ID)
    try:
        agent_cursor = SensingCursor(playback, session, AGENT_ID)
    except SensingProjectionError as exc:
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, str(exc)) from None
    agent = _agent(agent_cursor, agent_name)
    match = {
        "match_id": playback.match_id,
        "result_id": result["result_id"],
        "ruleset_id": playback.ruleset_id,
        "arena_size": playback.arena_size,
        "seed": result["reproducibility"]["seed"],
        "tick_limit": outcome["tick_limit"],
        "ticks": outcome["ticks"],
        "termination_reason": outcome["termination_reason"],
        "winner": outcome["winner"],
        "entrants": [[e["agent_id"], e["name"]] for e in result["entrants"]],
        "product_version": result.get("product_version"),
    }
    return broadcast, agent, match, {"tick_end_boundaries_checked": len(session.recorded_ticks)}


def _write_presentation(
    staging: Path, sources: dict[str, dict[str, Any]], documents: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    broadcast, agent, match, extra = documents
    presentation: dict[str, Any] = {}
    for key, document in (("broadcast", broadcast), ("agent_a", agent)):
        data = canonical_json(document)
        filename = PRESENTATION_FILES[key]
        (staging / filename).write_bytes(data)
        presentation[key] = {
            "path": filename,
            "schema": document["schema"],
            "schema_version": document["schema_version"],
            "sha256": _sha256_bytes(data),
            "bytes": len(data),
            "frames": len(document["frames"]),
        }
    tick_ends = sum(1 for frame in broadcast["frames"] if frame["p"] == PHASE_CODES["TICK_END"])
    if tick_ends != extra["tick_end_boundaries_checked"]:
        raise SpectatorExportError(EVIDENCE_UNVERIFIED, "broadcast tick boundaries disagree with the replay")
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "exporter": {"name": EXPORTER_NAME, "version": EXPORTER_VERSION},
        "bytefray": exporter_identity(),
        "match": match,
        "sources": sources,
        "verification": {
            "provenance": PROVENANCE,
            "result_replay_preflight": True,
            "artifact_pair_consistent": True,
            "exchange_reconstructed": True,
            "outcome_verified": True,
            "sources_unchanged": True,
            "tick_end_boundaries_checked": tick_ends,
            "agent_view_allowlist_checked": True,
        },
        "presentation": presentation,
    }
    (staging / MANIFEST_FILENAME).write_bytes(canonical_json(manifest))
    return manifest


def _export_into(
    result_path: Path, staging: Path, progress: Progress, expectation: Expectation | None = None
) -> dict[str, Any]:
    progress("verifying sources")
    sources = _verified_sources(result_path, expectation)
    before = _source_records(sources.named())
    documents = _build_documents(sources, progress)
    if _source_records(sources.named()) != before:
        raise SpectatorExportError(SOURCE_CHANGED, "match artifacts changed while they were being exported")
    progress("writing presentation")
    try:
        return _write_presentation(staging, before, documents)
    except OSError as exc:
        raise SpectatorExportError(OUTPUT_FAILED, f"could not write the presentation: {exc}") from None


def _is_presentation_dir(path: Path) -> bool:
    names = {entry.name for entry in path.iterdir()}
    allowed = {MANIFEST_FILENAME, *PRESENTATION_FILES.values()}
    return names <= allowed and all((path / name).is_file() for name in names)


def _check_output(out_dir: Path, result_path: Path, replace_existing: bool) -> None:
    """Refuse any output that could write into, or delete, something not ours.

    Run before the export and again immediately before installing: an export
    can take minutes, and the folder may be created or filled meanwhile.
    """
    _check_separation(out_dir, (result_path.parent,))
    if not out_dir.exists():
        return
    if not out_dir.is_dir():
        raise SpectatorExportError(OUTPUT_UNSAFE, f"{out_dir} exists and is not a directory")
    if not any(out_dir.iterdir()):
        return
    if not replace_existing:
        raise SpectatorExportError(OUTPUT_UNSAFE, f"{out_dir} is not empty; pass --replace to replace a presentation")
    if not _is_presentation_dir(out_dir):
        raise SpectatorExportError(OUTPUT_UNSAFE, f"{out_dir} holds files that are not a Spectator presentation")


def _new_staging(parent: Path, name: str) -> Path:
    try:
        parent.mkdir(parents=True, exist_ok=True)
        staging = parent / f".{name}.staging-{uuid.uuid4().hex[:12]}"
        staging.mkdir()
    except OSError as exc:
        raise SpectatorExportError(OUTPUT_FAILED, f"cannot create an output directory in {parent}: {exc}") from None
    return staging


def _install(staging: Path, out_dir: Path) -> None:
    """Move a complete staged presentation into place (rename within one directory).

    An existing ``out_dir`` is moved aside first and deleted only if it is empty
    or holds nothing but a presentation; anything else is moved back untouched
    and the install is refused.
    """
    if out_dir.exists():
        aside = out_dir.with_name(f".{out_dir.name}.old-{uuid.uuid4().hex[:12]}")
        os.replace(out_dir, aside)
        if not _is_presentation_dir(aside):
            os.replace(aside, out_dir)
            raise SpectatorExportError(OUTPUT_UNSAFE, f"{out_dir} gained files that are not a Spectator presentation")
        try:
            os.replace(staging, out_dir)
        except OSError:
            os.replace(aside, out_dir)
            raise
        shutil.rmtree(aside, ignore_errors=True)
    else:
        os.replace(staging, out_dir)


def _no_progress(_stage: str) -> None:
    return None


def export_presentation(
    source: Path, out_dir: Path, *, replace_existing: bool = False, progress: Progress = _no_progress
) -> dict[str, Any]:
    """Verify one completed match and write its presentation to ``out_dir``.

    ``source`` is the match directory or its ``result.json``. ``out_dir`` must be
    absent or empty, or (with ``replace_existing``) an earlier presentation.
    Returns the manifest. Raises :class:`SpectatorExportError` and leaves
    ``out_dir`` exactly as it was on any failure.
    """
    result_path = resolve_result_path(source)
    target = Path(out_dir).expanduser().resolve()
    _check_output(target, result_path, replace_existing)
    staging = _new_staging(target.parent, target.name)
    try:
        manifest = _export_into(result_path, staging, progress)
        _check_output(target, result_path, replace_existing)  # the export may have taken minutes
        try:
            _install(staging, target)
        except OSError as exc:
            raise SpectatorExportError(OUTPUT_FAILED, f"could not install the presentation: {exc}") from None
        return manifest
    finally:
        shutil.rmtree(staging, ignore_errors=True)


# --------------------------------------------------------------------------
# Verification of an existing presentation
# --------------------------------------------------------------------------


def verify_presentation(
    directory: Path, *, sources: Mapping[str, Mapping[str, Any]] | None = None, require_current_exporter: bool = False
) -> dict[str, Any]:
    """Check a production presentation against its manifest (and its sources).

    With ``sources`` the manifest must record exactly those source digests; with
    ``require_current_exporter`` it must have been written by this exporter
    build. Returns the manifest or raises ``SpectatorExportError``.
    """
    folder = Path(directory)

    def invalid(message: str) -> SpectatorExportError:
        return SpectatorExportError(PRESENTATION_INVALID, message)

    try:
        manifest = json.loads((folder / MANIFEST_FILENAME).read_bytes())
    except (OSError, ValueError) as exc:
        raise invalid(f"cannot read {MANIFEST_FILENAME}: {exc}") from None
    if not isinstance(manifest, dict):
        raise invalid("manifest is not a JSON object")
    if (manifest.get("schema"), manifest.get("schema_version")) != (MANIFEST_SCHEMA, MANIFEST_SCHEMA_VERSION):
        raise invalid("unsupported manifest schema")
    verification = manifest.get("verification")
    if not isinstance(verification, dict) or verification.get("provenance") != PROVENANCE:
        raise invalid("manifest records no verified Bytefray match")
    for key in (
        "result_replay_preflight",
        "artifact_pair_consistent",
        "exchange_reconstructed",
        "outcome_verified",
        "sources_unchanged",
        "agent_view_allowlist_checked",
    ):
        if verification.get(key) is not True:
            raise invalid(f"manifest does not record {key}")
    entries = manifest.get("presentation")
    if not isinstance(entries, dict) or set(entries) != set(PRESENTATION_FILES):
        raise invalid("manifest lists unexpected presentation files")
    for key, filename in PRESENTATION_FILES.items():
        entry = entries[key]
        if not isinstance(entry, dict) or entry.get("path") != filename:
            raise invalid(f"manifest entry for {key} is malformed")
        try:
            data = (folder / filename).read_bytes()
        except OSError as exc:
            raise invalid(f"cannot read {filename}: {exc}") from None
        if len(data) != entry.get("bytes") or _sha256_bytes(data) != entry.get("sha256"):
            raise invalid(f"{filename} does not match the manifest")
        try:
            document = json.loads(data)
        except ValueError as exc:
            raise invalid(f"{filename} is not JSON: {exc}") from None
        if not isinstance(document, dict) or not isinstance(document.get("frames"), list):
            raise invalid(f"{filename} is not a presentation document")
        if (document.get("schema"), document.get("schema_version")) != (DOCUMENT_SCHEMAS[key], DOCUMENT_SCHEMA_VERSION):
            raise invalid(f"{filename} has an unexpected schema")
        if len(document.get("frames", ())) != entry.get("frames"):
            raise invalid(f"{filename} frame count does not match the manifest")
        if key == "agent_a":
            check_agent_allowlist(document)
    if sources is not None and manifest.get("sources") != dict(sources):
        raise invalid("presentation was exported from different source artifacts")
    if require_current_exporter and (
        manifest.get("exporter") != {"name": EXPORTER_NAME, "version": EXPORTER_VERSION}
        or manifest.get("bytefray") != exporter_identity()
    ):
        raise invalid("presentation was written by a different exporter build")
    return manifest


# --------------------------------------------------------------------------
# Designer cache
# --------------------------------------------------------------------------


def default_cache_root(data_root: Path | None = None) -> Path:
    from battle_engine.paths import get_data_root

    root = get_data_root() if data_root is None else Path(data_root).expanduser().resolve()
    return root / CACHE_RELATIVE


def _cache_key(result_path: Path, sources: Mapping[str, Mapping[str, Any]]) -> str:
    from battle_engine.result_model import read_result

    try:
        match_id = read_result(result_path).match_id
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SpectatorExportError(SOURCE_UNAVAILABLE, f"the match result could not be read: {exc}") from None
    identity = {"sources": dict(sources), "exporter": EXPORTER_VERSION, "bytefray": exporter_identity()}
    digest = _sha256_bytes(canonical_json(identity))[:16]
    safe_match = "".join(ch for ch in str(match_id) if ch.isalnum() or ch in "-_")[:48] or "match"
    return f"{safe_match}-{digest}"


def _is_link(path: Path) -> bool:
    """Include Windows junctions/reparse points on every supported Python."""
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _check_separation(target: Path, source_dirs: tuple[Path, ...]) -> None:
    try:
        canonical = target.resolve()
        canonical_sources = tuple(source.resolve() for source in source_dirs)
    except (OSError, RuntimeError) as exc:
        raise SpectatorExportError(OUTPUT_UNSAFE, f"cannot resolve output/cache paths: {exc}") from None
    for source in canonical_sources:
        if canonical == source or canonical in source.parents or source in canonical.parents:
            raise SpectatorExportError(
                OUTPUT_UNSAFE, "the output/cache directory must be disjoint from the match directories"
            )


def _cache_owned(path: Path, key: str) -> bool:
    """Positive ownership plus a closed file set; never follow reparse points.

    New entries carry a private cache marker, including while staging or after
    file corruption. Older caches qualify only with a fully valid production
    presentation. Extra files or subdirectories always protect an entry.
    """
    if re.fullmatch(CACHE_KEY_PATTERN, key) is None:
        return False
    try:
        if _is_link(path) or not path.is_dir():
            return False
        names = {entry.name for entry in path.iterdir()}
        allowed = {MANIFEST_FILENAME, *PRESENTATION_FILES.values(), CACHE_OWNER}
        if not names <= allowed:
            return False
        if any(_is_link(path / name) or not (path / name).is_file() for name in names):
            return False
        if CACHE_OWNER in names:
            return json.loads((path / CACHE_OWNER).read_bytes()) == {"schema": CACHE_OWNER_SCHEMA, "key": key}
        if names != allowed - {CACHE_OWNER}:
            return False
        manifest = verify_presentation(path)
        exporter = manifest.get("exporter")
        return isinstance(exporter, dict) and exporter.get("name") == EXPORTER_NAME
    except (OSError, ValueError, TypeError, SpectatorExportError):
        return False


def _verify_cached(path: Path, sources: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    # Older frozen builds may share the same product identity. Every reuse
    # path, including a concurrent install winner, must have the new marker.
    if not (path / CACHE_OWNER).is_file() or not _cache_owned(path, path.name):
        raise SpectatorExportError(PRESENTATION_INVALID, "cached presentation predates cache safety checks")
    return verify_presentation(path, sources=sources, require_current_exporter=True)


def _discard(path: Path, key: str) -> None:
    if not _cache_owned(path, key):
        return
    aside = path.with_name(f".{path.name}.discard-{uuid.uuid4().hex[:12]}")
    try:
        os.replace(path, aside)
    except OSError:
        return
    # Recheck after taking custody: never delete files added meanwhile.
    if _cache_owned(aside, key):
        shutil.rmtree(aside, ignore_errors=True)
    else:
        try:
            os.replace(aside, path)
        except OSError:
            pass  # retain everything under the aside name if restoration races


def _mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:  # removed meanwhile by a concurrent prepare
        return None


def _prune(cache_root: Path, keep: Path) -> None:
    """Bound the cache; remove abandoned staging directories.

    Never fails the prepare that called it: entries may vanish concurrently.
    """
    now = time.time()
    try:
        entries = list(cache_root.iterdir())
    except OSError:
        return
    presentations: list[tuple[float, Path]] = []
    for entry in entries:
        modified = _mtime(entry)
        if modified is None:
            continue
        abandoned = re.fullmatch(rf"\.({CACHE_KEY_PATTERN})\.(?:staging|discard)-[0-9a-f]{{12}}", entry.name)
        key = abandoned[1] if abandoned else entry.name
        if not _cache_owned(entry, key):
            continue
        if abandoned:
            if now - modified > STALE_STAGING_SECONDS:
                _discard(entry, key)
        elif entry != keep:
            presentations.append((modified, entry))
    presentations.sort(reverse=True)
    for _modified, stale in presentations[CACHE_LIMIT - 1 :]:
        _discard(stale, stale.name)


def prepare_presentation(
    source: Path, cache_root: Path, *, progress: Progress = _no_progress, expectation: Expectation | None = None
) -> PreparedPresentation:
    """Return a verified presentation for ``source``, reusing a cached one when it verifies.

    Reuse requires the cached manifest to name exactly the current source
    digests, its files to match the manifest, and the same exporter build; the
    replay preflight also runs again. Anything else is discarded and exported
    afresh. Concurrent callers export into separate staging directories; the
    first complete one is installed and the others reuse it. ``expectation``
    (Designer's own preflight context: artifact root and expected ids) is
    enforced by every preflight this function runs.
    """
    result_path = resolve_result_path(source)
    support = spectator_support(result_path)
    if not support.supported:
        raise SpectatorExportError(support.code or SOURCE_UNAVAILABLE, support.message)
    try:
        cache = Path(cache_root).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise SpectatorExportError(OUTPUT_UNSAFE, f"cannot resolve cache: {exc}") from None
    _check_separation(cache, (result_path.parent,))
    verified = _verified_sources(result_path, expectation)
    source_dirs = tuple(
        parent for path in verified.named().values() for parent in (path.parent, path.resolve().parent)
    )
    _check_separation(cache, source_dirs)
    sources = _source_records(verified.named())
    final = cache / _cache_key(result_path, sources)
    if os.path.lexists(final):
        if not _cache_owned(final, final.name):
            raise SpectatorExportError(OUTPUT_UNSAFE, f"{final} is not a Spectator-owned cache entry")
        try:
            manifest = _verify_cached(final, sources)
        except SpectatorExportError:
            _discard(final, final.name)
        else:
            try:
                os.utime(final)  # most recently used: kept longest by _prune
            except OSError:
                pass
            return PreparedPresentation(final, True, manifest)
    staging = _new_staging(cache, final.name)
    try:
        (staging / CACHE_OWNER).write_bytes(canonical_json({"schema": CACHE_OWNER_SCHEMA, "key": final.name}))
        manifest = _export_into(result_path, staging, progress, expectation)
        if manifest["sources"] != sources:
            raise SpectatorExportError(SOURCE_CHANGED, "match artifacts changed while they were being exported")
        _check_separation(cache, source_dirs)
        if os.path.lexists(final) and not _cache_owned(final, final.name):
            raise SpectatorExportError(OUTPUT_UNSAFE, f"{final} gained unrelated files during export")
        try:
            os.replace(staging, final)
        except OSError:
            # Another export installed this key first; use it only if it verifies.
            try:
                manifest = _verify_cached(final, sources)
            except SpectatorExportError as exc:
                raise SpectatorExportError(OUTPUT_FAILED, f"could not install the presentation: {exc}") from None
            return PreparedPresentation(final, True, manifest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    _prune(cache, final)
    return PreparedPresentation(final, False, manifest)


# --------------------------------------------------------------------------
# Command line: bytefray spectator export|prepare|verify
# --------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bytefray spectator",
        description="Verify completed V6 alpha1 matches and write Bytefray Spectator presentations.",
    )
    commands = parser.add_subparsers(dest="action", required=True)
    export = commands.add_parser("export", help="verify a match and write its presentation directory")
    export.add_argument("--source", type=Path, required=True, help="match directory or its result.json")
    export.add_argument("--out", type=Path, required=True, help="new or empty presentation directory")
    export.add_argument("--replace", action="store_true", help="replace an earlier presentation in --out")
    prepare = commands.add_parser("prepare", help="reuse or create a cached presentation (used by Designer)")
    prepare.add_argument("--source", type=Path, required=True, help="match directory or its result.json")
    prepare.add_argument("--cache", type=Path, default=None, help="cache root (default: <data root>/cache/spectator/presentations)")
    prepare.add_argument("--artifact-root", type=Path, default=None, help="directory the result must stay beneath")
    prepare.add_argument("--expect-match-id", default=None, help="refuse unless the result has this match_id")
    prepare.add_argument("--expect-result-id", default=None, help="refuse unless the result has this result_id")
    verify = commands.add_parser("verify", help="check a presentation directory against its manifest")
    verify.add_argument("--presentation", type=Path, required=True)
    verify.add_argument("--source", type=Path, default=None, help="also require these match artifacts")
    return parser


def _emit(record: Mapping[str, Any]) -> None:
    print(json.dumps(record, sort_keys=True), flush=True)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.action == "export":
            manifest = export_presentation(
                args.source, args.out, replace_existing=args.replace, progress=lambda s: print(f"{s}...", file=sys.stderr)
            )
            for key, entry in manifest["presentation"].items():
                print(f"{key}: {entry['path']} frames={entry['frames']} sha256={entry['sha256']}")
            print(f"presentation: {Path(args.out).expanduser().resolve()}")
            return 0
        if args.action == "prepare":
            cache = args.cache if args.cache is not None else default_cache_root()
            expectation = Expectation(args.artifact_root, args.expect_match_id, args.expect_result_id)
            prepared = prepare_presentation(
                args.source,
                cache,
                progress=lambda stage: _emit({"status": "progress", "stage": stage}),
                expectation=expectation,
            )
            _emit(
                {
                    "status": "ok",
                    "presentation": str(prepared.directory),
                    "reused": prepared.reused,
                    "match_id": prepared.manifest["match"]["match_id"],
                    "result_id": prepared.manifest["match"]["result_id"],
                }
            )
            return 0
        sources = None
        if args.source is not None:
            sources = _source_records(_verified_sources(resolve_result_path(args.source)).named())
        manifest = verify_presentation(args.presentation, sources=sources)
        print(f"verified: {manifest['match']['match_id']} ({manifest['match']['ruleset_id']})")
        return 0
    except (SpectatorExportError, OSError) as exc:
        # Any other OSError (disk full, permissions) is an output failure, still
        # reported in the same structured way rather than as a traceback.
        code = exc.code if isinstance(exc, SpectatorExportError) else OUTPUT_FAILED
        if args.action == "prepare":
            _emit({"status": "error", "code": code, "message": str(exc)})
        else:
            print(f"spectator {args.action} failed ({code}): {exc}", file=sys.stderr)
        return 1


__all__ = [
    "AGENT_ALLOWED_KEYS",
    "EXPORTER_VERSION",
    "MANIFEST_SCHEMA_VERSION",
    "PROVENANCE",
    "Expectation",
    "PreparedPresentation",
    "SpectatorExportError",
    "SpectatorSupport",
    "check_agent_allowlist",
    "default_cache_root",
    "export_presentation",
    "exporter_identity",
    "main",
    "prepare_presentation",
    "resolve_result_path",
    "spectator_support",
    "verify_outcome",
    "verify_presentation",
]


if __name__ == "__main__":
    raise SystemExit(main())
