"""Authoritative incremental VM/arena ownership-count invariants.

V6 Phase 2B.12 (docs/research/v6/V6_PHASE2B12_SCOPE_C_RUNTIME_RETIREMENT.md)
removed ``VM.load_code`` (VM code placement) and ``python_runtime.
apply_action``/``PythonEntrantState`` (Agent API v1 execution) alongside
VM/blob and Agent API v1 execution. The subject this file actually tests --
``VM._wr8``'s ownership-count bookkeeping, the shared arena primitive
``process_runtime.ProcessMatchController`` (the retained control's runtime)
still uses -- is unaffected and stays covered directly through ``_wr8``.
"""

from __future__ import annotations

from collections import Counter

from battle_engine.vm import VM


def _recomputed(vm: VM) -> dict[str, int]:
    return dict(Counter(owner for owner in vm.writer if owner is not None))


def _assert_consistent(vm: VM) -> None:
    assert vm.ownership_counts == _recomputed(vm)
    assert sum(vm.ownership_counts.values()) == sum(owner is not None for owner in vm.writer)


def test_wrapped_writes_overwrites_same_owner_and_unowned_transitions():
    vm = VM(4)
    assert vm.ownership_counts == {}

    vm._wr8(4, 1, "A")
    _assert_consistent(vm)
    assert vm.ownership_counts == {"A": 1}

    vm._wr8(0, 2, "A")
    _assert_consistent(vm)
    assert vm.ownership_counts == {"A": 1}

    vm._wr8(-4, 3, "B")
    _assert_consistent(vm)
    assert vm.ownership_counts == {"B": 1}

    vm._wr8(0, 4, None)
    _assert_consistent(vm)
    assert vm.ownership_counts == {}


def test_every_mutation_in_sequence_matches_full_recomputation():
    vm = VM(17)
    operations = [
        (-1, "A"),
        (0, "A"),
        (17, "B"),
        (34, "B"),
        (5, "C"),
        (5, "C"),
        (16, None),
        (22, "A"),
        (-12, "B"),
    ]
    for value, (address, owner) in enumerate(operations):
        vm._wr8(address, value, owner)
        _assert_consistent(vm)
