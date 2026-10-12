"""E6 seed-set blindness tooling (pre-registration Sec 9; implementation plan Sec 8).

Nothing here runs at import, and no seed exists until phase I-7, which is
separately authorized. The protocol:

1. The family and the structural matrix identity are frozen first.
2. ``generate`` draws 32 unique integers with ``secrets.randbelow(2**53)``.
3. ``encode`` is the canonical form: decimal ASCII (``str(int)``, no sign,
   no leading zeros), one per line, LF line endings and a trailing LF, in
   generation order, which is the matrix order.
4. ``commitment`` is the SHA-256 hex of those bytes, and
   ``execution_identity`` is ``v6-e6-exec-v1-<first 12 hex of SHA-256
   (structural digest hex + LF + commitment hex + LF)>``.
5. Only the commitment and the execution identity are committed, before the
   first matrix cell. The list itself stays in ``PRIVATE_SEEDS_PATH``, which
   is git-ignored and outside every agent package.
6. At reveal, ``d6`` verifies the committed list: the commitment, the
   execution identity, and that every matrix cell's seed is on it.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.research.v6.experiment_harness import REPO_ROOT

SEED_COUNT = 32
SEED_BOUND = 2**53
EXECUTION_IDENTITY_PREFIX = "v6-e6-exec-v1-"
PRIVATE_SEEDS_PATH = REPO_ROOT / "runs" / "research_v6_e6" / "seeds.private.txt"


class SeedProtocolError(ValueError):
    """A seed list, encoding or commitment breaks the registered protocol."""


def _check(seeds: Sequence[int], *, count: int = SEED_COUNT) -> None:
    if len(seeds) != count:
        raise SeedProtocolError(f"{len(seeds)} seeds, {count} required")
    for seed in seeds:
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < SEED_BOUND:
            raise SeedProtocolError(f"seed {seed!r} is not an integer in [0, 2**53)")
    if len(set(seeds)) != len(seeds):
        raise SeedProtocolError("duplicate seed")


def generate(count: int = SEED_COUNT) -> list[int]:
    """``count`` unique seeds from ``secrets.randbelow(2**53)``, in generation order."""
    seeds: list[int] = []
    while len(seeds) < count:
        seed = secrets.randbelow(SEED_BOUND)
        if seed not in seeds:
            seeds.append(seed)
    return seeds


def encode(seeds: Sequence[int], *, count: int = SEED_COUNT) -> bytes:
    _check(seeds, count=count)
    return "".join(f"{seed}\n" for seed in seeds).encode("ascii")


def decode(data: bytes, *, count: int = SEED_COUNT) -> list[int]:
    """Parse the canonical form strictly: anything else is rejected, never repaired."""
    if not data.endswith(b"\n") or b"\r" in data:
        raise SeedProtocolError("not canonical: LF line endings and a trailing LF are required")
    lines = data[:-1].split(b"\n")
    seeds = []
    for line in lines:
        if not line.isdigit() or (len(line) > 1 and line.startswith(b"0")):
            raise SeedProtocolError(f"not a canonical decimal seed: {line!r}")
        seeds.append(int(line))
    if encode(seeds, count=count) != data:
        raise SeedProtocolError("not canonical")
    return seeds


def commitment(seeds: Sequence[int], *, count: int = SEED_COUNT) -> str:
    return hashlib.sha256(encode(seeds, count=count)).hexdigest()


def verify(seeds: Sequence[int], committed: str, *, count: int = SEED_COUNT) -> bool:
    return commitment(seeds, count=count) == committed


def execution_identity(structural_digest: str, seed_commitment: str) -> str:
    for name, value in (("structural digest", structural_digest), ("seed commitment", seed_commitment)):
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            raise SeedProtocolError(f"{name} is not a lowercase SHA-256 hex digest: {value!r}")
    payload = f"{structural_digest}\n{seed_commitment}\n".encode()
    return EXECUTION_IDENTITY_PREFIX + hashlib.sha256(payload).hexdigest()[:12]


def write_private(seeds: Sequence[int], path: Path = PRIVATE_SEEDS_PATH) -> str:
    """Store the list privately (never overwriting) and return its commitment."""
    data = encode(seeds)
    if path.exists():
        raise SeedProtocolError(f"{path} already exists; a seed list is generated once")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def load_private(committed: str, path: Path = PRIVATE_SEEDS_PATH) -> list[int]:
    """The private list, refused unless it matches the committed value."""
    seeds = decode(path.read_bytes())
    if not verify(seeds, committed):
        raise SeedProtocolError("the private seed list does not match the committed seed commitment")
    return seeds


def d6(revealed: bytes, *, committed: str, structural_digest: str, committed_execution_identity: str,
       cell_seeds: Iterable[int]) -> dict[str, Any]:
    """E6-D clause D-6 at reveal: commitment, execution identity, and every cell's seed on the list."""
    checks: dict[str, bool] = {}
    try:
        seeds = decode(revealed)
    except SeedProtocolError:
        seeds = []
        checks["canonical"] = False
    else:
        checks["canonical"] = True
    checks["commitment"] = bool(seeds) and verify(seeds, committed)
    checks["execution_identity"] = execution_identity(structural_digest, committed) == committed_execution_identity
    off_list = sorted({seed for seed in cell_seeds} - set(seeds))
    checks["cell_seeds_on_list"] = bool(seeds) and not off_list
    return {"clause": "D-6", "checks": checks, "off_list_seeds": off_list[:10],
            "status": "PASS" if all(checks.values()) else "FAIL"}


def committed_record(seed_commitment: str, structural_digest: str, generated_at: str,
                     tool_commit: str) -> Mapping[str, str]:
    """The only facts about the seeds the freeze record may carry before reveal (PR Sec 9, step 5)."""
    return {
        "seed_commitment": seed_commitment,
        "execution_matrix_identity": execution_identity(structural_digest, seed_commitment),
        "generated_at_utc": generated_at,
        "tool_commit": tool_commit,
    }
