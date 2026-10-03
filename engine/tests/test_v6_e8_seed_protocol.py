"""V6 E8: the seed-set blindness tooling (PR8 Sec 9, D8-10; phase I8-5).

**Synthetic lists only.** No real E8 seed list is generated, committed or
written anywhere but a temporary directory: ``generate`` is driven by a
deterministic stand-in for ``secrets.randbelow``. The real list is generated
exactly once, at the separately authorized phase I8-6.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path

import pytest

from tools.research.v6.e8 import matrix, seed_protocol

SYNTHETIC = [(7919 * k * k + 104729 * k + 13) % seed_protocol.SEED_BOUND for k in range(1, 33)]


def _source(values: list[int]):  # type: ignore[no-untyped-def]
    stream = iter(values)
    return lambda bound: next(stream) % bound


def test_the_registered_protocol_constants() -> None:
    protocol = matrix.structural_definition()["seed_protocol"]
    assert (seed_protocol.SEED_COUNT, seed_protocol.SEED_BOUND) == (32, 2**53)
    assert protocol["generator"] == "secrets.randbelow(2**53)"
    assert protocol["execution_identity"].startswith(seed_protocol.EXECUTION_IDENTITY_PREFIX)
    assert seed_protocol.EXECUTION_IDENTITY_PREFIX == "v6-e8-exec-v1-"
    # The private list lives under runs/, which git ignores, outside every agent package.
    assert seed_protocol.PRIVATE_SEEDS_PATH.parts[-3:] == ("runs", "research_v6_e8", "seeds.private.txt")


def test_generate_draws_unique_values_in_generation_order_and_redraws_a_repeat() -> None:
    values = [5, 9, 5, *range(100, 129), 7]  # one repeat, which is redrawn
    drawn = seed_protocol.generate(randbelow=_source(values))
    assert drawn == [5, 9, *range(100, 129), 7]
    assert len(set(drawn)) == 32


def test_generate_uses_secrets_by_default_without_running_it() -> None:
    import inspect

    assert inspect.signature(seed_protocol.generate).parameters["randbelow"].default is seed_protocol.secrets.randbelow


def test_the_canonical_encoding_and_its_commitment() -> None:
    data = seed_protocol.encode(SYNTHETIC)
    assert data == "".join(f"{s}\n" for s in SYNTHETIC).encode("ascii")
    assert seed_protocol.commitment(SYNTHETIC) == hashlib.sha256(data).hexdigest()
    assert seed_protocol.decode(data) == SYNTHETIC
    assert seed_protocol.verify(SYNTHETIC, seed_protocol.commitment(SYNTHETIC))


@pytest.mark.parametrize("data", [
    b"1\r\n" * 32,                                   # CRLF
    "".join(f"{s}\n" for s in SYNTHETIC).encode()[:-1],  # no trailing LF
    b"01\n" + "".join(f"{s}\n" for s in SYNTHETIC[1:]).encode(),  # a leading zero
    b"+5\n" + "".join(f"{s}\n" for s in SYNTHETIC[1:]).encode(),  # a sign
    "".join(f"{s}\n" for s in SYNTHETIC[:31]).encode(),   # 31 seeds
])
def test_decoding_refuses_anything_not_canonical(data: bytes) -> None:
    with pytest.raises(seed_protocol.SeedProtocolError):
        seed_protocol.decode(data)


@pytest.mark.parametrize("bad", [SYNTHETIC[:31], [*SYNTHETIC[:31], SYNTHETIC[0]], [*SYNTHETIC[:31], -1],
                                 [*SYNTHETIC[:31], 2**53], [*SYNTHETIC[:31], True]])
def test_encoding_refuses_a_list_off_the_protocol(bad: list[int]) -> None:
    with pytest.raises(seed_protocol.SeedProtocolError):
        seed_protocol.encode(bad)


def test_the_execution_identity_binds_the_structure_to_the_commitment() -> None:
    commitment = seed_protocol.commitment(SYNTHETIC)
    expected = hashlib.sha256(f"{matrix.STRUCTURAL_DIGEST}\n{commitment}\n".encode()).hexdigest()[:12]
    assert seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, commitment) == "v6-e8-exec-v1-" + expected
    assert seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, "d" * 64) != seed_protocol.execution_identity(
        matrix.STRUCTURAL_DIGEST, commitment)
    for bad in ("D" * 64, "d" * 63, "z" * 64):
        with pytest.raises(seed_protocol.SeedProtocolError):
            seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, bad)


def test_the_private_list_is_written_once_and_loaded_only_against_its_commitment(tmp_path: Path) -> None:
    path = tmp_path / "seeds.private.txt"
    commitment = seed_protocol.write_private(SYNTHETIC, path)
    assert commitment == seed_protocol.commitment(SYNTHETIC)
    with pytest.raises(seed_protocol.SeedProtocolError, match="generated once"):
        seed_protocol.write_private(SYNTHETIC, path)
    assert seed_protocol.load_private(commitment, path) == SYNTHETIC
    with pytest.raises(seed_protocol.SeedProtocolError, match="does not match"):
        seed_protocol.load_private("e" * 64, path)
    path.write_bytes(path.read_bytes().replace(str(SYNTHETIC[0]).encode(), str(SYNTHETIC[0] + 1).encode(), 1))
    with pytest.raises(seed_protocol.SeedProtocolError):
        seed_protocol.load_private(commitment, path)


def test_the_committed_record_carries_only_the_permitted_facts() -> None:
    commitment = seed_protocol.commitment(SYNTHETIC)
    record = seed_protocol.committed_record(commitment, matrix.STRUCTURAL_DIGEST, "2026-10-01T00:00:00Z", "0" * 40)
    assert set(record) == {"seed_commitment", "execution_matrix_identity", "generated_at_utc", "tool_commit"}
    assert not any(str(seed) in "".join(record.values()) for seed in SYNTHETIC)


def test_d8_10_passes_only_for_the_committed_list_identity_and_cell_seeds() -> None:
    commitment = seed_protocol.commitment(SYNTHETIC)
    identity = seed_protocol.execution_identity(matrix.STRUCTURAL_DIGEST, commitment)
    data = seed_protocol.encode(SYNTHETIC)

    def check(revealed: bytes, cells: list[int], committed_identity: str = identity) -> dict:  # type: ignore[type-arg]
        return seed_protocol.d8_10(revealed, committed=commitment, structural_digest=matrix.STRUCTURAL_DIGEST,
                           committed_execution_identity=committed_identity, cell_seeds=cells)

    assert check(data, SYNTHETIC * 3)["status"] == "PASS"
    other = list(SYNTHETIC)
    other[0] += 1
    assert check(seed_protocol.encode(other), SYNTHETIC)["checks"]["commitment"] is False
    assert check(data, [*SYNTHETIC, 5])["checks"]["cell_seeds_on_list"] is False
    assert check(data, SYNTHETIC, "v6-e8-exec-v1-000000000000")["checks"]["execution_identity"] is False
    assert check(data[:-1], SYNTHETIC)["checks"]["canonical"] is False
    for report in (check(seed_protocol.encode(other), SYNTHETIC), check(data[:-1], SYNTHETIC)):
        assert report["status"] == "FAIL"


def test_the_seed_guard_redacts_every_seed_by_value_wherever_it_appears() -> None:
    guard = seed_protocol.SeedGuard(SYNTHETIC)
    path = f"runs/x/matches/0001-candidate-a-vs-b-seed{SYNTHETIC[3]}-seeded-{SYNTHETIC[3]}-candidate_first"
    redacted = guard.redact(f'{{"artifact_dir": "{path}", "seed": {SYNTHETIC[7]}}}')
    assert guard.clean(redacted)
    assert str(SYNTHETIC[3]) not in redacted and str(SYNTHETIC[7]) not in redacted
    assert redacted.count(seed_protocol.REDACTED) == 3
    assert not guard.clean(str(SYNTHETIC[0]))
    with pytest.raises(seed_protocol.SeedProtocolError):
        guard.require_clean(f"leak {SYNTHETIC[31]}")
    assert guard.require_clean("nothing here") == "nothing here"


def test_the_seed_guard_leaves_no_seed_inside_a_longer_one() -> None:
    long_seed, short_seed = 123456789012345, 12345  # the short one's digits sit inside the long one
    guard = seed_protocol.SeedGuard([long_seed, short_seed])
    assert guard.redact(f"{long_seed} {short_seed}") == f"{seed_protocol.REDACTED} {seed_protocol.REDACTED}"
    with pytest.raises(seed_protocol.SeedProtocolError):
        seed_protocol.SeedGuard([])


def test_a_synthetic_round_trip_never_touches_the_private_path(tmp_path: Path) -> None:
    rng = random.Random(3)
    drawn = seed_protocol.generate(randbelow=lambda bound: rng.randrange(bound))
    path = tmp_path / "seeds.private.txt"
    assert seed_protocol.load_private(seed_protocol.write_private(drawn, path), path) == drawn
    assert path.parent == tmp_path
