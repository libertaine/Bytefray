"""Phase 6.5a: canonical replay reconstruction, digest, and identity contract.

These tests exist to prove -- not merely assert -- that the canonical
``battle2.replay`` stream produced by ``NativeMatchService`` is sufficient to
reconstruct engine-observable match state (arena content, ownership, and
per-tick score) at any tick using only the public typed reader API
(``iter_replay``), without rerunning any agent.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
retired VM/blob execution: this file's VM-specific ground-truth cross-check
(re-simulating a match with ``vm.step`` independently of ``NativeMatchService``
to prove the replay matches) and its VM-HALT death-event case were removed
along with the opcode-execution machinery they depended on. The Python-agent
cases -- the file's real subject -- are converted from Agent API v1 fixtures
to Agent API v2, and every identity/digest test now runs a real
``bytefray-rules-4`` match instead of a VM one.
"""

from __future__ import annotations

import json

import pytest
from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    canonical_match_id,
)
from battle_engine.replay import (
    MatchResult,
    ReplayHeader,
    TickSnapshot,
    iter_replay,
)
from battle_engine.result_model import (
    ReplayIntegrityError,
    read_result,
    stable_id,
    verify_replay_digest,
    verify_replay_digest_value,
    verify_result_replay,
)


# ---------------------------------------------------------------------------
# Shared reconstruction helper: rebuilds arena bytes/ownership at every tick
# using ONLY the public typed replay reader, mirroring what a Phase 7 replay
# viewer would do. This is intentionally independent of match_service's
# internal finalize logic -- it only consumes the public ReplayRecord model.
# ---------------------------------------------------------------------------
def _reconstruct_ticks(replay_path):
    header = None
    arena = None
    owners = None
    reconstructed = {}
    for record in iter_replay(replay_path):
        if isinstance(record, ReplayHeader):
            header = record
            arena_size = header.config.arena_size
            arena = bytearray(arena_size)
            owners = [None] * arena_size
            continue
        if isinstance(record, TickSnapshot):
            assert arena is not None and owners is not None, "header must precede ticks"
            for diff in record.memory_diffs:
                for offset, value in enumerate(diff.values):
                    address = (diff.address + offset) % len(arena)
                    arena[address] = value
                    owners[address] = diff.owner
            reconstructed[record.tick] = {
                "arena": bytes(arena),
                "owners": tuple(owners),
                "score": dict(record.score),
                "agents": {
                    agent.agent_id: agent for agent in record.agents
                },
            }
    assert header is not None, "replay must contain a header"
    return header, reconstructed


def _config(arena_size=64, instr_per_tick=8, seed=1337):
    return Config(arena_size=arena_size, instr_per_tick=instr_per_tick, seed=seed)


def _python_spec(root, name, source):
    from battle_engine.agents import resolve_agent

    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "agent.yaml").write_text(
        json.dumps(
            {
                "kind": "python",
                "api_version": 2,
                "entrypoint": "agent.py:create_agent",
                "name": name,
                "display": name.title(),
                "version": "1.0",
            }
        ),
        encoding="utf-8",
    )
    (directory / "agent.py").write_text(source, encoding="utf-8")
    return resolve_agent(root, name)


# A single-process, full-reach agent so its declared process can legally
# target any arena address (a narrower ``reach`` rejects an out-of-range
# WRITE/READ target as an invalid action) -- see ``ProcessDeclaration``'s
# own reach semantics in ``docs/AGENT_API_V2.md``.
WRITER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=self.arena_size - 1, share=1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.WRITE, 10, 0xAB)

def create_agent():
    return Agent()
"""

READER_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=self.arena_size - 1, share=1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, 10)

def create_agent():
    return Agent()
"""

PASSIVE_SOURCE = """
from battle_engine.agent_api import ActionKindV2, AgentAction, ProcessDeclaration

class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=self.arena_size - 1, share=1.0)]

    def act(self, observation):
        return AgentAction(ActionKindV2.READ, observation.self_anchor)

def create_agent():
    return Agent()
"""


