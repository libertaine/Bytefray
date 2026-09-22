"""V6 research-integrity hardening, Part B: standalone native-match source TOCTOU.

The independent repository-wide review that closed V6 Phase 3 flagged a
suspected defect: ``NativeMatchService`` freezes each Python entrant's
source digest once, before a match ticks (``process_runtime.
ProcessMatchController.from_python_entrants``), but ``canonical_match_id``
used to re-read the same on-disk source a second time during post-execution
finalization (``match_service._finalize_native_artifacts``). If an entrant's
source file changed on disk while the match was executing, the executed
code and the persisted ``match_id``/entrant metadata could describe two
different source versions.

This module reproduces that window deterministically (proving the defect
existed against the pre-fix code path) and then pins the corrected
invariant as an ordinary regression test: a match's persisted identity and
entrant provenance must always derive from the same frozen source digest
that actually executed, never a second independent disk read taken after
execution has already finished.
"""

from __future__ import annotations

import hashlib

from battle_engine.config import Config
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    canonical_match_id,
)
from battle_engine.process_runtime import ProcessMatchController


def _config(arena_size=32, instr_per_tick=8, seed=1337):
    return Config(arena_size=arena_size, instr_per_tick=instr_per_tick, seed=seed)


def _python_spec(root, name, source):
    import json

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


def test_match_identity_derives_from_frozen_execution_source_not_a_post_execution_reread(
    monkeypatch, tmp_path
):
    """Reproduce, then pin closed, the standalone native-match source TOCTOU.

    Sequence, matching the suspected defect's shape exactly:

    1. Resolve a candidate + opponent agent and capture the candidate's
       initial on-disk source digest.
    2. Run a real match, but mutate the candidate's source file on disk at
       the one seam guaranteed to fall strictly *after* execution has
       frozen its source digest (``ProcessMatchController.from_python_
       entrants``, called before ``ProcessMatchController.run``) and
       strictly *before* finalization computes ``match_id``.
    3. Confirm the mutation actually landed (sanity), confirm the entrant's
       own recorded provenance (``metadata["source_sha256"]``) is the
       *pre*-mutation digest (proving execution used the frozen source, not
       the mutated one), and confirm the persisted ``match_id`` matches what
       ``canonical_match_id`` computes from that same frozen digest.
    4. Prove the fix is load-bearing, not incidental: an independent,
       *unfrozen* ``canonical_match_id(request)`` call made now (mirroring
       exactly what the pre-fix finalize path used to compute, since it
       passed no frozen digest at all) reads the *current* -- mutated --
       source and must disagree with the persisted ``match_id``. Before the
       fix, ``result.match_id`` *was* this stale re-read value; this
       assertion is what the pre-fix code fails.
    """

    candidate_spec = _python_spec(tmp_path, "candidate", PASSIVE_SOURCE)
    opponent_spec = _python_spec(tmp_path, "opponent", PASSIVE_SOURCE)
    entrants = (
        MatchEntrant.python("A", "candidate", 0, candidate_spec),
        MatchEntrant.python("B", "opponent", 16, opponent_spec),
    )
    request = MatchRequest(
        _config(), entrants, max_ticks=3,
        replay_path=tmp_path / "replay.jsonl", verbose=False,
    )

    initial_digest = hashlib.sha256(candidate_spec.source_path.read_bytes()).hexdigest()

    real_run = ProcessMatchController.run
    mutation_state = {"applied": False}

    def _mutate_source_then_run(self, *args, **kwargs):
        # Fires after `from_python_entrants` has already frozen every
        # entrant's `source_digest` (it runs strictly before a
        # `ProcessMatchController` -- and therefore before `.run()` can be
        # called on one) and before finalization has computed `match_id`.
        # This is exactly the "source changes while a match is executing"
        # window Part B describes.
        if not mutation_state["applied"]:
            candidate_spec.source_path.write_text(
                PASSIVE_SOURCE + "\n# mutated while the match was executing\n",
                encoding="utf-8",
            )
            mutation_state["applied"] = True
        return real_run(self, *args, **kwargs)

    monkeypatch.setattr(ProcessMatchController, "run", _mutate_source_then_run)

    result = NativeMatchService().run(request)

    assert mutation_state["applied"]
    mutated_digest = hashlib.sha256(candidate_spec.source_path.read_bytes()).hexdigest()
    assert mutated_digest != initial_digest, "sanity: the mutation must actually change the file"

    executed_digest = result.agents_by_id["A"].metadata["source_sha256"]
    assert executed_digest == initial_digest, (
        "the entrant's own recorded provenance must describe the source that "
        "actually executed (frozen before ticking), not the post-execution "
        "mutated file"
    )

    frozen_source_digests = {
        agent.agent_id: agent.metadata["source_sha256"] for agent in result.agents
    }
    expected_id_from_frozen_source = canonical_match_id(
        request, frozen_source_digests=frozen_source_digests
    )
    assert result.match_id == expected_id_from_frozen_source, (
        "the persisted match_id must derive from the same frozen entrant "
        "source identity used for execution"
    )

    # The pre-fix computation: no frozen digest at all, so it re-reads
    # `candidate_spec.source_path` fresh -- which is now the mutated file.
    stale_reread_id = canonical_match_id(request)
    assert result.match_id != stale_reread_id, (
        "a match_id that happened to equal a fresh post-execution re-read "
        "of (now-mutated) entrant source would mean identity is following "
        "disk content instead of the source that actually ran -- the "
        "defect this test reproduces and pins closed"
    )


def test_unchanged_source_still_produces_identical_match_id_via_frozen_digest(tmp_path):
    """Ordinary-case control: when source never changes, the frozen-digest
    path and a fresh independent re-read agree exactly, so no ordinary
    match_id changes as a result of the TOCTOU fix.
    """

    candidate_spec = _python_spec(tmp_path, "candidate", PASSIVE_SOURCE)
    opponent_spec = _python_spec(tmp_path, "opponent", PASSIVE_SOURCE)
    entrants = (
        MatchEntrant.python("A", "candidate", 0, candidate_spec),
        MatchEntrant.python("B", "opponent", 16, opponent_spec),
    )
    request = MatchRequest(
        _config(), entrants, max_ticks=3,
        replay_path=tmp_path / "replay.jsonl", verbose=False,
    )

    result = NativeMatchService().run(request)

    unfrozen_id = canonical_match_id(request)
    assert result.match_id == unfrozen_id
