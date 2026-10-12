"""Shared helpers for the V6 E8 engine tests (phase I8-2).

Two things live here:

* **A scripted-match harness.** Explicit ``ProcessEntrantSpec`` entrants whose
  processes run scripted executors at explicit positions, traced to a schema-2
  trace file. None is an E8 family member, and no test built on it asserts an
  outcome (PR8 Sec 10's delivery tests; SYN6 Sec H, item 4).
* **An independent presence oracle.** :func:`presence_problems` re-states
  PR8 Sec 10's presence rules (Revisions 4 and 5) over the raw JSON of a trace,
  written from the registered text alone and sharing no code with the engine's
  writer. The engine's traces must pass it, and a planted stray or missing
  field must fail it. It is a qualification oracle for I8-2's serialization,
  not the E8 analysis gates, which belong to I8-5.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from battle_engine.agent_api import ActionKindV2, AgentAction, ObservationV2
from battle_engine.agent_trace import TRACE_SCHEMA_VERSION_V2, TraceHeader, TraceWriter
from battle_engine.config import Config
from battle_engine.process_runtime import (
    ProcessEntrantSpec,
    ProcessInstance,
    ProcessMatchController,
    ProcessRole,
)
from battle_engine.ruleset_policy import (
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27,
    RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32,
    RULESET_V6_RESEARCH_SENSING_ACTIVE_W27,
    RULESET_V6_RESEARCH_SENSING_R32,
    RulesetPolicy,
)

ARENA = 512
QUOTA = 8
WINDOW = 27
#: T8 and T8L, and their parents C8 and C8L.
TREATMENTS = (RULESET_V6_RESEARCH_SENSING_ACTIVE_W27, RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_ACTIVE_W27)
CONTROLS = (RULESET_V6_RESEARCH_SENSING_R32, RULESET_V6_RESEARCH_DISRUPTION_SLOT1_SENSING_R32)
PARENT = dict(zip(TREATMENTS, CONTROLS, strict=True))

Step = AgentAction | Callable[[ObservationV2], AgentAction]


def ids(policy: RulesetPolicy) -> str:
    return policy.ruleset_id


def sense(target: int) -> AgentAction:
    return AgentAction(ActionKindV2.SENSE, target)


def read(address: int) -> AgentAction:
    return AgentAction(ActionKindV2.READ, address)


def write(address: int, value: int = 0xEE) -> AgentAction:
    return AgentAction(ActionKindV2.WRITE, address, value)


@dataclass
class Scripted:
    """One process's executor: ``steps[n]`` is its action at its ``n``-th callback (1-based).

    An unscripted callback READs the process's own anchor, which is always in
    reach and changes nothing. Every callback is logged, in match order, to the
    shared ``log`` as ``(name, tick, n)``.
    """

    name: str
    log: list[tuple[str, int, int]]
    steps: Mapping[int, Step] = field(default_factory=dict)
    calls: int = 0
    observations: list[ObservationV2] = field(default_factory=list)

    def __call__(self, obs: ObservationV2, _slot: int) -> AgentAction:
        self.calls += 1
        self.observations.append(obs)
        self.log.append((self.name, obs.current_tick, self.calls))
        step = self.steps.get(self.calls)
        if step is None:
            return read(obs.self_anchor)
        return step(obs) if callable(step) else step


def process(pid: str, position: int, reach: int, share: int, executor: Scripted) -> ProcessInstance:
    return ProcessInstance(pid, ProcessRole.GENERALIST, initial_position=position, reach=reach, quota_share=share,
                           logic=lambda _obs, _state: read(position), executor=executor)


@dataclass
class TracedRun:
    controller: ProcessMatchController
    result: dict[str, Any]
    records: list[dict[str, Any]]
    lines: list[str]

    def decisions(self, agent_id: str | None = None, process_id: str | None = None) -> list[dict[str, Any]]:
        return [r for r in self.records if r["record_type"] == "decision_v2"
                and (agent_id is None or r["agent_id"] == agent_id)
                and (process_id is None or r["process_id"] == process_id)]


def run_traced(tmp_path: Path, policy: RulesetPolicy, entrants: Sequence[tuple[str, int, list[ProcessInstance]]], *,
               ticks: int = 1, arena: int = ARENA, prepare: Callable[[ProcessMatchController], None] | None = None,
               name: str = "trace.jsonl") -> TracedRun:
    """Run one explicit-spec match with a schema-2 trace, and return its raw records."""

    specs = [ProcessEntrantSpec(agent_id=seat, name=f"seat-{seat}", processes=processes, start=start)
             for seat, start, processes in entrants]
    path = tmp_path / name
    writer = TraceWriter(path)
    writer.write_header(TraceHeader(match_seed=1, agents={seat: seat for seat, _, _ in entrants}, supervised=False,
                                    schema_version=TRACE_SCHEMA_VERSION_V2))
    controller = ProcessMatchController(Config(seed=1, arena_size=arena, instr_per_tick=QUOTA), specs, ticks,
                                        ruleset_policy=policy, trace_writer=writer)
    if prepare is not None:
        prepare(controller)
    try:
        result = controller.run()
    finally:
        writer.close()
    lines = path.read_text(encoding="utf-8").splitlines()
    return TracedRun(controller, result, [json.loads(line) for line in lines], lines)


def trace_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# The independent presence oracle (PR8 Sec 10, Revisions 4 and 5)
# ---------------------------------------------------------------------------

ORDINARY_STATUSES = ("APPLIED", "REJECTED_OUT_OF_REACH")


def presence_problems(records: Iterable[Mapping[str, Any]], *, active: bool, window: int = WINDOW) -> list[str]:
    """Every place a trace breaks PR8 Sec 10's presence rules, checked both ways.

    * ``ResetRecord.sensing_window``: exactly ``window`` under ``"active"``; absent,
      not ``null``, under ``"passive"`` (D8-15).
    * ``applied_result.sensed_anchors``: on every record whose action is SENSE and
      on no other; a list (ascending, distinct integers) if ``APPLIED`` and
      ``null`` if ``REJECTED_OUT_OF_REACH``. A SENSE record with any other status
      is outside D8-14's universe and reported too (D8-1).
    * ``observation.previous_sense_anchors``: on exactly the callback that owes a
      reflection -- the same process's next callback after a SENSE record --
      equal to that record's ``sensed_anchors``, and on no other (D8-13).
    """

    problems: list[str] = []
    previous: dict[tuple[str, str], Mapping[str, Any]] = {}
    for index, record in enumerate(records):
        kind = record.get("record_type")
        if kind == "reset":
            if active and record.get("sensing_window", "<absent>") != window:
                problems.append(f"{index}: treatment reset sensing_window {record.get('sensing_window', '<absent>')!r}")
            if not active and "sensing_window" in record:
                problems.append(f"{index}: control reset carries sensing_window {record['sensing_window']!r}")
        if kind != "decision_v2":
            continue
        key = (record["agent_id"], record["process_id"])
        action = record.get("action") or {}
        result = record.get("applied_result") or {}
        is_sense = action.get("kind") == "sense"
        if is_sense and not active:
            problems.append(f"{index}: a SENSE record under a passive Ruleset")
        if is_sense:
            if "sensed_anchors" not in result:
                problems.append(f"{index}: SENSE record without sensed_anchors")
            else:
                value, status = result["sensed_anchors"], result.get("status")
                if status == "APPLIED":
                    if not isinstance(value, list) or value != sorted(set(value)):
                        problems.append(f"{index}: applied SENSE sensed_anchors {value!r} is not an ascending list")
                elif status == "REJECTED_OUT_OF_REACH":
                    if value is not None:
                        problems.append(f"{index}: refused SENSE sensed_anchors {value!r} is not null")
                else:
                    problems.append(f"{index}: SENSE record with status {status!r}, outside D8-14's universe")
        elif "sensed_anchors" in result:
            problems.append(f"{index}: stray sensed_anchors on a {action.get('kind')!r} record")
        prior = previous.get(key)
        owed = prior is not None and (prior.get("action") or {}).get("kind") == "sense"
        observation = record["observation"]
        if owed:
            expected = (prior.get("applied_result") or {}).get("sensed_anchors", "<absent>")
            if "previous_sense_anchors" not in observation:
                problems.append(f"{index}: owed reflection missing")
            elif observation["previous_sense_anchors"] != expected:
                problems.append(f"{index}: reflection {observation['previous_sense_anchors']!r} != {expected!r}")
        elif "previous_sense_anchors" in observation:
            problems.append(f"{index}: stray previous_sense_anchors {observation['previous_sense_anchors']!r}")
        previous[key] = record
    return problems


def status_problems(records: Iterable[Mapping[str, Any]]) -> list[str]:
    """D8-14's status universe: every ``decision_v2`` status is ``APPLIED`` or ``REJECTED_OUT_OF_REACH``."""

    return [f"{index}: status {(record.get('applied_result') or {}).get('status', '<missing>')!r}"
            for index, record in enumerate(records) if record.get("record_type") == "decision_v2"
            and (record.get("applied_result") or {}).get("status") not in ORDINARY_STATUSES]


E8_KEYS = ("sensing_window", "sensed_anchors", "previous_sense_anchors")


def e8_keys_in(lines: Iterable[str]) -> list[str]:
    """Every E8 trace key present anywhere in the raw lines of a trace."""

    found: list[str] = []
    for number, line in enumerate(lines, start=1):
        payload = json.loads(line)
        for part in (payload, payload.get("observation") or {}, payload.get("applied_result") or {}):
            found += [f"{number}:{key}" for key in E8_KEYS if key in part]
    return found