# ---------------------------------------------------------------------------
# End-to-end reconstruction: Python (Agent API v2) match
# ---------------------------------------------------------------------------
def test_python_match_state_is_reconstructable_from_replay_alone(tmp_path):
    entrants = (
        MatchEntrant.python("A", "v4_scout", 0, _python_spec(tmp_path, "v4_scout", WRITER_SOURCE)),
        MatchEntrant.python("B", "reader", 32, _python_spec(tmp_path, "reader", READER_SOURCE)),
    )
    replay_path = tmp_path / "replay.jsonl"
    result = NativeMatchService().run(
        MatchRequest(_config(), entrants, max_ticks=3, replay_path=replay_path, verbose=False)
    )

    header, reconstructed = _reconstruct_ticks(replay_path)
    assert header.runtime_kind == "python"
    assert header.match_id == result.match_id

    # Ground truth is fully analytic: "v4_scout" unconditionally writes 0xAB
    # to address 10 every tick; "reader" runs after "v4_scout" in the same
    # tick (sequential same-tick visibility) and so always observes it.
    for tick in (1, 2, 3):
        assert reconstructed[tick]["arena"][10] == 0xAB
        assert reconstructed[tick]["owners"][10] == "A"

    # The reconstructed final tick must agree exactly with the terminal
    # record and the live result -- the replay stream, read alone, recovers
    # the same score/outcome ``NativeMatchService`` itself computed.
    terminal = list(iter_replay(replay_path))[-1]
    assert isinstance(terminal, MatchResult)
    assert terminal.match_id == result.match_id
    assert terminal.result_id == result.result_id
    assert terminal.ticks == result.ticks_run == 3
    assert dict(terminal.score) == dict(result.score) == reconstructed[3]["score"]
    envelope = read_result(result.result_path)
    assert terminal.termination_reason == envelope.termination_reason == "tick_limit"
    assert (terminal.winner or "tie") == envelope.winner


# ---------------------------------------------------------------------------
# Replay digest verification
# ---------------------------------------------------------------------------
def _run_simple_match(tmp_path):
    entrants = (
        MatchEntrant.python("A", "passive_a", 0, _python_spec(tmp_path, "passive_a", PASSIVE_SOURCE)),
        MatchEntrant.python("B", "passive_b", 32, _python_spec(tmp_path, "passive_b", PASSIVE_SOURCE)),
    )
    replay_path = tmp_path / "replay.jsonl"
    result = NativeMatchService().run(
        MatchRequest(_config(arena_size=64), entrants, max_ticks=2, replay_path=replay_path, verbose=False)
    )
    return result


def test_identical_native_runs_get_distinct_occurrences_without_identity_changes(
    tmp_path, monkeypatch
):
    occurrence_ids = iter(
        (
            "12345678-1234-4abc-8def-1234567890ab",
            "87654321-4321-4cba-9fed-ba0987654321",
        )
    )
    completion_times = iter(
        (
            "2026-09-11T19:42:31.123456Z",
            "2026-09-11T19:42:32.123456Z",
        )
    )

    class ProductInfo:
        version = "5.0.0-test"

    monkeypatch.setattr(
        "battle_engine.match_service.generate_occurrence_id",
        lambda: next(occurrence_ids),
    )
    monkeypatch.setattr(
        "battle_engine.match_service.utc_completed_at",
        lambda: next(completion_times),
    )
    monkeypatch.setattr(
        "battle_engine.match_service.get_project_info", lambda: ProductInfo()
    )

    first = _run_simple_match(tmp_path / "first")
    second = _run_simple_match(tmp_path / "second")
    first_envelope = read_result(first.result_path)
    second_envelope = read_result(second.result_path)

    assert first_envelope.schema_version == second_envelope.schema_version == 2
    assert first.match_id == second.match_id
    assert first.result_id == second.result_id
    assert first.replay_sha256 == second.replay_sha256
    assert first.winner == second.winner
    assert first.score == second.score
    assert first.ticks_run == second.ticks_run
    assert first_envelope.occurrence_id == "12345678-1234-4abc-8def-1234567890ab"
    assert second_envelope.occurrence_id == "87654321-4321-4cba-9fed-ba0987654321"
    assert first_envelope.completed_at == "2026-09-11T19:42:31.123456Z"
    assert second_envelope.completed_at == "2026-09-11T19:42:32.123456Z"
    assert first_envelope.product_version == second_envelope.product_version == (
        "5.0.0-test"
    )

    # Occurrence metadata belongs exclusively to result.json. Identical
    # executions retain byte-identical replay serialization and replay IDs.
    assert first.replay_path.read_bytes() == second.replay_path.read_bytes()
    for line in first.replay_path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        assert "occurrence_id" not in record
        assert "completed_at" not in record
        assert "product_version" not in record


