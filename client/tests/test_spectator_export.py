"""Production Bytefray Spectator export (battle_client.spectator_export).

Real product matches only: scripted Agent API v2 entrants played by
``NativeMatchService`` exactly as ``bytefray run`` plays them, writing the
same result.json/replay.jsonl/trace.jsonl a Designer run writes. No research
harness, private evidence or retained run is read.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path

import pytest
from battle_client import spectator_export as sx
from battle_engine.agents import agent_spec_from_dir
from battle_engine.config import Config
from battle_engine.match_service import MatchEntrant, MatchRequest, NativeMatchService
from battle_engine.rules import BYTEFRAY_RULESET_V4_ID, BYTEFRAY_RULESET_V6_ALPHA1_ID

STARTS = (0, 91, 300)
B_CORE = tuple(range(91, 99))


def _agent(folder: Path, name: str, script, processes: int, capabilities: str) -> object:
    folder.mkdir(parents=True)
    (folder / "agent.yaml").write_text(
        f"name: {name}\nkind: python\napi_version: 2\nentrypoint: agent.py:create_agent\n{capabilities}",
        encoding="utf-8",
    )
    (folder / "agent.py").write_text(
        "from battle_engine.agent_api import AgentV2, ProcessDeclaration, AgentAction, ActionKindV2\n"
        f"SCRIPT = {list(script)!r}\n"
        "class Scripted(AgentV2):\n"
        "    def __init__(self): self.calls = 0\n"
        "    def declare_processes(self):\n"
        f"        return [ProcessDeclaration(id=str(i), reach=128, share=1/{processes}) for i in range({processes})]\n"
        "    def act(self, obs):\n"
        "        item = SCRIPT[self.calls % len(SCRIPT)] if SCRIPT else ('read', obs.own_core_base)\n"
        "        self.calls += 1\n"
        "        return AgentAction(ActionKindV2(item[0]), operand=item[1], value=item[2] if len(item)>2 else None)\n"
        "def create_agent(): return Scripted()\n",
        encoding="utf-8",
    )
    spec = agent_spec_from_dir(folder)
    assert spec is not None
    return spec


def _match(
    root: Path,
    scripts,
    *,
    ticks: int = 6,
    processes=None,
    ruleset: str = BYTEFRAY_RULESET_V6_ALPHA1_ID,
) -> Path:
    """Play one match into ``root/match`` and return that match directory."""
    processes = processes or (1,) * len(scripts)
    capabilities = (
        "capabilities: {version: 1, required: [sense]}\n" if ruleset == BYTEFRAY_RULESET_V6_ALPHA1_ID else ""
    )
    entrants = []
    for index, script in enumerate(scripts):
        seat = "ABC"[index]
        spec = _agent(root / "agents" / seat.lower(), f"scripted_{seat.lower()}", script, processes[index], capabilities)
        entrants.append(MatchEntrant.python(seat, f"scripted_{seat.lower()}", STARTS[index], spec))
    match = root / "match"
    match.mkdir(parents=True)
    NativeMatchService().run(
        MatchRequest(
            config=Config(arena_size=512, instr_per_tick=8, seed=3),
            ruleset_id=ruleset,
            entrants=tuple(entrants),
            max_ticks=ticks,
            replay_path=match / "replay.jsonl",
            trace_path=match / "trace.jsonl",
            verbose=False,
        )
    )
    assert (match / "result.json").is_file()
    return match


def _snapshot(folder: Path) -> dict[str, tuple[str, int]]:
    return {
        path.name: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in sorted(folder.iterdir())
        if path.is_file()
    }


def _leftovers(parent: Path) -> list[str]:
    return sorted(entry.name for entry in parent.iterdir() if entry.name.startswith("."))


QUIET = [("read", 0)]


@pytest.fixture(scope="module")
def tie_match(tmp_path_factory) -> Path:
    return _match(tmp_path_factory.mktemp("tie"), [[("sense", 91), ("move", 16), ("read", 0)], [("read", 91)]])


@pytest.fixture(scope="module")
def tie_export(tie_match, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("tie-out") / "presentation"
    sx.export_presentation(tie_match, out)
    return out


# --- contract ----------------------------------------------------------------


def test_export_writes_a_versioned_verified_presentation(tie_match, tie_export):
    manifest = json.loads((tie_export / "manifest.json").read_bytes())
    assert (manifest["schema"], manifest["schema_version"]) == ("bytefray.spectator.manifest", 2)
    assert manifest["exporter"] == {"name": "battle_client.spectator_export", "version": sx.EXPORTER_VERSION}
    assert manifest["bytefray"] == sx.exporter_identity()
    assert manifest["verification"] == {
        "provenance": "bytefray_match",
        "result_replay_preflight": True,
        "artifact_pair_consistent": True,
        "exchange_reconstructed": True,
        "outcome_verified": True,
        "sources_unchanged": True,
        "tick_end_boundaries_checked": 7,
        "agent_view_allowlist_checked": True,
    }
    result = json.loads((tie_match / "result.json").read_bytes())
    match = manifest["match"]
    assert (match["match_id"], match["result_id"], match["ruleset_id"]) == (
        result["match_id"],
        result["result_id"],
        BYTEFRAY_RULESET_V6_ALPHA1_ID,
    )
    assert (match["winner"], match["termination_reason"], match["ticks"], match["tick_limit"]) == ("tie", "tick_limit", 6, 6)
    assert match["entrants"] == [["A", "scripted_a"], ["B", "scripted_b"]]
    for name in ("result.json", "replay.jsonl", "trace.jsonl"):
        data = (tie_match / name).read_bytes()
        assert manifest["sources"][name] == {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    assert sorted(path.name for path in tie_export.iterdir()) == ["agent_a.json", "broadcast.json", "manifest.json"]
    for key, filename, schema in (
        ("broadcast", "broadcast.json", "bytefray.spectator.broadcast"),
        ("agent_a", "agent_a.json", "bytefray.spectator.agent_view"),
    ):
        data = (tie_export / filename).read_bytes()
        document = json.loads(data)
        assert (document["schema"], document["schema_version"]) == (schema, 1)
        entry = manifest["presentation"][key]
        assert entry == {
            "path": filename,
            "schema": schema,
            "schema_version": 1,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "frames": len(document["frames"]),
        }
        assert data == sx.canonical_json(document)  # canonical, ASCII, LF


def test_broadcast_chronology_matches_the_authoritative_trace(tie_match, tie_export):
    broadcast = json.loads((tie_export / "broadcast.json").read_bytes())
    decisions = [
        json.loads(line)
        for line in (tie_match / "trace.jsonl").read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("record_type") == "decision_v2"
    ]
    actions = [frame for frame in broadcast["frames"] if frame["p"] == 1]
    assert [(f["t"], f["actor"], f["process"], f["kind"], f["status"]) for f in actions] == [
        (
            d["observation"]["current_tick"],
            d["agent_id"],
            d["process_id"],
            d["action"]["kind"],
            d["applied_result"]["status"],
        )
        for d in decisions
    ]
    assert [f["t"] for f in broadcast["frames"] if f["p"] == 2] == list(range(7))
    assert broadcast["result"] == {"winner": "tie", "termination_reason": "tick_limit", "ticks": 6}


def test_decisive_match_outcome_is_rederived(tmp_path):
    raid = [("write", address, 0x52) for address in B_CORE]
    match = _match(tmp_path, [raid, QUIET], ticks=40)
    manifest = sx.export_presentation(match, tmp_path / "out")
    result = json.loads((match / "result.json").read_bytes())
    assert result["termination_reason"] == "last_agent_standing"
    assert (manifest["match"]["winner"], manifest["match"]["termination_reason"]) == ("A", "last_agent_standing")
    assert manifest["match"]["ticks"] == result["ticks"] < 40
    broadcast = json.loads((tmp_path / "out" / "broadcast.json").read_bytes())
    assert broadcast["frames"][-1]["alive"] == ["A"]


def test_export_is_deterministic_and_never_touches_sources(tie_match, tie_export, tmp_path):
    before = _snapshot(tie_match)
    sx.export_presentation(tie_match / "result.json", tmp_path / "again")
    assert _snapshot(tie_match) == before
    for name in ("broadcast.json", "agent_a.json", "manifest.json"):
        assert (tmp_path / "again" / name).read_bytes() == (tie_export / name).read_bytes()
    assert _leftovers(tmp_path) == []


# --- Agent A knowledge isolation ---------------------------------------------


def test_agent_view_is_identical_whatever_the_opponent_does_unseen(tmp_path):
    """Opponent behaviour Agent A never observes must not change agent_a.json.

    A only reads its own core. The opponents differ in action kinds, process
    count (hidden decision timing) and ownership changes away from A. The
    positive control writes into A's core, which A's reads do deliver.
    """
    a_script = [("read", address) for address in range(8)]
    hidden = {
        "quiet": ([("read", 91)], 1),
        "busy": ([("write", 92, 0x11), ("sense", 300), ("read", 93)], 2),
        "mover": ([("move", 64), ("write", 400, 0x22)], 1),
    }
    exports = {}
    for name, (b_script, b_processes) in {**hidden, "control": ([("write", 3, 0x33)], 1)}.items():
        match = _match(tmp_path / name, [a_script, b_script], ticks=5, processes=(1, b_processes))
        sx.export_presentation(match, tmp_path / name / "out")
        exports[name] = tmp_path / name / "out"
    agent = {name: (path / "agent_a.json").read_bytes() for name, path in exports.items()}
    broadcast = {name: (path / "broadcast.json").read_bytes() for name, path in exports.items()}
    assert agent["quiet"] == agent["busy"] == agent["mover"]
    assert len({broadcast["quiet"], broadcast["busy"], broadcast["mover"]}) == 3
    assert agent["control"] != agent["quiet"]  # the comparison can see a delivered difference


def test_agent_document_never_carries_broadcast_or_outcome_fields(tie_export):
    agent = json.loads((tie_export / "agent_a.json").read_bytes())
    sx.check_agent_allowlist(agent)
    text = (tie_export / "agent_a.json").read_text(encoding="ascii")
    for forbidden in ('"winner"', '"termination_reason"', '"anchors"', '"owners"', '"actor"', '"match_id"', '"alive"'):
        assert forbidden not in text
    assert all(frame["p"] in (0, 1, 2) for frame in agent["frames"])
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.check_agent_allowlist({**agent, "winner": "B"})
    assert caught.value.code == sx.AGENT_VIEW_LEAK


# --- fail closed --------------------------------------------------------------


def _tamper_trace_operand(match: Path) -> None:
    lines = (match / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        record = json.loads(line)
        if record.get("record_type") == "decision_v2" and record["action"]["kind"] == "move":
            record["action"]["operand"] += 1
            lines[index] = json.dumps(record)
            break
    else:  # pragma: no cover - the fixture always moves
        raise AssertionError("no move to tamper with")
    (match / "trace.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _drop_trace_binding(match: Path) -> None:
    lines = (match / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if json.loads(line).get("record_type") != "binding"]
    assert len(kept) < len(lines)
    (match / "trace.jsonl").write_text("\n".join(kept) + "\n", encoding="utf-8")


def _edit_result(match: Path, **changes) -> None:
    result = json.loads((match / "result.json").read_bytes())
    result.update(changes)
    (match / "result.json").write_text(json.dumps(result), encoding="utf-8")


def _append_to_replay(match: Path) -> None:
    with (match / "replay.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("\n")


TAMPERING = {
    "replay changed": (_append_to_replay, sx.RESULT_UNVERIFIED),
    "trace missing": (lambda m: (m / "trace.jsonl").unlink(), sx.TRACE_MISSING),
    "trace decision edited": (_tamper_trace_operand, sx.EVIDENCE_UNVERIFIED),
    "trace binding removed": (_drop_trace_binding, sx.EVIDENCE_UNVERIFIED),
    "result winner rewritten": (lambda m: _edit_result(m, winner="A"), sx.OUTCOME_UNVERIFIED),
    "result score rewritten": (lambda m: _edit_result(m, score={"A": 999.0, "B": 0.0}), sx.OUTCOME_UNVERIFIED),
    "result match identity rewritten": (lambda m: _edit_result(m, match_id="match_000000000000000000000000"), sx.RESULT_UNVERIFIED),
    "result missing": (lambda m: (m / "result.json").unlink(), sx.SOURCE_UNAVAILABLE),
}


@pytest.mark.parametrize("case", sorted(TAMPERING))
def test_tampered_or_incomplete_artifacts_are_refused(tie_match, tmp_path, case):
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    tamper, code = TAMPERING[case]
    tamper(match)
    out = tmp_path / "out"
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.export_presentation(match, out)
    assert caught.value.code == code, str(caught.value)
    assert not out.exists()
    assert _leftovers(tmp_path) == []


def test_a_foreign_trace_is_refused(tie_match, tmp_path):
    other = _match(tmp_path / "other", [[("read", 1)], [("read", 92)]])
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    shutil.copyfile(other / "trace.jsonl", match / "trace.jsonl")
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.export_presentation(match, tmp_path / "out")
    assert caught.value.code == sx.EVIDENCE_UNVERIFIED


def test_unsupported_rulesets_and_rosters(tmp_path):
    v4 = _match(tmp_path / "v4", [[("read", 0)], [("read", 91)]], ruleset=BYTEFRAY_RULESET_V4_ID)
    three = _match(tmp_path / "three", [[("read", 0)], [("read", 91)], [("read", 300)]])
    for match, code in ((v4, sx.UNSUPPORTED_RULESET), (three, sx.UNSUPPORTED_ROSTER)):
        support = sx.spectator_support(match / "result.json")
        assert (support.supported, support.code) == (False, code)
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.export_presentation(match, tmp_path / f"out-{code}")
        assert caught.value.code == code
        assert not (tmp_path / f"out-{code}").exists()


def test_support_check_for_a_supported_match_and_a_missing_trace(tie_match, tmp_path):
    assert sx.spectator_support(tie_match / "result.json") == sx.SpectatorSupport(True)
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    (match / "trace.jsonl").unlink()
    assert sx.spectator_support(match / "result.json").code == sx.TRACE_MISSING


# --- output handling -----------------------------------------------------------


def test_output_must_be_new_empty_or_an_explicitly_replaced_presentation(tie_match, tie_export, tmp_path):
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "notes.txt").write_text("keep me", encoding="utf-8")
    for replace in (False, True):
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.export_presentation(tie_match, occupied, replace_existing=replace)
        assert caught.value.code == sx.OUTPUT_UNSAFE
    assert (occupied / "notes.txt").read_text(encoding="utf-8") == "keep me"

    for unsafe in (tie_match, tie_match.parent):
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.export_presentation(tie_match, unsafe, replace_existing=True)
        assert caught.value.code == sx.OUTPUT_UNSAFE

    empty = tmp_path / "empty"
    empty.mkdir()
    sx.export_presentation(tie_match, empty)
    with pytest.raises(sx.SpectatorExportError):
        sx.export_presentation(tie_match, empty)
    (empty / "broadcast.json").write_bytes(b"stale")
    sx.export_presentation(tie_match, empty, replace_existing=True)
    assert (empty / "broadcast.json").read_bytes() == (tie_export / "broadcast.json").read_bytes()
    assert _leftovers(tmp_path) == []


def test_output_inside_the_match_directory_is_refused(tie_match, tmp_path):
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    before = sorted(path.name for path in match.iterdir())
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.export_presentation(match, match / "presentation")
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert sorted(path.name for path in match.iterdir()) == before  # not even a staging directory


@pytest.mark.parametrize("replace", [False, True])
def test_files_that_appear_in_the_output_during_export_are_never_deleted(tie_match, tie_export, tmp_path, replace):
    out = tmp_path / "out"
    if replace:
        shutil.copytree(tie_export, out)

    def meanwhile(stage: str) -> None:
        if stage == "projecting agent view":  # long after the first output check
            out.mkdir(exist_ok=True)
            (out / "notes.txt").write_text("written during the export", encoding="utf-8")

    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.export_presentation(tie_match, out, replace_existing=replace, progress=meanwhile)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert (out / "notes.txt").read_text(encoding="utf-8") == "written during the export"
    assert _leftovers(tmp_path) == []


def test_install_never_deletes_a_folder_that_is_not_a_presentation(tie_export, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep.txt").write_text("keep", encoding="utf-8")
    staging = tmp_path / ".staging"
    shutil.copytree(tie_export, staging)
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx._install(staging, out)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert (out / "keep.txt").read_text(encoding="utf-8") == "keep" and staging.is_dir()


def test_prepare_enforces_the_callers_expected_identity_and_artifact_root(tie_match, tmp_path):
    result = json.loads((tie_match / "result.json").read_bytes())
    cache = tmp_path / "cache"
    good = sx.Expectation(tie_match.parent, result["match_id"], result["result_id"])
    assert sx.prepare_presentation(tie_match, cache, expectation=good).manifest["match"]["match_id"] == result["match_id"]
    for wrong in (
        sx.Expectation(match_id="match_000000000000000000000000"),
        sx.Expectation(result_id="result_000000000000000000000000"),
        sx.Expectation(artifact_root=tmp_path / "elsewhere"),
    ):
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.prepare_presentation(tie_match, cache, expectation=wrong)
        assert caught.value.code == sx.RESULT_UNVERIFIED


def test_cli_prepare_reports_identity_and_output_failures_as_json(tie_match, tmp_path, capsys):
    result = json.loads((tie_match / "result.json").read_bytes())
    args = ["prepare", "--source", str(tie_match), "--cache", str(tmp_path / "c")]
    assert sx.main([*args, "--expect-match-id", result["match_id"], "--expect-result-id", result["result_id"]]) == 0
    final = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert (final["status"], final["match_id"], final["result_id"]) == ("ok", result["match_id"], result["result_id"])
    assert sx.main([*args, "--expect-match-id", "match_000000000000000000000000"]) == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["code"] == sx.RESULT_UNVERIFIED
    blocked = tmp_path / "not a directory"
    blocked.write_text("a file where the cache should be", encoding="utf-8")
    assert sx.main(["prepare", "--source", str(tie_match), "--cache", str(blocked / "cache")]) == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["code"] == sx.OUTPUT_FAILED


def test_a_failed_replacement_keeps_the_previous_presentation(tie_match, tie_export, tmp_path):
    out = tmp_path / "out"
    shutil.copytree(tie_export, out)
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    _tamper_trace_operand(match)
    with pytest.raises(sx.SpectatorExportError):
        sx.export_presentation(match, out, replace_existing=True)
    for name in ("manifest.json", "broadcast.json", "agent_a.json"):
        assert (out / name).read_bytes() == (tie_export / name).read_bytes()


def test_verify_presentation_detects_any_change(tie_match, tie_export, tmp_path):
    sources = json.loads((tie_export / "manifest.json").read_bytes())["sources"]
    assert sx.verify_presentation(tie_export, sources=sources, require_current_exporter=True)["match"]
    for name, mutate in (
        ("broadcast.json", lambda b: b.replace(b'"t":1', b'"t":2', 1)),
        ("agent_a.json", lambda b: b[:-1] + b" \n"),
        ("manifest.json", lambda b: b.replace(b'"outcome_verified":true', b'"outcome_verified":false')),
    ):
        copy = tmp_path / name
        shutil.copytree(tie_export, copy)
        (copy / name).write_bytes(mutate((copy / name).read_bytes()))
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.verify_presentation(copy)
        assert caught.value.code == sx.PRESENTATION_INVALID
    with pytest.raises(sx.SpectatorExportError):
        sx.verify_presentation(tie_export, sources={**sources, "trace.jsonl": {"sha256": "0" * 64, "bytes": 1}})
    # A manifest rewritten to vouch for a non-document is still refused, with a stable code.
    forged = tmp_path / "forged"
    shutil.copytree(tie_export, forged)
    manifest = json.loads((forged / "manifest.json").read_bytes())
    for payload, name in ((b"[1, 2]\n", "broadcast.json"), (b"not json\n", "agent_a.json")):
        (forged / name).write_bytes(payload)
        key = "broadcast" if name == "broadcast.json" else "agent_a"
        manifest["presentation"][key].update(sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
        (forged / "manifest.json").write_bytes(sx.canonical_json(manifest))
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.verify_presentation(forged)
        assert caught.value.code == sx.PRESENTATION_INVALID


# --- Designer cache ---------------------------------------------------------------


def test_prepare_exports_once_then_reuses_only_a_verified_presentation(tie_match, tmp_path):
    cache = tmp_path / "cache"
    first = sx.prepare_presentation(tie_match, cache)
    assert first.reused is False and first.directory.parent == cache
    second = sx.prepare_presentation(tie_match / "result.json", cache)
    assert (second.reused, second.directory) == (True, first.directory)

    (first.directory / "agent_a.json").write_bytes(b"{}\n")  # corrupted cache entry
    third = sx.prepare_presentation(tie_match, cache)
    assert (third.reused, third.directory) == (False, first.directory)
    sx.verify_presentation(third.directory, require_current_exporter=True)
    assert _leftovers(cache) == []


def test_prepare_never_reuses_a_presentation_for_changed_sources(tie_match, tmp_path):
    cache = tmp_path / "cache"
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    first = sx.prepare_presentation(match, cache)
    _tamper_trace_operand(match)
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.prepare_presentation(match, cache)
    assert caught.value.code == sx.EVIDENCE_UNVERIFIED
    assert [entry for entry in cache.iterdir()] == [first.directory]  # nothing new installed


def test_concurrent_prepares_share_one_verified_presentation(tie_match, tmp_path):
    cache = tmp_path / "cache"
    outcomes: list[sx.PreparedPresentation] = []
    errors: list[BaseException] = []

    def run() -> None:
        try:
            outcomes.append(sx.prepare_presentation(tie_match, cache))
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert len({outcome.directory for outcome in outcomes}) == 1
    sx.verify_presentation(outcomes[0].directory, require_current_exporter=True)
    assert [entry.name for entry in cache.iterdir() if not entry.name.startswith(".")] == [outcomes[0].directory.name]


def test_cache_is_bounded_and_lives_outside_the_run_tree(tie_match, tie_export, tmp_path, monkeypatch):
    assert sx.default_cache_root(tmp_path) == tmp_path / "cache" / "spectator" / "presentations"
    monkeypatch.setattr(sx, "CACHE_LIMIT", 2)
    cache = tmp_path / "cache"
    stale = [cache / f"match_old{index}-{'0' * 16}" for index in range(3)]
    for index, folder in enumerate(stale):
        shutil.copytree(tie_export, folder)
        os.utime(folder, (1_000_000 + index, 1_000_000 + index))
    prepared = sx.prepare_presentation(tie_match, cache)
    remaining = sorted(entry.name for entry in cache.iterdir())
    assert remaining == sorted([prepared.directory.name, stale[2].name])


# --- command line ------------------------------------------------------------------


def test_cli_prepare_reports_json_and_bytefray_dispatches_it(tie_match, tmp_path, capsys):
    from battle_engine.command import main as bytefray_main

    assert bytefray_main(["spectator", "prepare", "--source", str(tie_match), "--cache", str(tmp_path / "c")]) == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [line["stage"] for line in lines if line["status"] == "progress"] == [
        "verifying sources",
        "reconstructing",
        "projecting broadcast",
        "projecting agent view",
        "writing presentation",
    ]
    final = lines[-1]
    assert final["status"] == "ok" and final["reused"] is False
    assert Path(final["presentation"]).parent == tmp_path / "c"

    match = tmp_path / "bad"
    shutil.copytree(tie_match, match)
    (match / "trace.jsonl").unlink()
    assert sx.main(["prepare", "--source", str(match), "--cache", str(tmp_path / "c")]) == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1]) == {
        "status": "error",
        "code": "trace_missing",
        "message": "the match has no trace.jsonl beside its replay",
    }


def test_cli_export_and_verify(tie_match, tmp_path, capsys):
    out = tmp_path / "with space" / "presentation"
    assert sx.main(["export", "--source", str(tie_match), "--out", str(out)]) == 0
    assert "broadcast: broadcast.json" in capsys.readouterr().out
    assert sx.main(["verify", "--presentation", str(out), "--source", str(tie_match)]) == 0
    assert sx.main(["export", "--source", str(tie_match), "--out", str(out)]) == 1
    assert "output_unsafe" in capsys.readouterr().err


# --- independent-review regression cases -------------------------------------


def test_prepare_refuses_original_pruning_reproduction(tie_match, tmp_path, capsys):
    runs = tmp_path / "runs"
    match = runs / "old-source"
    shutil.copytree(tie_match, match)
    before = _snapshot(match)
    os.utime(match, (1, 1))
    for index in range(16):
        sibling = runs / f"newer-{index}"
        sibling.mkdir()
        (sibling / "keep.txt").write_text("unrelated")
        os.utime(sibling, (2 + index, 2 + index))
    names = sorted(p.name for p in runs.iterdir())
    assert sx.main(["prepare", "--source", str(match), "--cache", str(runs)]) == 1
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["code"] == sx.OUTPUT_UNSAFE
    assert _snapshot(match) == before
    assert sorted(p.name for p in runs.iterdir()) == names


@pytest.mark.parametrize("location", ["same", "descendant", "ancestor"])
def test_prepare_refuses_all_source_cache_overlaps(tie_match, tmp_path, location):
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    cache = {"same": match, "descendant": match / "cache", "ancestor": tmp_path}[location]
    before = _snapshot(match)
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.prepare_presentation(match, cache)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert _snapshot(match) == before
    assert not (match / "cache").exists()
    assert _leftovers(tmp_path) == []


@pytest.mark.parametrize("api", ["export", "prepare"])
@pytest.mark.parametrize("score", [999999, None, "0", True, False, [], {}, float("nan"), float("inf"), "missing"])
def test_unverified_entrant_scores_never_get_a_manifest(tie_match, tmp_path, api, score):
    match = tmp_path / "copied-valid-match"
    shutil.copytree(tie_match, match)
    result = json.loads((match / "result.json").read_bytes())
    if score == "missing":
        del result["entrants"][0]["score"]
    else:
        result["entrants"][0]["score"] = score
    _edit_result(match, entrants=result["entrants"])
    before = _snapshot(match)
    out = tmp_path / "output"
    with pytest.raises(sx.SpectatorExportError):
        if api == "export":
            sx.export_presentation(match, out)
        else:
            sx.prepare_presentation(match, out)
    assert not list(out.rglob("manifest.json"))
    assert not list(out.glob(".*"))
    assert _snapshot(match) == before


def test_cache_never_prunes_unrelated_directories(tie_match, tmp_path, monkeypatch):
    monkeypatch.setattr(sx, "CACHE_LIMIT", 1)
    cache = tmp_path / "cache"
    cache.mkdir()
    for name in ("ordinary", ".hidden", ".match_old.staging-deadbeef0000", "match_fake-" + "0" * 16):
        folder = cache / name
        folder.mkdir()
        (folder / "keep.txt").write_text("keep")
        os.utime(folder, (1, 1))
    before = {p.name: _snapshot(p) for p in cache.iterdir()}
    sx.prepare_presentation(tie_match, cache)
    for name, snapshot in before.items():
        assert _snapshot(cache / name) == snapshot


def _directory_alias(alias: Path, target: Path) -> None:
    if os.name == "nt":
        # Junctions need no symlink privilege and exercise native reparse points.
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
            capture_output=True, text=True, check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
    else:
        alias.symlink_to(target, target_is_directory=True)


@pytest.mark.parametrize("kind", ["cache-alias", "source-alias", "cache-child-alias"])
def test_canonical_source_cache_alias_overlaps_are_refused(tie_match, tmp_path, kind):
    match = tmp_path / "runs" / "match"
    shutil.copytree(tie_match, match)
    before = _snapshot(match)
    alias = tmp_path / "alias"
    if kind == "cache-alias":
        _directory_alias(alias, match.parent)
        source, cache = match, alias
    elif kind == "source-alias":
        _directory_alias(alias, match)
        source, cache = alias, match.parent
    else:
        _directory_alias(alias, match)
        source, cache = match, alias / "new-cache"
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.prepare_presentation(source, cache)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert _snapshot(match) == before
    assert not (match / "new-cache").exists()


def test_pruning_preserves_junctions_and_entries_with_unrelated_files(tie_match, tie_export, tmp_path, monkeypatch):
    monkeypatch.setattr(sx, "CACHE_LIMIT", 1)
    cache = tmp_path / "cache"
    cache.mkdir()
    target = tmp_path / "foreign"
    shutil.copytree(tie_export, target)
    alias = cache / ("match_alias-" + "a" * 16)
    _directory_alias(alias, target)
    occupied = cache / ("match_occupied-" + "b" * 16)
    shutil.copytree(tie_export, occupied)
    (occupied / "notes.txt").write_text("keep")
    for path in (target, occupied):
        os.utime(path, (1, 1))
    snapshots = [_snapshot(path) for path in (target, occupied)]
    sx.prepare_presentation(tie_match, cache)
    assert alias.is_dir()
    assert [_snapshot(path) for path in (target, occupied)] == snapshots


def test_cache_key_collision_never_discards_unrelated_files(tie_match, tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    key = "match_collision-" + "f" * 16
    monkeypatch.setattr(sx, "_cache_key", lambda *_: key)
    foreign = cache / key
    foreign.mkdir(parents=True)
    (foreign / "notes.txt").write_text("keep")
    before = _snapshot(foreign)
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.prepare_presentation(tie_match, cache)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert _snapshot(foreign) == before


def test_owned_staging_cleanup_and_cache_retention(tie_match, tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    monkeypatch.setattr(sx, "CACHE_LIMIT", 2)
    prepared = sx.prepare_presentation(tie_match, cache)
    key = prepared.directory.name
    # Real cache entries (including corrupt rebuildable documents) are bounded.
    old_keys = ["match_old-" + str(i) * 16 for i in range(3)]
    for index, old_key in enumerate(old_keys):
        old = cache / old_key
        shutil.copytree(prepared.directory, old)
        (old / sx.CACHE_OWNER).write_bytes(sx.canonical_json({"schema": sx.CACHE_OWNER_SCHEMA, "key": old_key}))
        (old / "broadcast.json").write_text("damaged cache")
        os.utime(old, (1 + index, 1 + index))
    abandoned = cache / f".{key}.staging-012345abcdef"
    abandoned.mkdir()
    (abandoned / sx.CACHE_OWNER).write_bytes(sx.canonical_json({"schema": sx.CACHE_OWNER_SCHEMA, "key": key}))
    (abandoned / "broadcast.json").write_text("partial")
    os.utime(abandoned, (1, 1))
    recent = cache / f".{key}.staging-abcdef012345"
    shutil.copytree(abandoned, recent)
    os.utime(recent, None)
    sx._prune(cache, prepared.directory)
    assert sorted(p.name for p in cache.iterdir()) == sorted([key, old_keys[-1], recent.name])


def test_valid_entrant_scores_match_terminal_and_broadcast(tie_match, tmp_path):
    result = json.loads((tie_match / "result.json").read_bytes())
    terminal = json.loads((tie_match / "replay.jsonl").read_text().splitlines()[-1])
    prepared = sx.prepare_presentation(tie_match, tmp_path / "cache")
    broadcast = json.loads((prepared.directory / "broadcast.json").read_bytes())
    assert prepared.manifest["verification"]["outcome_verified"] is True
    assert {e["id"]: e["score"] for e in broadcast["entrants"]} == terminal["score"] == result["score"]


@pytest.mark.parametrize("exporter", [None, [], 1, "not-an-exporter"])
def test_malformed_legacy_cache_manifest_is_preserved(tie_match, tie_export, tmp_path, exporter):
    cache = tmp_path / "cache"
    legacy = cache / ("match_legacy-" + "0" * 16)
    shutil.copytree(tie_export, legacy)
    manifest = json.loads((legacy / "manifest.json").read_bytes())
    manifest["exporter"] = exporter
    (legacy / "manifest.json").write_bytes(sx.canonical_json(manifest))
    os.utime(legacy, (1, 1))
    before = _snapshot(legacy)
    prepared = sx.prepare_presentation(tie_match, cache)
    assert sx.verify_presentation(prepared.directory)["verification"]["outcome_verified"] is True
    assert _snapshot(legacy) == before


def test_cache_does_not_delete_files_added_during_export(tie_match, tmp_path, monkeypatch):
    key = "match_occupied-" + "0" * 16
    monkeypatch.setattr(sx, "_cache_key", lambda *_: key)
    cache = tmp_path / "cache"

    def meanwhile(stage):
        if stage == "projecting agent view":
            foreign = cache / key
            foreign.mkdir()
            (foreign / "notes.txt").write_text("keep")

    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.prepare_presentation(tie_match, cache, progress=meanwhile)
    assert caught.value.code == sx.OUTPUT_UNSAFE
    assert (cache / key / "notes.txt").read_text() == "keep"
    assert not list(cache.rglob("manifest.json"))
    assert _leftovers(cache) == []


@pytest.mark.parametrize("score", [
    None, [], {"A": 0}, {"A": 0, "B": 0, "C": 0},
    {"A": False, "B": 0}, {"A": "0", "B": 0}, {"A": float("inf"), "B": 0},
])
def test_malformed_result_score_maps_fail_closed(tie_match, tmp_path, score):
    match = tmp_path / "match"
    shutil.copytree(tie_match, match)
    _edit_result(match, score=score)
    with pytest.raises(sx.SpectatorExportError):
        sx.export_presentation(match, tmp_path / "out")
    assert not (tmp_path / "out").exists()
    assert _leftovers(tmp_path) == []


@pytest.mark.parametrize("score", [
    None, [], {"A": 0}, {"A": 0, "B": 0, "C": 0},
    {"A": False, "B": 0}, {"A": float("nan"), "B": 0},
])
def test_terminal_score_map_requires_exact_finite_numeric_entrants(tie_match, score):
    from battle_engine.sensing_playback import reconstruct_sensing_playback

    result = json.loads((tie_match / "result.json").read_bytes())
    terminal = sx._replay_terminal(tie_match / "replay.jsonl")
    terminal["score"] = score
    playback = reconstruct_sensing_playback(
        tie_match / "replay.jsonl", tie_match / "trace.jsonl", result_path=tie_match / "result.json",
    )
    with pytest.raises(sx.SpectatorExportError) as caught:
        sx.verify_outcome(playback, terminal, result)
    assert caught.value.code == sx.OUTCOME_UNVERIFIED


@pytest.mark.parametrize("blocked_discard", [False, True])
def test_unmarked_legacy_cache_is_reverified_even_with_identical_exporter_identity(
    tie_match, tmp_path, monkeypatch, blocked_discard,
):
    cache = tmp_path / "cache"
    first = sx.prepare_presentation(tie_match, cache)
    (first.directory / sx.CACHE_OWNER).unlink()
    broadcast_path = first.directory / "broadcast.json"
    broadcast = json.loads(broadcast_path.read_bytes())
    broadcast["entrants"][0]["score"] = 999999
    data = sx.canonical_json(broadcast)
    broadcast_path.write_bytes(data)
    manifest_path = first.directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["presentation"]["broadcast"].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest_path.write_bytes(sx.canonical_json(manifest))
    # A pre-fix cache can have valid file digests and the same frozen identity.
    sx.verify_presentation(first.directory, require_current_exporter=True)
    if blocked_discard:
        # Windows sharing/ACLs may prevent retiring the old directory. The
        # concurrent-winner fallback must not re-authorize this legacy cache.
        monkeypatch.setattr(sx, "_discard", lambda *_: None)
        before = _snapshot(first.directory)
        with pytest.raises(sx.SpectatorExportError) as caught:
            sx.prepare_presentation(tie_match, cache)
        assert caught.value.code == sx.OUTPUT_FAILED
        assert _snapshot(first.directory) == before
        assert _leftovers(cache) == []
        return
    prepared = sx.prepare_presentation(tie_match, cache)
    assert prepared.reused is False
    result = json.loads((tie_match / "result.json").read_bytes())
    rebuilt = json.loads((prepared.directory / "broadcast.json").read_bytes())
    assert {e["id"]: e["score"] for e in rebuilt["entrants"]} == result["score"]
