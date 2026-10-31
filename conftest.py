"""Repository-wide pytest hooks: the product / frozen-science test boundary.

Product qualification (``python -m pytest``, ci.yml) verifies the current
implementation against its current contracts. A small, explicitly listed
inventory of frozen V6/E9 science tests asserts that today's tree still has
the byte identities of a historical research snapshot; those cases are
verified against that snapshot instead, by
.github/workflows/frozen-science.yml. The exact inventory, with a reason for
every entry, is ``product_ci_transfer`` in
tools/qualification/frozen_science_e9.json -- nothing is matched by name
pattern. Transferred cases are reported as deselected, never skipped or
passed, and ``--include-frozen-science`` restores them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_POLICY = Path(__file__).resolve().parent / "tools" / "qualification" / "frozen_science_e9.json"
_TRANSFERRED = pytest.StashKey[int]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--include-frozen-science",
        action="store_true",
        default=False,
        help="also run the frozen-science cases transferred to the historical workflow",
    )


def transferred_inventory() -> tuple[frozenset[str], frozenset[str]]:
    """Exact transferred module paths and exact node IDs (parameters included or not)."""

    transfer = json.loads(_POLICY.read_text(encoding="utf-8"))["product_ci_transfer"]
    modules = frozenset(entry["path"] for entry in transfer["modules"])
    cases = frozenset(entry["node_id"] for entry in transfer["cases"])
    return modules, cases


def is_transferred(node_id: str, modules: frozenset[str], cases: frozenset[str]) -> bool:
    """A collected node is transferred only by an exact module path or exact node ID.

    A case entry without parameters (``path::test``) covers every
    parametrization of that one test function; nothing else is implied.
    """

    module = node_id.split("::", 1)[0]
    return module in modules or node_id in cases or node_id.split("[", 1)[0] in cases


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--include-frozen-science"):
        return
    modules, cases = transferred_inventory()
    keep: list[pytest.Item] = []
    moved: list[pytest.Item] = []
    for item in items:
        (moved if is_transferred(item.nodeid, modules, cases) else keep).append(item)
    if moved:
        config.hook.pytest_deselected(items=moved)
        items[:] = keep
    config.stash[_TRANSFERRED] = len(moved)


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter, config: pytest.Config) -> None:
    moved = config.stash.get(_TRANSFERRED, 0)
    if moved:
        terminalreporter.write_line(
            f"frozen science: {moved} case(s) deselected from product qualification and verified at the "
            "historical snapshot by .github/workflows/frozen-science.yml "
            "(tools/qualification/frozen_science_e9.json)"
        )