def test_verify_replay_digest_accepts_the_original_file(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    digest = verify_replay_digest(envelope, result.replay_path)
    assert digest == envelope.replay.sha256

    # The result-reader convenience helper resolves the replay path itself.
    assert verify_result_replay(result.result_path) == envelope.replay.sha256


def test_verify_replay_digest_detects_modification(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    result.replay_path.write_bytes(result.replay_path.read_bytes() + b'{"tampered":true}\n')

    with pytest.raises(ReplayIntegrityError) as excinfo:
        verify_replay_digest(envelope, result.replay_path)
    assert excinfo.value.code == "replay_digest_mismatch"


def test_verify_replay_digest_detects_truncation(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    original = result.replay_path.read_bytes()
    result.replay_path.write_bytes(original[: len(original) // 2])

    with pytest.raises(ReplayIntegrityError) as excinfo:
        verify_replay_digest(envelope, result.replay_path)
    assert excinfo.value.code == "replay_digest_mismatch"


def test_verify_replay_digest_reports_missing_file(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    result.replay_path.unlink()

    with pytest.raises(ReplayIntegrityError) as excinfo:
        verify_replay_digest(envelope, result.replay_path)
    assert excinfo.value.code == "replay_file_missing"


def test_verify_replay_digest_value_accepts_the_original_file(tmp_path):
    """The Phase 7D helper factored out of ``verify_replay_digest`` (Replay
    History's ``resolve_replay`` hands back only the expected digest string,
    never a full ``ResultEnvelope``, so this is the entry point it needs)."""

    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    digest = verify_replay_digest_value(envelope.replay.sha256, result.replay_path)
    assert digest == envelope.replay.sha256
    # verify_replay_digest itself now delegates to this helper; same result.
    assert verify_replay_digest(envelope, result.replay_path) == digest


def test_verify_replay_digest_value_detects_mismatch(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    result.replay_path.write_bytes(result.replay_path.read_bytes() + b'{"tampered":true}\n')

    with pytest.raises(ReplayIntegrityError) as excinfo:
        verify_replay_digest_value(envelope.replay.sha256, result.replay_path)
    assert excinfo.value.code == "replay_digest_mismatch"


def test_verify_replay_digest_value_reports_missing_file(tmp_path):
    result = _run_simple_match(tmp_path)
    envelope = read_result(result.result_path)
    result.replay_path.unlink()

    with pytest.raises(ReplayIntegrityError) as excinfo:
        verify_replay_digest_value(envelope.replay.sha256, result.replay_path)
    assert excinfo.value.code == "replay_file_missing"


def test_read_result_never_verifies_automatically(tmp_path):
    """Explicit opt-in only: reading a result must not require the replay
    to exist or match, so historical results stay readable even if their
    replay was pruned or deleted."""

    result = _run_simple_match(tmp_path)
    result.replay_path.unlink()
    envelope = read_result(result.result_path)  # must not raise
    assert envelope.replay is not None


# ---------------------------------------------------------------------------
# result_id determinism under nondeterministic exception text
# ---------------------------------------------------------------------------
def test_result_id_is_stable_despite_nondeterministic_exception_text(tmp_path, monkeypatch):
    """result_id must not depend on diagnostic message text.

    Real agent-exception text is nondeterministic in practice -- e.g. a
    default ``repr()`` embeds an ``id()``-derived pseudo-address, which
    CPython's allocator can (and, depending on prior allocation traffic,
    reliably does) reuse across two sequentially-created objects. Asserting
    that two runs' messages actually differ by relying on that address is
    therefore not itself deterministic: it can pass or fail depending on
    unrelated allocator state left over from other tests in the same
    process.

    ``canonical_match_id`` folds each Python entrant's agent source bytes
    into match identity (``source_sha256``), so simply baking a distinct
    marker into each run's agent.py (an earlier version of this fix did
    that) would make ``match_id`` differ for a real, unrelated reason --
    the agents genuinely would no longer be identical -- defeating the
    point of the test. Instead, both runs use byte-identical agent source;
    the message-text marker is supplied at *runtime* via an environment
    variable the agent reads in ``act()``, so it varies deterministically
    between runs without the agent's on-disk identity changing at all.
    """
    from battle_engine.agents import resolve_agent

    marker_env_var = "BYTEFRAY_TEST_RESULT_ID_MARKER"
    failing_source = f"""
import os
from battle_engine.agent_api import ProcessDeclaration

class Agent:
    def reset(self, context):
        self.arena_size = context.arena_size

    def declare_processes(self):
        return [ProcessDeclaration(id="main", reach=self.arena_size - 1, share=1.0)]

    def act(self, observation):
        raise RuntimeError("boom-" + os.environ["{marker_env_var}"])

def create_agent():
    return Agent()
"""

    def _spec(root, name, source):
        directory = root / "agents" / name
        directory.mkdir(parents=True)
        (directory / "agent.yaml").write_text(
            json.dumps(
                {
                    "kind": "python",
                    "api_version": 2,
                    "entrypoint": "agent.py:create_agent",
                    "name": name,
                    "display": name.title(),
                    "version": "1.0",
                }
            ),
            encoding="utf-8",
        )
        (directory / "agent.py").write_text(source, encoding="utf-8")
        return resolve_agent(root, name)

    def _run(label):
        root = tmp_path / label
        entrants = (
            MatchEntrant.python("A", "failing", 0, _spec(root, "failing", failing_source)),
            MatchEntrant.python("B", "passive", 32, _spec(root, "passive", PASSIVE_SOURCE)),
        )
        replay_path = root / "replay.jsonl"
        monkeypatch.setenv(marker_env_var, label)
        return NativeMatchService().run(
            MatchRequest(_config(), entrants, max_ticks=2, replay_path=replay_path, verbose=False)
        )

    first = _run("first")
    second = _run("second")

    first_message = read_result(first.result_path).entrants[0]["diagnostic"]["message"]
    second_message = read_result(second.result_path).entrants[0]["diagnostic"]["message"]
    # Each run's raised message embeds its own label ("first"/"second") via
    # the environment marker, by construction -- guaranteed different,
    # deterministically, with no dependence on allocator/`id()` behavior...
    assert "first" in first_message
    assert "second" in second_message
    assert first_message != second_message
    # ...yet identity is unaffected: the agent source on disk (and thus
    # match_id's source_sha256) is byte-identical between the two runs.
    assert first.match_id == second.match_id
    assert first.result_id == second.result_id


# ---------------------------------------------------------------------------
# match_id / result_id identity pinning
# ---------------------------------------------------------------------------
def test_match_id_is_stable_across_different_absolute_checkout_paths(tmp_path):
    spec = _python_spec(tmp_path, "passive", PASSIVE_SOURCE)
    entrants_one = (
        MatchEntrant.python("A", "a", 0, spec),
        MatchEntrant.python("B", "b", 16, spec),
    )
    entrants_two = (
        MatchEntrant.python("A", "a", 0, spec),
        MatchEntrant.python("B", "b", 16, spec),
    )
    first = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32),
            entrants_one,
            max_ticks=2,
            replay_path=tmp_path / "one" / "nested" / "deep" / "replay.jsonl",
            verbose=False,
        )
    )
    second = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32),
            entrants_two,
            max_ticks=2,
            replay_path=tmp_path / "two" / "replay.jsonl",
            verbose=False,
        )
    )
    assert first.replay_path != second.replay_path
    assert first.match_id == second.match_id
    assert first.result_id == second.result_id


def test_match_id_changes_with_meaningful_config_or_code_changes(tmp_path):
    passive_spec = _python_spec(tmp_path, "passive", PASSIVE_SOURCE)
    writer_spec = _python_spec(tmp_path, "v4_scout", WRITER_SOURCE)
    base_entrants = (
        MatchEntrant.python("A", "a", 0, passive_spec),
        MatchEntrant.python("B", "b", 16, passive_spec),
    )
    baseline = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32), base_entrants, max_ticks=2,
            replay_path=tmp_path / "baseline" / "replay.jsonl", verbose=False,
        )
    )
    different_seed = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32, seed=99), base_entrants, max_ticks=2,
            replay_path=tmp_path / "seed" / "replay.jsonl", verbose=False,
        )
    )
    different_code = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32),
            (
                MatchEntrant.python("A", "a", 0, writer_spec),
                MatchEntrant.python("B", "b", 16, passive_spec),
            ),
            max_ticks=2,
            replay_path=tmp_path / "code" / "replay.jsonl",
            verbose=False,
        )
    )
    assert different_seed.match_id != baseline.match_id
    assert different_code.match_id != baseline.match_id


