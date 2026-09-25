"""E6-D clause D-5: the static family-discipline gate.

docs/research/v6/V6_E6_PRICED_SENSING_PREREGISTRATION.md Sec 5.1 (D-5) and
docs/research/v6/V6_E6_PRICED_SENSING_IMPLEMENTATION_PLAN.md Sec 5.5; the
design reason is V6_PRICED_SENSING_DESIGN_REVIEW.md Sec E.2 and condition
C-2. A family member may learn where its opponent is only by playing: it
must not import placement or seed-derivation code, read its context's raw
``seed`` (``context.rng`` is its only randomness), open files, execute code
it builds, or carry a family package ID.

The check is an AST walk over each package's ``agent.py`` plus a raw-text
scan for package IDs (comments are not in the AST). It is deliberately
syntactic: it characterizes this frozen family, and is not a sandbox.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

#: The one engine module a member may import.
AGENT_API_MODULE = "battle_engine.agent_api"
#: The standard-library whitelist (plan Sec 5.5). A submodule of a listed
#: package (``collections.abc``) is part of that package.
STDLIB_WHITELIST = frozenset(
    {"__future__", "dataclasses", "typing", "enum", "math", "collections", "itertools", "functools"}
)
#: Names a member may never reference, called or not.
FORBIDDEN_NAMES = frozenset(
    {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "breakpoint", "input"}
)
#: Attributes a member may never read or write, on any object.
FORBIDDEN_ATTRIBUTES = frozenset({"seed"})
#: Every family package ID has this shape (``e6_q01`` .. ``e6_q18``).
PACKAGE_ID_PATTERN = re.compile(r"e6_q\d{2}")


@dataclass(frozen=True)
class Violation:
    line: int
    rule: str
    detail: str


def _import_allowed(module: str) -> bool:
    if module == AGENT_API_MODULE:
        return True
    return module.split(".", 1)[0] in STDLIB_WHITELIST


def violations(source: str) -> list[Violation]:
    """Every D-5 violation in one member's source, in line order."""

    found: list[Violation] = []
    for number, line in enumerate(source.splitlines(), start=1):
        for match in PACKAGE_ID_PATTERN.finditer(line):
            found.append(Violation(number, "package-id", match.group(0)))
    tree = ast.parse(source)
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _import_allowed(alias.name):
                    found.append(Violation(line, "import", alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level != 0 or not _import_allowed(module):
                found.append(Violation(line, "import", "." * node.level + module))
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRIBUTES:
            found.append(Violation(line, "attribute", node.attr))
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            found.append(Violation(line, "name", node.id))
    return sorted(found, key=lambda violation: (violation.line, violation.rule, violation.detail))


def check_packages(package_dirs: Iterable[Path]) -> dict[str, list[Violation]]:
    """D-5 over every package: its name mapped to its violations (empty = passes)."""

    return {
        package.name: violations((package / "agent.py").read_text(encoding="utf-8"))
        for package in sorted(package_dirs)
    }


def passes(package_dirs: Iterable[Path]) -> bool:
    return not any(check_packages(package_dirs).values())
