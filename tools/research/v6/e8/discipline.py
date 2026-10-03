"""E8-D clause D8-9: the static discipline and containment gate (phase I8-3).

docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md (PR8) Sec 3.3,
5.1 (D8-9) and 13, and the implementation plan Sec 5.7. It is E6's D-5 gate
(``tools/research/v6/e6/discipline.py``, reused unchanged: allowed imports
only, no ``seed`` attribute, none of the forbidden builtins), with E8's own
package-ID pattern, and one added check:

**every path that returns SENSE is guarded by ``sensing_window is not None``.**

Syntactically, a *SENSE reference* is the attribute ``SENSE`` (as in
``ActionKindV2.SENSE``) or the string constant ``"sense"`` (the action's wire
value). Each must lie in the body -- never the ``else`` branch -- of an ``if``
whose test is ``<x>.sensing_window is not None`` or ``sensing_window is not
None``, alone or as one operand of an ``and``. A guard means something only if
the guarded name holds the context's value, so a name or attribute called
``sensing_window`` may be bound only from another ``sensing_window``
attribute (``self.sensing_window = context.sensing_window``).

The same analysis gives the static class of PR8 Sec 3.3 and 13 that the
pre-match compatibility gate (``compatibility.py``) reads:

* ``none``: no SENSE reference at all;
* ``context-gated``: SENSE references, every one guarded, and no ungrounded
  binding of ``sensing_window``;
* ``ungated``: anything else that references SENSE.

Like E6's, the check is deliberately syntactic: it characterizes this frozen
family, and is not a sandbox. CQ8-1 checks the controls dynamically.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from pathlib import Path

from tools.research.v6.e6 import discipline as e6_discipline
from tools.research.v6.e6.discipline import Violation

#: Every E8 family package ID has this shape (``e8_q01`` .. ``e8_q22``).
PACKAGE_ID_PATTERN = re.compile(r"e8_q\d{2}")
SENSE_ATTRIBUTE = "SENSE"
SENSE_WIRE_VALUE = "sense"
GUARD_NAME = "sensing_window"

NONE, CONTEXT_GATED, UNGATED = "none", "context-gated", "ungated"
CLASSES: tuple[str, ...] = (NONE, CONTEXT_GATED, UNGATED)

__all__ = [
    "CLASSES",
    "CONTEXT_GATED",
    "NONE",
    "PACKAGE_ID_PATTERN",
    "UNGATED",
    "Violation",
    "check_packages",
    "classify",
    "classify_package",
    "passes",
    "sense_violations",
    "violations",
]


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def _is_sense_reference(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute) and node.attr == SENSE_ATTRIBUTE:
        return True
    return isinstance(node, ast.Constant) and node.value == SENSE_WIRE_VALUE


def _names_guard(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == GUARD_NAME) or (
        isinstance(node, ast.Name) and node.id == GUARD_NAME
    )


def _is_guard_test(test: ast.AST) -> bool:
    """``<x>.sensing_window is not None``, alone or as one operand of an ``and``."""

    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        return any(_is_guard_test(value) for value in test.values)
    return (
        isinstance(test, ast.Compare)
        and _names_guard(test.left)
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.IsNot)
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    )


def _guarded(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """Whether ``node`` lies in the body of an ``if`` whose test is the guard."""

    child, parent = node, parents.get(node)
    while parent is not None:
        if (isinstance(parent, ast.If) and any(child is statement for statement in parent.body)
                and _is_guard_test(parent.test)):
            return True
        child, parent = parent, parents.get(parent)
    return False


def _grounded_binding(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """Whether a store to ``sensing_window`` copies another ``sensing_window``, or ``None``.

    Only a plain ``x.sensing_window = <y>.sensing_window`` (or ``= None``,
    which can only disable sensing) is grounded; unpacking, augmented
    assignment, loop targets and every other value are not. An annotation
    with no value binds nothing.
    """

    statement = parents.get(node)
    if isinstance(statement, ast.AnnAssign) and statement.target is node:
        value = statement.value
        if value is None:
            return True
    elif isinstance(statement, ast.Assign) and any(target is node for target in statement.targets):
        value = statement.value
    else:
        return False
    return _names_guard(value) or (isinstance(value, ast.Constant) and value.value is None)


def sense_violations(source: str) -> list[Violation]:
    """The added D8-9 rule: unguarded SENSE references and ungrounded ``sensing_window`` bindings."""

    tree = ast.parse(source)
    parents = _parents(tree)
    found: list[Violation] = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if _is_sense_reference(node) and not _guarded(node, parents):
            found.append(Violation(line, "sense-guard", "SENSE outside a sensing_window guard"))
        if (
            _names_guard(node)
            and isinstance(getattr(node, "ctx", None), ast.Store | ast.Del)
            and not _grounded_binding(node, parents)
        ):
            found.append(Violation(line, "sense-guard", "sensing_window bound from something else"))
    return found


def _references_sense(source: str) -> bool:
    return any(_is_sense_reference(node) for node in ast.walk(ast.parse(source)))


def violations(source: str) -> list[Violation]:
    """Every D8-9 violation in one member's source, in line order."""

    found = list(e6_discipline.violations(source))
    for number, line in enumerate(source.splitlines(), start=1):
        for match in PACKAGE_ID_PATTERN.finditer(line):
            found.append(Violation(number, "package-id", match.group(0)))
    found += sense_violations(source)
    return sorted(found, key=lambda violation: (violation.line, violation.rule, violation.detail))


def classify(source: str) -> str:
    """The static class of PR8 Sec 3.3 and 13: ``none``, ``context-gated`` or ``ungated``."""

    if not _references_sense(source):
        return NONE
    return UNGATED if sense_violations(source) else CONTEXT_GATED


def classify_package(package_dir: Path) -> str:
    return classify((package_dir / "agent.py").read_text(encoding="utf-8"))


def check_packages(package_dirs: Iterable[Path]) -> dict[str, list[Violation]]:
    """D8-9 over every package: its name mapped to its violations (empty = passes)."""

    return {
        package.name: violations((package / "agent.py").read_text(encoding="utf-8"))
        for package in sorted(package_dirs)
    }


def passes(package_dirs: Iterable[Path]) -> bool:
    return not any(check_packages(package_dirs).values())