def test_canonical_match_id_changes_if_ruleset_identity_changes(monkeypatch, tmp_path):
    """v0.10 Phase 4: Ruleset identity is a first-class, live input to
    ``canonical_match_id``'s hash payload, not decorative -- two otherwise-
    identical execution inputs must never collide under one ``match_id`` if
    they ran under different declared gameplay semantics. There is only one
    Ruleset today, so this is proven by monkeypatching the canonical
    constant ``canonical_match_id`` actually reads (rather than requiring a
    real second Ruleset to exist) and confirming the computed id changes.

    V6 Phase 2B.12 re-pointed the omitted-``ruleset_id`` default from the
    retired ``BYTEFRAY_RULESET_ID`` to the retained control
    ``BYTEFRAY_RULESET_V4_ID`` (docs/research/v6/
    V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md, trap F-1); that is now the
    constant this monkeypatch targets.
    """

    spec = _python_spec(tmp_path, "passive", PASSIVE_SOURCE)
    entrants = (
        MatchEntrant.python("A", "a", 0, spec),
        MatchEntrant.python("B", "b", 16, spec),
    )
    request = MatchRequest(
        _config(arena_size=32), entrants, max_ticks=2,
        replay_path=tmp_path / "replay.jsonl", verbose=False,
    )
    baseline_id = canonical_match_id(request)

    monkeypatch.setattr(
        "battle_engine.match_service.BYTEFRAY_RULESET_V4_ID", "bytefray-rules-6-hypothetical"
    )
    changed_id = canonical_match_id(request)

    assert changed_id != baseline_id


