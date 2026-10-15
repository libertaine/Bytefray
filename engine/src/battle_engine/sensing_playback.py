"""Bytefray V6 M1-3: Artifact Validation and Sensing-Exchange Reconstruction.

Independently validates demonstration and match execution artifacts
(replay.jsonl, trace.jsonl, result.json, demo.json) and reconstructs the
complete sub-tick sensing exchange without trusting runner narrative or
sidecar assertions.

Operates under public experimental Ruleset bytefray-rules-6-alpha1 and
preserves existing replay4, trace2, and result2 wire schemas.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from battle_engine.agent_trace import (
    ABSENT,
    DecisionRecordV2,
    ResetRecord,
    TraceFormatError,
    read_trace_v2,
)
from battle_engine.paths import contained_path
from battle_engine.python_runtime import core_addresses
from battle_engine.replay import (
    MemoryDiff,
    TickSnapshot,
)
from battle_engine.result_model import (
    read_result,
    verify_replay_digest,
)
from battle_engine.rules import BYTEFRAY_RULESET_V6_ALPHA1_ID
from battle_engine.ruleset_policy import (
    ACTIVE_SENSING_HALF_WIDTH,
    resolve_ruleset_policy,
)
from battle_engine.spectator_derivation import (
    PairBinding,
    PairBindingError,
    PairConsistencyError,
    verify_pair,
)
from battle_engine.spectator_events import (
    SpectatorAnalysisError,
    circular_distance,
    load_schema4_replay,
)

DEMO_SCHEMA = "bytefray.sensing_demo"
DEMO_SCHEMA_VERSION = 1
DEMO_PROVENANCE = "product_teaching_demo"

PLAYBACK_SCHEMA = "bytefray.sensing_playback"
PLAYBACK_SCHEMA_VERSION = 1

EXPECTED_RULESET_ID = BYTEFRAY_RULESET_V6_ALPHA1_ID
EXPECTED_SENSING_WINDOW = ACTIVE_SENSING_HALF_WIDTH


class SensingPlaybackError(ValueError):
    """Base error for sensing playback validation and reconstruction failures."""


class ArtifactIntegrityError(SensingPlaybackError, PairBindingError):
    """Artifact files are missing, malformed, or have mismatched hashes/identities."""


class ExchangeReconstructionError(SensingPlaybackError):
    """Trace records contradict gameplay rules, illegal sensing, or quota/costs."""


class ExchangeConsistencyError(SensingPlaybackError, PairConsistencyError):
    """Replay and trace disagree on match state or progression."""


class ExchangePhase(str, Enum):
    """The execution phase represented by an exchange fact."""

    OBSERVATION = "OBSERVATION"
    ACTION = "ACTION"
    TICK_END = "TICK_END"


class VerificationStatus(str, Enum):
    """Verification classification for teaching exchange steps."""

    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    NOT_PROVEN = "NOT_PROVEN"


@dataclass(frozen=True)
class SubTickWorldState:
    """Immutable snapshot of the arena world state at one sub-tick phase."""

    tick: int
    decision_index: int | None
    phase: ExchangePhase
    anchors: dict[tuple[str, str], int]
    alive_entrants: frozenset[str]
    disrupted_processes: frozenset[tuple[str, str]]
    memory: bytes
    owners: tuple[str | None, ...]

    def get_anchor(self, entrant_id: str, process_id: str) -> int | None:
        """Return the current anchor position of a process, or None."""
        return self.anchors.get((entrant_id, process_id))

    def is_disrupted(self, entrant_id: str, process_id: str) -> bool:
        """Return True if the specified process is currently disrupted."""
        return (entrant_id, process_id) in self.disrupted_processes

    def is_alive(self, entrant_id: str) -> bool:
        """Return True if the entrant is currently alive."""
        return entrant_id in self.alive_entrants


@dataclass(frozen=True)
class SensingExchangeFact:
    """One immutable derived sensing exchange fact in execution order.

    Order is (tick, global_decision_index, phase).
    No sensing result enters an agent audience until receipt.
    """

    tick: int
    decision_index: int | None
    phase: ExchangePhase
    actor_id: str | None
    process_id: str | None
    action_kind: str | None
    status: str | None
    normalized_address: int | None
    operand: int | None
    value: int | None
    cost: int
    sample_point: tuple[int, int] | None
    delivery_point: tuple[int, int] | None
    audience: tuple[str, ...]
    sensed_anchors: tuple[int, ...] | None = None
    read_value: int | None = None
    read_owner: str | None = None
    world_state: SubTickWorldState | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerifiedExchangeStep:
    """Verification finding for one canonical teaching exchange event."""

    step_index: int
    name: str
    status: VerificationStatus
    tick: int | None
    decision_index: int | None
    actor_id: str | None
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeachingExchangeVerification:
    """Independent verification findings for the 7 canonical teaching events."""

    steps: tuple[VerifiedExchangeStep, ...]
    is_verified: bool
    findings: tuple[str, ...]

    @property
    def incomplete_info_before_sensing(self) -> VerificationStatus:
        return self._status_for_index(1)

    @property
    def legal_sense_request(self) -> VerificationStatus:
        return self._status_for_index(2)

    @property
    def one_action_sensing_cost(self) -> VerificationStatus:
        return self._status_for_index(3)

    @property
    def historical_sample_captured(self) -> VerificationStatus:
        return self._status_for_index(4)

    @property
    def anonymous_sample_delivered(self) -> VerificationStatus:
        return self._status_for_index(5)

    @property
    def legal_move_informed(self) -> VerificationStatus:
        return self._status_for_index(6)

    @property
    def optional_write_supported(self) -> VerificationStatus:
        return self._status_for_index(7)

    def _status_for_index(self, index: int) -> VerificationStatus:
        for s in self.steps:
            if s.step_index == index:
                return s.status
        return VerificationStatus.NOT_PROVEN


@dataclass(frozen=True)
class SensingPlayback:
    """Full verified sensing playback model derived from authoritative artifacts."""

    match_id: str
    ruleset_id: str
    arena_size: int
    facts: tuple[SensingExchangeFact, ...]
    sub_tick_states: tuple[SubTickWorldState, ...]
    teaching_verification: TeachingExchangeVerification | None
    binding: PairBinding
    demo_artifacts: dict[str, Any] | None = None


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ArtifactIntegrityError(f"Cannot read artifact file {path}: {exc}") from exc


def _expand(diff: MemoryDiff, arena_size: int) -> list[tuple[int, str | None, int]]:
    return [
        ((diff.address + offset) % arena_size, diff.owner, value)
        for offset, value in enumerate(diff.values)
    ]


def verify_demonstration_artifacts(demo_dir_or_file: Path | str) -> dict[str, Any]:
    """Validate machine-checkable demo.json provenance and SHA-256 bindings.

    Checks:
    1. demo.json schema is bytefray.sensing_demo v1.
    2. provenance identifier is 'product_teaching_demo'.
    3. declared_product_fixture is True.
    4. ruleset_id matches bytefray-rules-6-alpha1.
    5. replay, trace, and result artifact files exist without path traversal.
    6. SHA-256 digests match on-disk file contents.
    7. Cross-bindings with trace and replay agree.

    Raises ArtifactIntegrityError if any check fails.
    """
    target = Path(demo_dir_or_file).expanduser().resolve()
    demo_path = target / "demo.json" if target.is_dir() else target
    if not demo_path.is_file():
        raise ArtifactIntegrityError(f"Demonstration metadata not found: {demo_path}")

    try:
        payload = json.loads(demo_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ArtifactIntegrityError(f"Malformed demonstration metadata JSON in {demo_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ArtifactIntegrityError(f"Demonstration metadata must be a JSON object: {demo_path}")

    if payload.get("schema") != DEMO_SCHEMA:
        raise ArtifactIntegrityError(
            f"Unsupported demo schema {payload.get('schema')!r} (expected {DEMO_SCHEMA!r})"
        )
    if payload.get("schema_version") != DEMO_SCHEMA_VERSION:
        raise ArtifactIntegrityError(
            f"Unsupported demo schema_version {payload.get('schema_version')!r} (expected {DEMO_SCHEMA_VERSION})"
        )
    if payload.get("provenance") != DEMO_PROVENANCE:
        raise ArtifactIntegrityError(
            f"Unauthorized demo provenance {payload.get('provenance')!r} (expected {DEMO_PROVENANCE!r})"
        )
    if payload.get("declared_product_fixture") is not True:
        raise ArtifactIntegrityError(
            f"Demo declared_product_fixture must be True, got {payload.get('declared_product_fixture')!r}"
        )
    if payload.get("ruleset_id") != EXPECTED_RULESET_ID:
        raise ArtifactIntegrityError(
            f"Unexpected demo ruleset_id {payload.get('ruleset_id')!r} (expected {EXPECTED_RULESET_ID!r})"
        )

    match_id = payload.get("match_id")
    if not isinstance(match_id, str) or not match_id:
        raise ArtifactIntegrityError("Demo metadata missing or empty match_id")

    result_id = payload.get("result_id")
    if not isinstance(result_id, str) or not result_id:
        raise ArtifactIntegrityError("Demo metadata missing or empty result_id")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ArtifactIntegrityError("Demo metadata 'artifacts' must be a dictionary")

    base_dir = demo_path.parent
    validated_paths: dict[str, Path] = {}

    for key in ("replay", "trace", "result"):
        entry = artifacts.get(key)
        if not isinstance(entry, dict):
            raise ArtifactIntegrityError(f"Demo metadata artifacts missing required entry for {key!r}")
        filename = entry.get("filename")
        expected_sha = entry.get("sha256")
        if not isinstance(filename, str) or not filename.strip():
            raise ArtifactIntegrityError(f"Demo metadata artifacts[{key!r}] missing filename")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise ArtifactIntegrityError(f"Demo metadata artifacts[{key!r}] invalid sha256: {expected_sha!r}")

        file_path = contained_path(base_dir, filename)
        if file_path is None or not file_path.is_file():
            raise ArtifactIntegrityError(f"Demo artifact file for {key!r} not found or unsafe: {filename}")

        actual_sha = _sha256_file(file_path)
        if actual_sha != expected_sha:
            raise ArtifactIntegrityError(
                f"Digest mismatch for {key!r} ({file_path.name}): expected {expected_sha}, actual {actual_sha}"
            )
        validated_paths[key] = file_path

    # Validate result.json association and match IDs
    result_file = validated_paths["result"]
    try:
        result_envelope = read_result(result_file)
    except Exception as exc:
        raise ArtifactIntegrityError(f"Unreadable result artifact {result_file}: {exc}") from exc

    if result_envelope.match_id != match_id:
        raise ArtifactIntegrityError(
            f"Result match_id {result_envelope.match_id!r} contradicts demo match_id {match_id!r}"
        )
    if result_envelope.result_id != result_id:
        raise ArtifactIntegrityError(
            f"Result result_id {result_envelope.result_id!r} contradicts demo result_id {result_id!r}"
        )
    if result_envelope.ruleset_id != EXPECTED_RULESET_ID:
        raise ArtifactIntegrityError(
            f"Result ruleset_id {result_envelope.ruleset_id!r} contradicts demo ruleset_id {EXPECTED_RULESET_ID!r}"
        )
    if (
        result_envelope.replay is not None
        and result_envelope.replay.sha256 != artifacts["replay"]["sha256"]
    ):
        raise ArtifactIntegrityError(
            f"Result replay sha256 {result_envelope.replay.sha256} contradicts demo replay sha256"
        )

    # Validate entrants metadata integrity
    entrants = payload.get("entrants")
    if not isinstance(entrants, list) or not entrants:
        raise ArtifactIntegrityError("Demo metadata 'entrants' must be a non-empty list")
    for entrant in entrants:
        if not isinstance(entrant, dict):
            raise ArtifactIntegrityError("Demo metadata entrant entry must be a dictionary")
        if entrant.get("drift_detected") is True:
            raise ArtifactIntegrityError(
                f"Entrant {entrant.get('agent_id')} declared runtime drift in demo metadata"
            )
        if entrant.get("capture_complete") is False:
            raise ArtifactIntegrityError(
                f"Entrant {entrant.get('agent_id')} source capture incomplete in demo metadata"
            )

    # Validate config
    config = payload.get("config")
    if not isinstance(config, dict):
        raise ArtifactIntegrityError("Demo metadata 'config' must be a dictionary")

    return {
        "demo_path": demo_path,
        "payload": payload,
        "paths": validated_paths,
    }


def evaluate_teaching_exchange(
    facts: Sequence[SensingExchangeFact],
    arena_size: int = 512,
    scout_id: str = "A",
    *,
    scout_name: str | None = None,
) -> TeachingExchangeVerification:
    """Independently establish the 7 canonical Window Scout teaching events from facts.

    Each step reports only what replay and trace facts show. Steps not
    reached in the recording are NOT_PROVEN, and ``is_verified`` requires
    steps 1-6 to be VERIFIED, so a consistent but incomplete recording is
    never a completed teaching exchange. No step asserts agent intent.
    ``scout_name`` is the evaluated entrant's replay-header name; step
    descriptions name that entrant, never an assumed Window Scout.
    """
    steps: list[VerifiedExchangeStep] = []
    findings: list[str] = []
    entrant_label = f"Entrant {scout_id}" + (f" ({scout_name})" if scout_name else "")

    # Locate SENSE(91) action fact for scout
    sense_fact = next(
        (
            f
            for f in facts
            if f.phase == ExchangePhase.ACTION
            and f.actor_id == scout_id
            and f.action_kind == "sense"
            and f.operand == 91
        ),
        None,
    )

    # 1. Incomplete opponent information before sensing
    step1_verified = False
    step1_ev: dict[str, Any] = {}
    if sense_fact is not None and sense_fact.decision_index is not None:
        obs_before_sense = next(
            (
                f
                for f in facts
                if f.phase == ExchangePhase.OBSERVATION
                and f.actor_id == scout_id
                and f.decision_index == sense_fact.decision_index
            ),
            None,
        )
        # Check all observations for scout up to and including this decision
        prior_observations = [
            f
            for f in facts
            if f.phase == ExchangePhase.OBSERVATION
            and f.actor_id == scout_id
            and f.decision_index is not None
            and f.decision_index <= sense_fact.decision_index
        ]
        leaks = [
            f
            for f in prior_observations
            if f.sensed_anchors is not None
            or f.detail.get("visible_enemy_anchor_addresses", ()) != ()
        ]
        if obs_before_sense is not None and not leaks:
            step1_verified = True
            step1_ev = {
                "tick": obs_before_sense.tick,
                "decision_index": obs_before_sense.decision_index,
                "visible_enemy_anchors": (),
                "previous_sense": None,
            }
            steps.append(
                VerifiedExchangeStep(
                    step_index=1,
                    name="incomplete_info_before_sensing",
                    status=VerificationStatus.VERIFIED,
                    tick=obs_before_sense.tick,
                    decision_index=obs_before_sense.decision_index,
                    actor_id=scout_id,
                    description=f"{entrant_label} begins with no initial contacts (visible enemy set empty, prior sense absent).",
                    evidence=step1_ev,
                )
            )
            findings.append("VERIFIED: Incomplete opponent information before sensing.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=1,
                    name="incomplete_info_before_sensing",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=obs_before_sense.tick if obs_before_sense else None,
                    decision_index=obs_before_sense.decision_index if obs_before_sense else None,
                    actor_id=scout_id,
                    description="Observation prior to sensing disclosed enemy contacts or prior sensing data.",
                    evidence=step1_ev,
                )
            )
            findings.append("NOT_VERIFIED: Observation prior to sensing disclosed enemy contacts or prior sensing data.")
    else:
        # No SENSE fact found; check if initial observation leaked information
        first_obs = next(
            (f for f in facts if f.phase == ExchangePhase.OBSERVATION and f.actor_id == scout_id),
            None,
        )
        if first_obs is not None and (
            first_obs.sensed_anchors is not None
            or first_obs.detail.get("visible_enemy_anchor_addresses", ()) != ()
        ):
            steps.append(
                VerifiedExchangeStep(
                    step_index=1,
                    name="incomplete_info_before_sensing",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=first_obs.tick,
                    decision_index=first_obs.decision_index,
                    actor_id=scout_id,
                    description="Initial observation disclosed enemy contacts or prior sensing data.",
                )
            )
            findings.append("NOT_VERIFIED: Initial observation disclosed enemy contacts or prior sensing data.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=1,
                    name="incomplete_info_before_sensing",
                    status=VerificationStatus.NOT_PROVEN,
                    tick=first_obs.tick if first_obs else None,
                    decision_index=first_obs.decision_index if first_obs else None,
                    actor_id=scout_id,
                    description="Cannot establish pre-sensing knowledge state without SENSE request.",
                )
            )
            findings.append("NOT_PROVEN: Incomplete opponent information before sensing.")

    # 2. Legal SENSE(91) request
    step2_verified = False
    step2_ev: dict[str, Any] = {}
    if sense_fact is not None:
        act_anchor = (
            sense_fact.world_state.get_anchor(scout_id, sense_fact.process_id or "main")
            if sense_fact.world_state else 0
        )
        norm_op = 91 % arena_size
        dist = circular_distance(act_anchor or 0, norm_op, arena_size)
        if dist <= 128 and sense_fact.status == "APPLIED":
            step2_verified = True
            step2_ev = {
                "tick": sense_fact.tick,
                "decision_index": sense_fact.decision_index,
                "target": 91,
                "distance": dist,
                "status": "APPLIED",
            }
            steps.append(
                VerifiedExchangeStep(
                    step_index=2,
                    name="legal_sense_request",
                    status=VerificationStatus.VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description=f"{entrant_label} requests legal SENSE(91) within reach; status APPLIED.",
                    evidence=step2_ev,
                )
            )
            findings.append("VERIFIED: Legal SENSE(91) request in reach.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=2,
                    name="legal_sense_request",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description=f"SENSE(91) request was invalid or rejected (dist={dist}, status={sense_fact.status}).",
                    evidence={"distance": dist, "status": sense_fact.status},
                )
            )
            findings.append("NOT_VERIFIED: Legal SENSE(91) request in reach.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=2,
                name="legal_sense_request",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Legal SENSE(91) request was not found in recorded sequence.",
            )
        )
        findings.append("NOT_PROVEN: Legal SENSE(91) request in reach.")

    # 3. One-action sensing cost
    step3_verified = False
    step3_ev: dict[str, Any] = {}
    if sense_fact is not None:
        if sense_fact.cost == 1:
            step3_verified = True
            step3_ev = {
                "cost": 1,
                "world_mutation": False,
            }
            steps.append(
                VerifiedExchangeStep(
                    step_index=3,
                    name="one_action_sensing_cost",
                    status=VerificationStatus.VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description="Sensing consumed exactly 1 action opportunity with zero world mutation.",
                    evidence=step3_ev,
                )
            )
            findings.append("VERIFIED: One-action sensing cost.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=3,
                    name="one_action_sensing_cost",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description=f"Sensing cost was {sense_fact.cost} instead of 1.",
                    evidence={"cost": sense_fact.cost},
                )
            )
            findings.append("NOT_VERIFIED: One-action sensing cost.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=3,
                name="one_action_sensing_cost",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Cannot establish sensing cost without SENSE action.",
            )
        )
        findings.append("NOT_PROVEN: One-action sensing cost.")

    # 4. Historical sensing sample captured at execution point
    step4_verified = False
    step4_ev: dict[str, Any] = {}
    if sense_fact is not None and sense_fact.sample_point is not None:
        expected_sample_pt = (sense_fact.tick, sense_fact.decision_index)
        if (
            sense_fact.sensed_anchors == (91,)
            and sense_fact.sample_point == expected_sample_pt
            and scout_id not in sense_fact.audience
        ):
            step4_verified = True
            step4_ev = {
                "sample": (91,),
                "sample_point": sense_fact.sample_point,
                "audience_isolated": scout_id not in sense_fact.audience,
            }
            steps.append(
                VerifiedExchangeStep(
                    step_index=4,
                    name="historical_sample_captured",
                    status=VerificationStatus.VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description="Historical sample (91,) captured at execution point and isolated from entrant audience.",
                    evidence=step4_ev,
                )
            )
            findings.append("VERIFIED: Historical sensing sample captured at execution point.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=4,
                    name="historical_sample_captured",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=sense_fact.tick,
                    decision_index=sense_fact.decision_index,
                    actor_id=scout_id,
                    description=f"Captured sample was {sense_fact.sensed_anchors!r} with audience {sense_fact.audience!r}.",
                    evidence={"sample": sense_fact.sensed_anchors, "audience": sense_fact.audience},
                )
            )
            findings.append("NOT_VERIFIED: Historical sensing sample captured at execution point.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=4,
                name="historical_sample_captured",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Cannot establish sample capture without SENSE action.",
            )
        )
        findings.append("NOT_PROVEN: Historical sensing sample captured at execution point.")

    # 5. Anonymous sample delivered at the next eligible same-process callback
    step5_verified = False
    step5_ev: dict[str, Any] = {}
    delivery_obs_fact: SensingExchangeFact | None = None
    if sense_fact is not None and sense_fact.decision_index is not None:
        delivery_obs_fact = next(
            (
                f
                for f in facts
                if f.phase == ExchangePhase.OBSERVATION
                and f.actor_id == scout_id
                and f.process_id == sense_fact.process_id
                and f.decision_index is not None
                and f.decision_index > sense_fact.decision_index
            ),
            None,
        )

    if delivery_obs_fact is not None and sense_fact is not None:
        expected_delivery_pt = (delivery_obs_fact.tick, delivery_obs_fact.decision_index)
        if (
            delivery_obs_fact.sensed_anchors == (91,)
            and delivery_obs_fact.sample_point == sense_fact.sample_point
            and delivery_obs_fact.delivery_point == expected_delivery_pt
            and scout_id in delivery_obs_fact.audience
            and delivery_obs_fact.detail.get("previous_action_applied") is True
        ):
            step5_verified = True
            step5_ev = {
                "delivered_anchors": (91,),
                "delivery_point": delivery_obs_fact.delivery_point,
                "sample_point": delivery_obs_fact.sample_point,
            }
            steps.append(
                VerifiedExchangeStep(
                    step_index=5,
                    name="anonymous_sample_delivered",
                    status=VerificationStatus.VERIFIED,
                    tick=delivery_obs_fact.tick,
                    decision_index=delivery_obs_fact.decision_index,
                    actor_id=scout_id,
                    description="Anonymous sample (91,) delivered at next eligible same-process callback.",
                    evidence=step5_ev,
                )
            )
            findings.append("VERIFIED: Anonymous sample delivered at next eligible same-process callback.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=5,
                    name="anonymous_sample_delivered",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=delivery_obs_fact.tick,
                    decision_index=delivery_obs_fact.decision_index,
                    actor_id=scout_id,
                    description=f"Delivered anchors were {delivery_obs_fact.sensed_anchors!r} (sample_pt={delivery_obs_fact.sample_point}).",
                    evidence={"delivered": delivery_obs_fact.sensed_anchors, "sample_point": delivery_obs_fact.sample_point},
                )
            )
            findings.append("NOT_VERIFIED: Anonymous sample delivered at next eligible same-process callback.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=5,
                name="anonymous_sample_delivered",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Delivery callback did not occur before match ended.",
            )
        )
        findings.append("NOT_PROVEN: Anonymous sample delivered at next eligible same-process callback.")

    # 6. Legal MOVE(64) on the receipt callback, toward the delivered contact.
    # "Informed" means only that the receipt was in the deciding observation.
    # Replay and trace show the applied movement relative to the delivered
    # contact; they cannot show why the agent chose it, so no step claims that.
    step6_verified = False
    step6_ev: dict[str, Any] = {}
    move_fact: SensingExchangeFact | None = None
    if delivery_obs_fact is not None and delivery_obs_fact.decision_index is not None:
        move_fact = next(
            (
                f
                for f in facts
                if f.phase == ExchangePhase.ACTION
                and f.actor_id == scout_id
                and f.decision_index == delivery_obs_fact.decision_index
            ),
            None,
        )

    if move_fact is not None:
        move_process = move_fact.process_id or "main"
        anchor_before = (
            delivery_obs_fact.world_state.get_anchor(scout_id, move_process)
            if delivery_obs_fact is not None and delivery_obs_fact.world_state
            else None
        )
        anchor_after = (
            move_fact.world_state.get_anchor(scout_id, move_process)
            if move_fact.world_state
            else None
        )
        distance_before = (
            circular_distance(anchor_before, 91, arena_size) if anchor_before is not None else None
        )
        distance_after = (
            circular_distance(anchor_after, 91, arena_size) if anchor_after is not None else None
        )
        step6_ev = {
            "tick": move_fact.tick,
            "decision_index": move_fact.decision_index,
            "action": move_fact.action_kind,
            "operand": move_fact.operand,
            "status": move_fact.status,
            "cost": move_fact.cost,
            "delivered_contact": 91,
            "anchor_before": anchor_before,
            "anchor_after": anchor_after,
            "contact_distance_before": distance_before,
            "contact_distance_after": distance_after,
            "receipt_available_at_decision": step5_verified,
            "motivation_established": False,
        }
        if (
            step5_verified
            and move_fact.action_kind == "move"
            and move_fact.operand == 64
            and move_fact.status == "APPLIED"
            and move_fact.cost == 1
            and distance_before is not None
            and distance_after is not None
            and distance_after < distance_before
        ):
            step6_verified = True
            steps.append(
                VerifiedExchangeStep(
                    step_index=6,
                    name="legal_move_informed",
                    status=VerificationStatus.VERIFIED,
                    tick=move_fact.tick,
                    decision_index=move_fact.decision_index,
                    actor_id=scout_id,
                    description=(
                        f"Legal MOVE(+64) applied on the receipt callback: anchor {anchor_before}->{anchor_after} "
                        f"reduces distance to delivered contact 91 from {distance_before} to {distance_after}. "
                        "Artifacts show receipt-consistent movement, not the agent's reason for moving."
                    ),
                    evidence=step6_ev,
                )
            )
            findings.append(
                "VERIFIED: Legal MOVE(64) on the receipt callback reduced distance to the delivered contact "
                "(agent motivation not established)."
            )
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=6,
                    name="legal_move_informed",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=move_fact.tick,
                    decision_index=move_fact.decision_index,
                    actor_id=scout_id,
                    description=(
                        f"Action on the receipt callback was {move_fact.action_kind}({move_fact.operand}) "
                        f"status={move_fact.status}; anchor {anchor_before}->{anchor_after}, distance to "
                        f"delivered contact 91 {distance_before}->{distance_after}."
                    ),
                    evidence=step6_ev,
                )
            )
            findings.append("NOT_VERIFIED: Legal MOVE(64) on the receipt callback toward the delivered contact.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=6,
                name="legal_move_informed",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Move action after delivery was not reached.",
            )
        )
        findings.append("NOT_PROVEN: Legal MOVE(64) informed by delivered observation.")

    # 7. Optional later WRITE(91), when supported by the recorded sequence
    min_write_idx = (
        move_fact.decision_index
        if move_fact and move_fact.decision_index is not None
        else (
            delivery_obs_fact.decision_index
            if delivery_obs_fact and delivery_obs_fact.decision_index is not None
            else (
                sense_fact.decision_index
                if sense_fact and sense_fact.decision_index is not None
                else 0
            )
        )
    )
    write_fact = next(
        (
            f
            for f in facts
            if f.phase == ExchangePhase.ACTION
            and f.actor_id == scout_id
            and f.action_kind == "write"
            and f.operand == 91
            and f.decision_index is not None
            and f.decision_index > min_write_idx
        ),
        None,
    )
    if write_fact is not None:
        if write_fact.status == "APPLIED" and write_fact.cost == 1:
            steps.append(
                VerifiedExchangeStep(
                    step_index=7,
                    name="optional_write_supported",
                    status=VerificationStatus.VERIFIED,
                    tick=write_fact.tick,
                    decision_index=write_fact.decision_index,
                    actor_id=scout_id,
                    description=f"{entrant_label} executes legal in-reach WRITE(91) to sampled address.",
                    evidence={
                        "tick": write_fact.tick,
                        "decision_index": write_fact.decision_index,
                        "target": 91,
                        "value": write_fact.value,
                        "cost": write_fact.cost,
                    },
                )
            )
            findings.append("VERIFIED: Optional later WRITE(91) supported by recorded sequence.")
        else:
            steps.append(
                VerifiedExchangeStep(
                    step_index=7,
                    name="optional_write_supported",
                    status=VerificationStatus.NOT_VERIFIED,
                    tick=write_fact.tick,
                    decision_index=write_fact.decision_index,
                    actor_id=scout_id,
                    description=f"Later WRITE(91) failed with status={write_fact.status} cost={write_fact.cost}.",
                    evidence={"status": write_fact.status, "cost": write_fact.cost},
                )
            )
            findings.append("NOT_VERIFIED: Optional later WRITE(91) failed or rejected.")
    else:
        steps.append(
            VerifiedExchangeStep(
                step_index=7,
                name="optional_write_supported",
                status=VerificationStatus.NOT_PROVEN,
                tick=None,
                decision_index=None,
                actor_id=scout_id,
                description="Optional later WRITE(91) was not executed in the recorded sequence.",
            )
        )
        findings.append("NOT_PROVEN: Optional later WRITE(91) was not executed in the recorded sequence.")

    # All required core steps (1 through 6) must pass. Step 7 is optional but if present must be VERIFIED.
    is_verified = (
        step1_verified
        and step2_verified
        and step3_verified
        and step4_verified
        and step5_verified
        and step6_verified
        and all(s.status != VerificationStatus.NOT_VERIFIED for s in steps)
    )

    return TeachingExchangeVerification(
        steps=tuple(steps),
        is_verified=is_verified,
        findings=tuple(findings),
    )


def reconstruct_sensing_playback(
    replay_path: Path | str,
    trace_path: Path | str,
    *,
    result_path: Path | str | None = None,
    demo_path: Path | str | None = None,
) -> SensingPlayback:
    """Consume replay4/trace2, validate bindings, and independently reconstruct sub-tick facts.

    Reconciles reconstructed tick-end bytes, ownership, anchors, and disruption with
    every canonical replay snapshot. Rejects any corrupted, tampered, or inconsistent
    evidence.
    """
    replay_p = Path(replay_path).expanduser().resolve()
    trace_p = Path(trace_path).expanduser().resolve()

    try:
        binding = verify_pair(replay_p, trace_p)
    except PairBindingError as exc:
        raise ArtifactIntegrityError(f"Pair binding verification failed: {exc}") from exc
    except Exception as exc:
        raise ArtifactIntegrityError(f"Unusable pair: {exc}") from exc

    if result_path is not None:
        result_p = Path(result_path).expanduser().resolve()
        try:
            envelope = read_result(result_p)
            verify_replay_digest(envelope, replay_p)
        except Exception as exc:
            raise ArtifactIntegrityError(f"Result association failed for {result_p}: {exc}") from exc
        if envelope.match_id != binding.match_id:
            raise ArtifactIntegrityError(
                f"Result match_id {envelope.match_id!r} does not match replay match_id {binding.match_id!r}"
            )
        if envelope.ruleset_id != binding.ruleset_id:
            raise ArtifactIntegrityError(
                f"Result ruleset_id {envelope.ruleset_id!r} does not match replay ruleset_id {binding.ruleset_id!r}"
            )

    demo_artifacts_info: dict[str, Any] | None = None
    if demo_path is not None:
        demo_artifacts_info = verify_demonstration_artifacts(demo_path)

    policy = resolve_ruleset_policy(binding.ruleset_id)
    if policy.sensing_mode != "active":
        raise ExchangeReconstructionError(
            f"Ruleset {binding.ruleset_id!r} has sensing_mode {policy.sensing_mode!r}; "
            "sensing exchange reconstruction requires an active sensing ruleset."
        )
    window = policy.sensing_window
    if window is None:
        raise ExchangeReconstructionError(f"Ruleset {binding.ruleset_id!r} has no active sensing window")

    try:
        document = read_trace_v2(trace_p)
    except TraceFormatError as exc:
        raise ArtifactIntegrityError(f"Trace format error in {trace_p}: {exc}") from exc

    try:
        loaded = load_schema4_replay(replay_p)
    except SpectatorAnalysisError as exc:
        raise ArtifactIntegrityError(f"Replay analysis error in {replay_p}: {exc}") from exc

    if result_path is not None and loaded.header.result_id and envelope.result_id != loaded.header.result_id:
        raise ArtifactIntegrityError(
            f"Result result_id {envelope.result_id!r} contradicts replay header {loaded.header.result_id!r}"
        )

    arena_size = loaded.header.config.arena_size
    action_budget = loaded.header.config.instr_per_tick

    # Verify reset records have sensing_window = 27
    resets = tuple(r for r in document.records if isinstance(r, ResetRecord))
    for reset in resets:
        if reset.sensing_window != window:
            raise ExchangeReconstructionError(
                f"Reset record for {reset.agent_id} has sensing_window {reset.sensing_window!r} "
                f"(expected {window})"
            )

    # Process declarations
    declared_reaches: dict[tuple[str, str], int] = {}
    for decl in document.declarations:
        declared_reaches[(decl.agent_id, decl.process_id)] = decl.reach

    # Initialize tick 0 state
    tick_0 = loaded.ticks[0]
    memory = bytearray(arena_size)
    owners: list[str | None] = [None] * arena_size
    for diff in tick_0.memory_diffs:
        for offset, val in enumerate(diff.values):
            addr = (diff.address + offset) % arena_size
            memory[addr] = val
            owners[addr] = diff.owner

    anchors: dict[tuple[str, str], int] = {
        (p.entrant_id, p.process_id): p.anchor for p in tick_0.processes
    }
    alive_entrants: set[str] = {a.agent_id for a in tick_0.agents if a.alive}
    # Each entrant's fixed core, from its tick-zero region start, for the
    # end-of-tick core-capture rule (python_runtime.apply_core_capture).
    core_cells: dict[str, tuple[int, ...]] = {}
    for a in tick_0.agents:
        if a.region is None:
            raise ExchangeReconstructionError(
                f"Tick 0: entrant {a.agent_id} has no recorded core region"
            )
        core_cells[a.agent_id] = core_addresses(a.region[0], arena_size)
    core_zero_streak: dict[str, int] = {}
    disrupted_processes: set[tuple[str, str]] = {
        (p.entrant_id, p.process_id) for p in tick_0.processes if p.disrupted
    }

    initial_world_state = SubTickWorldState(
        tick=0,
        decision_index=None,
        phase=ExchangePhase.TICK_END,
        anchors=dict(anchors),
        alive_entrants=frozenset(alive_entrants),
        disrupted_processes=frozenset(disrupted_processes),
        memory=bytes(memory),
        owners=tuple(owners),
    )

    facts: list[SensingExchangeFact] = [
        SensingExchangeFact(
            tick=0,
            decision_index=None,
            phase=ExchangePhase.TICK_END,
            actor_id=None,
            process_id=None,
            action_kind=None,
            status=None,
            normalized_address=None,
            operand=None,
            value=None,
            cost=0,
            sample_point=None,
            delivery_point=None,
            audience=(),
            world_state=initial_world_state,
        )
    ]
    sub_tick_states: list[SubTickWorldState] = [initial_world_state]

    # Map decisions by tick and verify monotonic tick ordering
    decisions_by_tick: dict[int, list[tuple[int, DecisionRecordV2]]] = {}
    prev_d_tick = 0
    for idx, decision in enumerate(document.decisions):
        d_tick = decision.observation.current_tick
        if d_tick < prev_d_tick:
            raise ExchangeConsistencyError(
                f"Impossible action ordering: decision {idx} records tick {d_tick} after tick {prev_d_tick}"
            )
        prev_d_tick = d_tick
        decisions_by_tick.setdefault(d_tick, []).append((idx, decision))

    pending_sensing: dict[tuple[str, str], tuple[tuple[int, ...], int, int]] = {}
    pending_refusal: dict[tuple[str, str], tuple[int, int]] = {}
    cumulative_writes: dict[str, int] = {}

    ticks_by_number: dict[int, TickSnapshot] = {s.tick: s for s in loaded.ticks}
    max_tick = max(ticks_by_number.keys()) if ticks_by_number else 0

    for current_tick in range(1, max_tick + 1):
        tick_decisions = decisions_by_tick.get(current_tick, [])
        writes_this_tick: list[tuple[int, str | None, int]] = []
        disrupted_this_tick: set[tuple[str, str]] = set()
        actions_this_tick: dict[tuple[str, str], int] = {}
        entrant_actions_this_tick: dict[str, int] = {}
        entrant_writes_this_tick: dict[str, int] = {}

        for decision_index, decision in tick_decisions:
            agent_id = decision.agent_id
            process_id = decision.process_id
            proc_key = (agent_id, process_id)
            obs = decision.observation
            reach = declared_reaches.get(proc_key, 128)

            # 1. Observation check
            current_anchor = anchors.get(proc_key)
            if current_anchor != obs.self_anchor:
                raise ExchangeConsistencyError(
                    f"Tick {current_tick} decision {decision_index}: {agent_id}/{process_id} "
                    f"observation self_anchor is {obs.self_anchor} but reconstructed anchor is {current_anchor}"
                )

            # In active sensing mode, passive visibility MUST be empty
            if obs.visible_enemy_anchor_addresses != ():
                raise ExchangeReconstructionError(
                    f"Tick {current_tick} decision {decision_index}: active sensing forbids passive enemy visibility, "
                    f"got {obs.visible_enemy_anchor_addresses}"
                )

            delivered_sample: tuple[int, ...] | None = None
            sample_pt: tuple[int, int] | None = None
            delivery_pt: tuple[int, int] | None = None

            if proc_key in pending_sensing:
                expected_sample, s_tick, s_idx = pending_sensing.pop(proc_key)
                if obs.previous_sense_anchors is ABSENT:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: expected sensing delivery "
                        f"{expected_sample} for {proc_key}, but previous_sense_anchors was ABSENT"
                    )
                if obs.previous_sense_anchors != expected_sample:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: delivered previous_sense_anchors "
                        f"{obs.previous_sense_anchors} does not match sampled anchors {expected_sample}"
                    )
                if not obs.previous_action_applied:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: previous_action_applied must be True "
                        f"for delivered sample {expected_sample}"
                    )
                delivered_sample = expected_sample
                sample_pt = (s_tick, s_idx)
                delivery_pt = (current_tick, decision_index)

            elif proc_key in pending_refusal:
                refusal_tick, refusal_idx = pending_refusal.pop(proc_key)
                if obs.previous_sense_anchors is not None:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: out-of-reach SENSE must reflect None, "
                        f"got {obs.previous_sense_anchors}"
                    )
                if obs.previous_action_applied:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: out-of-reach SENSE must reflect "
                        "previous_action_applied=False"
                    )
                delivered_sample = None
                sample_pt = (refusal_tick, refusal_idx)
                delivery_pt = (current_tick, decision_index)

            else:
                if obs.previous_sense_anchors is not ABSENT:
                    raise ExchangeReconstructionError(
                        f"Tick {current_tick} decision {decision_index}: unexpected previous_sense_anchors "
                        f"{obs.previous_sense_anchors} for {proc_key} when no delivery was pending"
                    )

            obs_state = SubTickWorldState(
                tick=current_tick,
                decision_index=decision_index,
                phase=ExchangePhase.OBSERVATION,
                anchors=dict(anchors),
                alive_entrants=frozenset(alive_entrants),
                disrupted_processes=frozenset(disrupted_processes),
                memory=bytes(memory),
                owners=tuple(owners),
            )
            sub_tick_states.append(obs_state)

            facts.append(
                SensingExchangeFact(
                    tick=current_tick,
                    decision_index=decision_index,
                    phase=ExchangePhase.OBSERVATION,
                    actor_id=agent_id,
                    process_id=process_id,
                    action_kind=None,
                    status=None,
                    normalized_address=None,
                    operand=None,
                    value=None,
                    cost=0,
                    sample_point=sample_pt,
                    delivery_point=delivery_pt,
                    audience=(agent_id,),
                    sensed_anchors=delivered_sample,
                    read_value=obs.previous_read_value,
                    read_owner=obs.previous_read_owner,
                    world_state=obs_state,
                    detail={
                        "visible_enemy_anchor_addresses": obs.visible_enemy_anchor_addresses,
                        "previous_action_applied": obs.previous_action_applied,
                    },
                )
            )

            # 2. Action check and application
            actions_this_tick[proc_key] = actions_this_tick.get(proc_key, 0) + 1
            entrant_actions_this_tick[agent_id] = entrant_actions_this_tick.get(agent_id, 0) + 1
            if entrant_actions_this_tick[agent_id] > action_budget:
                raise ExchangeReconstructionError(
                    f"Tick {current_tick}: action budget exceeded for entrant {agent_id}: "
                    f"{entrant_actions_this_tick[agent_id]} > {action_budget}"
                )

            action = decision.action
            applied_res = decision.applied_result

            action_sample_point: tuple[int, int] | None = None
            action_sensed_anchors: tuple[int, ...] | None = None

            if action is None:
                if applied_res is not None and applied_res.status in {"EXCEPTION", "REJECTED_INVALID"}:
                    alive_entrants.discard(agent_id)
            else:
                kind = action.kind
                op = action.operand

                if kind == "sense":
                    if not isinstance(op, int) or isinstance(op, bool):
                        raise ExchangeReconstructionError(
                            f"Tick {current_tick} decision {decision_index}: SENSE requires integer operand, got {op!r}"
                        )
                    norm_target = op % arena_size
                    assert current_anchor is not None
                    dist = circular_distance(current_anchor, norm_target, arena_size)

                    if dist <= reach:
                        if applied_res is None or applied_res.status != "APPLIED":
                            raise ExchangeReconstructionError(
                                f"Tick {current_tick} decision {decision_index}: in-reach SENSE must be APPLIED"
                            )

                        # Independent ground-truth enemy anchor evaluation at this exact instant
                        other_anchors = {
                            pos
                            for (ent, _), pos in anchors.items()
                            if ent != agent_id and ent in alive_entrants
                        }
                        independent_sensed = tuple(
                            sorted(
                                pos
                                for pos in other_anchors
                                if circular_distance(pos, norm_target, arena_size) <= window
                            )
                        )

                        if applied_res.sensed_anchors != independent_sensed:
                            raise ExchangeReconstructionError(
                                f"Tick {current_tick} decision {decision_index}: trace recorded sensed_anchors "
                                f"{applied_res.sensed_anchors} but independent reconstruction derived {independent_sensed}"
                            )

                        pending_sensing[proc_key] = (independent_sensed, current_tick, decision_index)
                        action_sample_point = (current_tick, decision_index)
                        action_sensed_anchors = independent_sensed

                    else:
                        # Out of reach
                        if applied_res is None or applied_res.status != "REJECTED_OUT_OF_REACH":
                            raise ExchangeReconstructionError(
                                f"Tick {current_tick} decision {decision_index}: out-of-reach SENSE must be "
                                f"REJECTED_OUT_OF_REACH, got {applied_res.status if applied_res else None}"
                            )
                        if applied_res.sensed_anchors is not None:
                            raise ExchangeReconstructionError(
                                f"Tick {current_tick} decision {decision_index}: rejected SENSE must record null sensed_anchors"
                            )
                        pending_refusal[proc_key] = (current_tick, decision_index)

                elif kind == "move":
                    if op is not None and (not isinstance(op, int) or isinstance(op, bool)):
                        raise ExchangeReconstructionError(
                            f"Tick {current_tick} decision {decision_index}: MOVE requires integer operand, got {op!r}"
                        )
                    if applied_res is not None and applied_res.status == "APPLIED":
                        delta = op if op is not None else 0
                        assert current_anchor is not None
                        new_pos = (current_anchor + delta) % arena_size
                        anchors[proc_key] = new_pos
                        if applied_res.normalized_address != new_pos:
                            raise ExchangeConsistencyError(
                                f"Tick {current_tick} decision {decision_index}: MOVE applied normalized_address "
                                f"{applied_res.normalized_address} does not match reconstructed anchor {new_pos}"
                            )

                elif kind == "write":
                    if op is not None and (not isinstance(op, int) or isinstance(op, bool)):
                        raise ExchangeReconstructionError(
                            f"Tick {current_tick} decision {decision_index}: WRITE requires integer operand, got {op!r}"
                        )
                    if action.value is not None and (not isinstance(action.value, int) or isinstance(action.value, bool)):
                        raise ExchangeReconstructionError(
                            f"Tick {current_tick} decision {decision_index}: WRITE requires integer value, got {action.value!r}"
                        )
                    if applied_res is not None and applied_res.status == "APPLIED":
                        target_addr = (op if op is not None else 0) % arena_size
                        val = (action.value if action.value is not None else 0) & 0xFF
                        memory[target_addr] = val
                        owners[target_addr] = agent_id
                        writes_this_tick.append((target_addr, agent_id, val))
                        entrant_writes_this_tick[agent_id] = entrant_writes_this_tick.get(agent_id, 0) + 1
                        cumulative_writes[agent_id] = cumulative_writes.get(agent_id, 0) + 1

                        # Shared location disruption
                        for (other_ent, other_proc), other_pos in list(anchors.items()):
                            if other_ent != agent_id and other_ent in alive_entrants and other_pos == target_addr:
                                disrupted_this_tick.add((other_ent, other_proc))

                elif kind == "read":
                    if op is not None and (not isinstance(op, int) or isinstance(op, bool)):
                        raise ExchangeReconstructionError(
                            f"Tick {current_tick} decision {decision_index}: READ requires integer operand, got {op!r}"
                        )

                if applied_res is not None and applied_res.status in {"EXCEPTION", "REJECTED_INVALID"}:
                    alive_entrants.discard(agent_id)

            act_state = SubTickWorldState(
                tick=current_tick,
                decision_index=decision_index,
                phase=ExchangePhase.ACTION,
                anchors=dict(anchors),
                alive_entrants=frozenset(alive_entrants),
                disrupted_processes=frozenset(disrupted_processes),
                memory=bytes(memory),
                owners=tuple(owners),
            )
            sub_tick_states.append(act_state)

            facts.append(
                SensingExchangeFact(
                    tick=current_tick,
                    decision_index=decision_index,
                    phase=ExchangePhase.ACTION,
                    actor_id=agent_id,
                    process_id=process_id,
                    action_kind=action.kind if action else None,
                    status=applied_res.status if applied_res else None,
                    normalized_address=applied_res.normalized_address if applied_res else None,
                    operand=action.operand if action else None,
                    value=action.value if action else None,
                    cost=1,
                    sample_point=action_sample_point,
                    delivery_point=None,
                    audience=(agent_id,) if action and action.kind != "sense" else (),
                    sensed_anchors=action_sensed_anchors,
                    world_state=act_state,
                )
            )

        # End-of-tick core capture, after every action of the tick: a live
        # entrant owning zero of its own core cells at capture_hold_ticks
        # consecutive evaluations is eliminated. Judged two-phase against the
        # same end-of-tick board, so the eliminated set is order-independent.
        captured: list[str] = []
        for entrant_id in sorted(alive_entrants):
            if any(owners[address] == entrant_id for address in core_cells[entrant_id]):
                core_zero_streak[entrant_id] = 0
                continue
            core_zero_streak[entrant_id] = core_zero_streak.get(entrant_id, 0) + 1
            if core_zero_streak[entrant_id] >= policy.capture_hold_ticks:
                captured.append(entrant_id)
        alive_entrants.difference_update(captured)

        # 3. Tick-end agreement check with canonical replay snapshot
        snapshot = ticks_by_number.get(current_tick)
        if snapshot is None:
            raise ExchangeConsistencyError(f"Replay missing snapshot for tick {current_tick}")

        replay_writes = [entry for diff in snapshot.memory_diffs for entry in _expand(diff, arena_size)]
        if replay_writes != writes_this_tick:
            raise ExchangeConsistencyError(
                f"Tick {current_tick}: trace applied writes ({len(writes_this_tick)}) "
                f"do not match replay memory diffs ({len(replay_writes)})"
            )

        for p in snapshot.processes:
            reconstructed_anchor = anchors.get((p.entrant_id, p.process_id))
            if reconstructed_anchor != p.anchor:
                raise ExchangeConsistencyError(
                    f"Tick {current_tick}: {p.entrant_id}/{p.process_id} reconstructed anchor "
                    f"{reconstructed_anchor} does not match replay anchor {p.anchor}"
                )

        replay_disrupted = {
            (p.entrant_id, p.process_id) for p in snapshot.processes if p.disrupted
        }
        if replay_disrupted != disrupted_this_tick:
            raise ExchangeConsistencyError(
                f"Tick {current_tick}: reconstructed disruption {sorted(disrupted_this_tick)} "
                f"does not match replay disruption {sorted(replay_disrupted)}"
            )

        # Reconcile entrant alive status, cpu_used, and mem_writes
        replay_alive = {a.agent_id for a in snapshot.agents if a.alive}
        if alive_entrants != replay_alive:
            raise ExchangeConsistencyError(
                f"Tick {current_tick}: reconstructed alive entrants {sorted(alive_entrants)} "
                f"do not match replay snapshot {sorted(replay_alive)}"
            )

        for a in snapshot.agents:
            expected_cpu = entrant_actions_this_tick.get(a.agent_id, 0)
            if a.cpu_used != expected_cpu:
                raise ExchangeConsistencyError(
                    f"Tick {current_tick}: entrant {a.agent_id} replay cpu_used {a.cpu_used} "
                    f"does not match trace actions count {expected_cpu}"
                )
            expected_writes = cumulative_writes.get(a.agent_id, 0)
            if a.mem_writes != expected_writes:
                raise ExchangeConsistencyError(
                    f"Tick {current_tick}: entrant {a.agent_id} replay mem_writes {a.mem_writes} "
                    f"does not match trace cumulative writes count {expected_writes}"
                )

        alive_entrants = set(replay_alive)
        disrupted_processes = set(replay_disrupted)

        end_state = SubTickWorldState(
            tick=current_tick,
            decision_index=None,
            phase=ExchangePhase.TICK_END,
            anchors=dict(anchors),
            alive_entrants=frozenset(alive_entrants),
            disrupted_processes=frozenset(disrupted_processes),
            memory=bytes(memory),
            owners=tuple(owners),
        )
        sub_tick_states.append(end_state)

        facts.append(
            SensingExchangeFact(
                tick=current_tick,
                decision_index=None,
                phase=ExchangePhase.TICK_END,
                actor_id=None,
                process_id=None,
                action_kind=None,
                status=None,
                normalized_address=None,
                operand=None,
                value=None,
                cost=0,
                sample_point=None,
                delivery_point=None,
                audience=(),
                world_state=end_state,
            )
        )

    # Cross-check demo.json metadata if provided
    if demo_artifacts_info is not None:
        demo_payload = demo_artifacts_info["payload"]
        if demo_payload.get("match_id") != binding.match_id:
            raise ArtifactIntegrityError(
                f"demo.json match_id {demo_payload.get('match_id')!r} contradicts replay {binding.match_id!r}"
            )
        if demo_payload.get("ruleset_id") != binding.ruleset_id:
            raise ArtifactIntegrityError(
                f"demo.json ruleset_id {demo_payload.get('ruleset_id')!r} contradicts replay {binding.ruleset_id!r}"
            )
        if (
            loaded.header.result_id
            and demo_payload.get("result_id")
            and demo_payload.get("result_id") != loaded.header.result_id
        ):
            raise ArtifactIntegrityError(
                f"demo.json result_id {demo_payload.get('result_id')!r} contradicts replay header {loaded.header.result_id!r}"
            )
        demo_cfg = demo_payload.get("config", {})
        if "arena_size" in demo_cfg and demo_cfg["arena_size"] != loaded.header.config.arena_size:
            raise ArtifactIntegrityError(
                f"demo.json arena_size {demo_cfg['arena_size']} contradicts replay {loaded.header.config.arena_size}"
            )
        if "action_budget" in demo_cfg and demo_cfg["action_budget"] != loaded.header.config.instr_per_tick:
            raise ArtifactIntegrityError(
                f"demo.json action_budget {demo_cfg['action_budget']} contradicts replay {loaded.header.config.instr_per_tick}"
            )
        if "seed" in demo_cfg and demo_cfg["seed"] != loaded.header.config.seed:
            raise ArtifactIntegrityError(
                f"demo.json seed {demo_cfg['seed']} contradicts replay {loaded.header.config.seed}"
            )
        demo_entrants = tuple(
            e.get("agent_id") for e in demo_payload.get("entrants", []) if isinstance(e, dict)
        )
        if demo_entrants and demo_entrants != binding.entrant_identities:
            raise ArtifactIntegrityError(
                f"demo.json entrants {demo_entrants} contradict binding entrants {binding.entrant_identities}"
            )

    # Entrant names come from the digest-bound replay header; demo.json names
    # may only agree with it, never select the evaluated entrant.
    replay_names = {e.get("agent_id"): e.get("name") for e in loaded.header.entrants}
    if demo_artifacts_info is not None:
        for e in demo_artifacts_info["payload"].get("entrants", []):
            if (
                isinstance(e, dict)
                and "name" in e
                and e.get("agent_id") in replay_names
                and e["name"] != replay_names[e.get("agent_id")]
            ):
                raise ArtifactIntegrityError(
                    f"demo.json entrant {e.get('agent_id')!r} name {e['name']!r} contradicts "
                    f"replay header name {replay_names[e.get('agent_id')]!r}"
                )

    scout_entrant_id = next(
        (str(agent_id) for agent_id, name in replay_names.items() if name == "v6_window_scout"),
        "A",
    )
    scout_name = replay_names.get(scout_entrant_id)

    teaching_verif = evaluate_teaching_exchange(
        facts,
        arena_size=arena_size,
        scout_id=scout_entrant_id,
        scout_name=scout_name if isinstance(scout_name, str) else None,
    )

    # Reconcile teaching assertions in demo.json
    if demo_artifacts_info is not None:
        demo_payload = demo_artifacts_info["payload"]
        teaching_block = demo_payload.get("teaching_exchange", {})
        if isinstance(teaching_block, dict) and "sequence_verified" in teaching_block:
            claimed_verified = teaching_block.get("sequence_verified")
            if claimed_verified is True and not teaching_verif.is_verified:
                raise ExchangeReconstructionError(
                    "demo.json claims sequence_verified=True, but independent reconstruction failed"
                )
        if demo_payload.get("status") == "reproducible" and not teaching_verif.is_verified:
            raise ExchangeReconstructionError(
                "demo.json claims status='reproducible', but independent reconstruction failed"
            )

    return SensingPlayback(
        match_id=binding.match_id,
        ruleset_id=binding.ruleset_id,
        arena_size=arena_size,
        facts=tuple(facts),
        sub_tick_states=tuple(sub_tick_states),
        teaching_verification=teaching_verif,
        binding=binding,
        demo_artifacts=demo_artifacts_info,
    )


def verify_demonstration(demo_dir_or_file: Path | str) -> SensingPlayback:
    """End-to-end verification of an active sensing demonstration.

    Validates metadata/provenance, artifact digests, pairwise consistency,
    quota/costs, and independent reconstruction of the sensing exchange.
    Raises SensingPlaybackError if any integrity or gameplay verification fails.
    """
    artifacts_info = verify_demonstration_artifacts(demo_dir_or_file)
    paths = artifacts_info["paths"]
    demo_path = artifacts_info["demo_path"]

    playback = reconstruct_sensing_playback(
        replay_path=paths["replay"],
        trace_path=paths["trace"],
        result_path=paths.get("result"),
        demo_path=demo_path,
    )

    if playback.teaching_verification is None or not playback.teaching_verification.is_verified:
        details = ", ".join(playback.teaching_verification.findings) if playback.teaching_verification else "No findings"
        raise ExchangeReconstructionError(f"Demonstration verification failed: {details}")

    return playback


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for independent demonstration and artifact playback verification."""
    parser = argparse.ArgumentParser(
        description="Bytefray V6 M1-3: Sensing playback and artifact verification."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Path to demo.json or demonstration directory to verify.",
    )
    parser.add_argument("--replay", help="Path to replay.jsonl.")
    parser.add_argument("--trace", help="Path to trace.jsonl.")
    parser.add_argument("--result", help="Path to result.json.")

    args = parser.parse_args(argv)

    try:
        if args.target:
            playback = verify_demonstration(args.target)
            print("Demonstration verified: True")
            print(f"Match ID:   {playback.match_id}")
            print(f"Ruleset ID: {playback.ruleset_id}")
            if playback.teaching_verification:
                for step in playback.teaching_verification.steps:
                    print(f"  [Step {step.step_index}] {step.status.value}: {step.description}")
            return 0

        elif args.replay and args.trace:
            playback = reconstruct_sensing_playback(
                replay_path=args.replay,
                trace_path=args.trace,
                result_path=args.result,
            )
            # Pair mode checks artifact integrity and replay/trace consistency
            # only; it must not read as a teaching-exchange verification.
            print("Artifact pair integrity and consistency verified: True")
            print(f"Match ID:   {playback.match_id}")
            print(f"Ruleset ID: {playback.ruleset_id}")
            print(f"Total facts: {len(playback.facts)}")
            print(
                "Teaching exchange: NOT CLAIMED (pair mode does not verify the complete "
                "teaching exchange; verify a demonstration directory or demo.json for that)"
            )
            return 0

        else:
            parser.print_help(sys.stderr)
            return 2

    except SensingPlaybackError as exc:
        print(f"Verification FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Verification ERROR: {exc}", file=sys.stderr)
        return 1


__all__ = [
    "DEMO_PROVENANCE",
    "DEMO_SCHEMA",
    "DEMO_SCHEMA_VERSION",
    "EXPECTED_RULESET_ID",
    "EXPECTED_SENSING_WINDOW",
    "PLAYBACK_SCHEMA",
    "PLAYBACK_SCHEMA_VERSION",
    "ArtifactIntegrityError",
    "ExchangeConsistencyError",
    "ExchangePhase",
    "ExchangeReconstructionError",
    "SensingExchangeFact",
    "SensingPlayback",
    "SensingPlaybackError",
    "SubTickWorldState",
    "TeachingExchangeVerification",
    "VerificationStatus",
    "VerifiedExchangeStep",
    "evaluate_teaching_exchange",
    "main",
    "reconstruct_sensing_playback",
    "verify_demonstration",
]


if __name__ == "__main__":
    sys.exit(main())
