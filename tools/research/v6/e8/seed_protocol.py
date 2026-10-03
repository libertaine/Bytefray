"""E8 seed-set blindness tooling (PR8 Sec 9; implementation plan Sec 7, phase I8-5).

The plan's module table calls this ``seeds.py``. It is named
``seed_protocol.py`` because the frozen I8-0, I8-1 and I8-4 tests check that
no seed list exists by asserting that no ``seeds*`` file is in this package.
That check stays literally true: the private list lives under ``runs/``.

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 9
adopts PR6 Sec 9 unchanged, with E8's names. This is E6's seed tooling
(``tools/research/v6/e6/seeds.py``) ported to E8, plus the value-based seed
filter of step 6. Nothing here runs at import, and **no E8 seed exists until
phase I8-6, which is separately authorized.** I8-5 exercises every function
below on synthetic lists only.

1. The family and the structural matrix identity are frozen first (I8-4).
2. ``generate`` draws 32 unique integers with ``secrets.randbelow(2**53)``,
   exactly once. Its ``randbelow`` parameter exists so that tests can drive
   the mechanics with a deterministic synthetic source; the runner never
   passes one.
3. ``encode`` is the canonical form: decimal ASCII (``str(int)``, no sign, no
   leading zeros), one per line, LF line endings with a trailing LF, UTF-8, in
   generation order, which is the matrix order.
4. ``commitment`` is the SHA-256 hex of those bytes, and
   ``execution_identity`` is ``v6-e8-exec-v1-<first 12 hex of SHA-256(
   structural digest hex, LF, commitment hex, LF)>``.
5. Only the commitment and the execution identity are committed before the
   first matrix cell. The list stays in ``PRIVATE_SEEDS_PATH``, which is
   git-ignored (``runs/``) and outside every agent package. ``write_private``
   never overwrites.
6. ``SeedGuard`` is the value-based filter every printed or saved output
   passes before the reveal: artifact paths embed seeds, so it redacts each
   seed's decimal text wherever it occurs, not by key name.
7. At reveal, ``d8_10`` verifies the committed list: the commitment, the
   execution identity, and that every matrix cell's seed is on it.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from tools.research.v6.e8 import preregistration

SEED_COUNT = 32
SEED_BOUND = 2**53
EXECUTION_IDENTITY_PREFIX = "v6-e8-exec-v1-"
PRIVATE_SEEDS_PATH = preregistration.REPOSITORY_ROOT / "runs" / "research_v6_e8" / "seeds.private.txt"
REDACTED = "<seed>"


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


def generate(count: int = SEED_COUNT, *, randbelow: Callable[[int], int] = secrets.randbelow) -> list[int]:
    """``count`` unique seeds from ``randbelow(2**53)``, in generation order (a repeat is redrawn)."""
    seeds: list[int] = []
    while len(seeds) < count:
        seed = randbelow(SEED_BOUND)
        if seed not in seeds:
            seeds.append(seed)
    _check(seeds, count=count)
    return seeds


def encode(seeds: Sequence[int], *, count: int = SEED_COUNT) -> bytes:
    _check(seeds, count=count)
    return "".join(f"{seed}\n" for seed in seeds).encode("ascii")


def decode(data: bytes, *, count: int = SEED_COUNT) -> list[int]:
    """Parse the canonical form strictly: anything else is rejected, never repaired."""
    if not data.endswith(b"\n") or b"\r" in data:
        raise SeedProtocolError("not canonical: LF line endings and a trailing LF are required")
    seeds = []
    for line in data[:-1].split(b"\n"):
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


def _hex64(name: str, value: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise SeedProtocolError(f"{name} is not a lowercase SHA-256 hex digest: {value!r}")


def execution_identity(structural_digest: str, seed_commitment: str) -> str:
    """PR8 Sec 9, step 4: the execution identity binds the structure to the committed list."""
    _hex64("structural digest", structural_digest)
    _hex64("seed commitment", seed_commitment)
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


def committed_record(seed_commitment: str, structural_digest: str, generated_at: str,
                     tool_commit: str) -> Mapping[str, str]:
    """The only facts about the seeds a record may carry before the reveal (PR8 Sec 9, step 5)."""
    return {
        "seed_commitment": seed_commitment,
        "execution_matrix_identity": execution_identity(structural_digest, seed_commitment),
        "generated_at_utc": generated_at,
        "tool_commit": tool_commit,
    }


def d8_10(revealed: bytes, *, committed: str, structural_digest: str, committed_execution_identity: str,
          cell_seeds: Iterable[int]) -> dict[str, Any]:
    """D8-10 at the reveal: the commitment, the execution identity, and every cell's seed on the list."""
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
    off_list = sorted(set(cell_seeds) - set(seeds))
    checks["cell_seeds_on_list"] = bool(seeds) and not off_list
    return {"clause": "D8-10", "checks": checks, "off_list_seeds": off_list[:10],
            "status": "PASS" if all(checks.values()) else "FAIL"}


class SeedGuard:
    """PR8 Sec 9, step 6: redact every seed's decimal text from an output, by value.

    A seed is redacted wherever its digits occur, inside a path or a longer
    token included: over-redaction is harmless, a leak is not. Longer seeds
    are replaced first so that no seed's text survives inside another's.
    """

    def __init__(self, seeds: Iterable[int]) -> None:
        texts = sorted({str(int(seed)) for seed in seeds}, key=lambda text: (-len(text), text))
        if not texts:
            raise SeedProtocolError("a seed guard needs the seed list")
        self._pattern = re.compile("|".join(re.escape(text) for text in texts))

    def redact(self, text: str) -> str:
        return self._pattern.sub(REDACTED, text)

    def clean(self, text: str) -> bool:
        return self._pattern.search(text) is None

    def require_clean(self, text: str) -> str:
        if not self.clean(text):
            raise SeedProtocolError("an output carries a seed value before the reveal")
        return text