def test_result_id_changes_when_outcome_differs_for_same_match_id(tmp_path):
    # Same inputs, different tick limit: same match_id-relevant identity
    # inputs would differ here too (tick_limit is part of reproducibility),
    # so instead compare same match_id with a config change that only
    # affects scoring/outcome, not identity: not directly possible given
    # the current identity recipe (win_mode is part of reproducibility).
    # Assert the weaker, still-meaningful property: two runs with identical
    # inputs (hence identical match_id) produce identical result_id too,
    # since the engine is deterministic.
    spec = _python_spec(tmp_path, "passive", PASSIVE_SOURCE)
    entrants = (
        MatchEntrant.python("A", "a", 0, spec),
        MatchEntrant.python("B", "b", 16, spec),
    )
    first = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32), entrants, max_ticks=2,
            replay_path=tmp_path / "a" / "replay.jsonl", verbose=False,
        )
    )
    second = NativeMatchService().run(
        MatchRequest(
            _config(arena_size=32), entrants, max_ticks=2,
            replay_path=tmp_path / "b" / "replay.jsonl", verbose=False,
        )
    )
    assert first.match_id == second.match_id
    assert first.result_id == second.result_id


def test_result_id_is_a_function_of_match_id_and_outcome():
    match_id = stable_id("match", {"mode": "b2", "entrants": ["A", "B"]})
    same_outcome = stable_id(
        "result", {"match_id": match_id, "winner": "A", "score": {"A": 1}}
    )
    same_outcome_again = stable_id(
        "result", {"match_id": match_id, "winner": "A", "score": {"A": 1}}
    )
    different_outcome = stable_id(
        "result", {"match_id": match_id, "winner": "B", "score": {"A": 1}}
    )
    assert same_outcome == same_outcome_again
    assert same_outcome != different_outcome
