"""Read-only identities and byte recipes for the committed E9 protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
FREEZE = ROOT / "tools/research/v6/e9/protocol_freeze.json"
PROTOCOL_DIGEST = "563980801bf0466fd8ee58a952a114711735aace0981eb5be70890538d8bb3e8"
PROTOCOL_ID = "v6-e9-prereg-v1-563980801bf0"


class IntegrityError(ValueError):
    """Required evidence or a frozen identity does not hold."""


class ExecutionLocked(IntegrityError):
    """The separate experimental execution boundary has not been authorized."""


def canonical(value: Any) -> bytes:
    def encode(item: Any) -> Any:
        if isinstance(item, Fraction):
            return f"{item.numerator}/{item.denominator}"
        if isinstance(item, (set, frozenset)):
            return sorted(item)
        raise TypeError(f"unsupported canonical type: {type(item).__name__}")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False, default=encode).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path, *, lf: bool = False) -> str:
    data = path.read_bytes()
    return digest(data.replace(b"\r\n", b"\n") if lf else data)


def read_json(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise IntegrityError("duplicate JSON key")
            out[key] = value
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, ValueError) as exc:
        raise IntegrityError("unreadable or invalid required JSON evidence") from exc
    if not isinstance(data, dict):
        raise IntegrityError("required record is not an object")
    return data


def write_once(path: Path, value: Any) -> str:
    """Exclusive, durable publication; existing evidence is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value) + b"\n"
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return digest(data)


def load_protocol(*, verify: bool = True) -> dict[str, Any]:
    record = read_json(FREEZE)
    body = record.get("body", {})
    if (record.get("schema") != "bytefray.v6.e9.protocol_freeze"
            or record.get("status") != "FROZEN" or record.get("version") != 1
            or record.get("identity") != PROTOCOL_ID
            or record.get("digest") != PROTOCOL_DIGEST or digest(canonical(body)) != PROTOCOL_DIGEST):
        raise IntegrityError("the committed E9 protocol freeze does not recompute")
    if verify:
        snapshots = [body["protocol"], body["acceptance"]["evidence"],
                     body["acceptance"]["supplied_proposal"]]
        for entry in snapshots:
            if file_digest(ROOT / entry["path"]) != entry["sha256_raw"]:
                raise IntegrityError("a frozen protocol/acceptance snapshot changed")
        for path, hashes in body["governing_files"].items():
            if file_digest(ROOT / path, lf=True) != hashes["sha256_lf"]:
                raise IntegrityError("a governing contract changed")
        for path, sha in body["qualified_e9_raw"].items():
            if file_digest(ROOT / path) != sha:
                raise IntegrityError("a qualified E9 source changed")
        for path, sha in body["frozen_e8_lf"].items():
            if file_digest(ROOT / path, lf=True) != sha:
                raise IntegrityError("a frozen E8 source changed")
        for name in body["historical_packages"]:
            verify_package(name, ROOT / "tools/research/v6/e8/fixtures/agents" / name, body)
        if file_digest(ROOT / "tools/research/v6/e8/final_registered_result.json") != body["sealed_e8_result_sha256_raw"]:
            raise IntegrityError("the sealed E8 result changed")
        paths = sorted(subprocess.check_output(["git", "ls-files", "engine/src"],
                                               cwd=ROOT, text=True).split())
        manifest = "".join(f"{file_digest(ROOT / p, lf=True)}  {p}\n" for p in paths)
        if (len(paths) != body["engine_source"]["files"] or digest(manifest.encode())
                != body["engine_source"]["sha256_lf_manifest"]):
            raise IntegrityError("the frozen engine manifest changed")
    return body


@dataclass(frozen=True, order=True)
class Cell:
    row: str
    opponent: str
    position: int
    seat: str

    def validate(self, protocol: dict[str, Any]) -> None:
        if (self.row not in protocol["physical_rows"]
                or self.opponent not in protocol["historical_members"]
                or type(self.position) is not int or not 1 <= self.position <= 1412
                or self.seat not in ("A", "B")):
            raise IntegrityError("cell is outside the registered physical rectangle")

    @property
    def identity(self) -> str:
        return "v6-e9-cell-v1-" + digest(canonical([PROTOCOL_ID, self.row, self.opponent,
                                                  self.position, self.seat]))

    def packages(self, protocol: dict[str, Any]) -> tuple[str, str]:
        self.validate(protocol)
        focal = protocol["physical_packages"][self.row]
        member = protocol["historical_members"][self.opponent]
        opponent = member["twin" if self.row == self.opponent else "primary"]
        return (focal, opponent) if self.seat == "A" else (opponent, focal)


def cells(protocol: dict[str, Any]) -> Iterator[Cell]:
    for position in range(1, 1413):
        for row in protocol["physical_rows"]:
            for opponent in protocol["historical_members"]:
                for seat in ("A", "B"):
                    yield Cell(row, opponent, position, seat)


def configuration(row: str, protocol: dict[str, Any]) -> str:
    if row == "A":
        return "Variant()"
    if row in ("MEDIUM", "SPARSE"):
        return f'Variant(kind="fixed", mode=Mode.{row})'
    schedule = next((s for s in protocol["schedules"] if s["id"] == row), None)
    if schedule is None:
        raise IntegrityError("not a prospective E9 wrapper")
    return (f'Variant(kind="schedule", schedule=Schedule(Mode.{schedule["initial"]}, '
            f'{tuple(schedule["edges"])!r}, "{schedule["clock"]}"))')


def package_bytes(row: str, protocol: dict[str, Any]) -> dict[str, bytes]:
    name = protocol["physical_packages"][row]
    config = configuration(row, protocol)
    manifest = (f'name: {name}\nkind: python\napi_version: 2\n'
                'entrypoint: "agent.py:create_agent"\nversion: "1.0.0"\n')
    source = ('from tools.research.v6.e9.policy import Agent, Variant\n'
              'from tools.research.v6.e9.selectors import Mode, Schedule\n\n'
              f'def create_agent():\n    return Agent({config})\n')
    result = {"agent.yaml": manifest.replace("\n", "\r\n").encode(),
              "agent.py": source.replace("\n", "\r\n").encode()}
    if {key: digest(value) for key, value in result.items()} != protocol["prospective_packages"][name]:
        raise IntegrityError("prospective wrapper bytes disagree with the freeze")
    return result


def verify_package(name: str, path: Path, protocol: dict[str, Any]) -> None:
    expected = protocol["prospective_packages"].get(name)
    if expected is None:
        historic = protocol["historical_packages"].get(name)
        if historic is None:
            raise IntegrityError("unregistered package")
        expected = {"agent.py": historic["agent_py_sha256"],
                    "agent.yaml": historic["agent_yaml_sha256"]}
    if any(file_digest(path / filename) != sha for filename, sha in expected.items()):
        raise IntegrityError("evaluation package bytes changed")
