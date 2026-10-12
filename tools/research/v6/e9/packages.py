"""Scratch qualification packages; never an experimental roster or matrix."""

from pathlib import Path


def package(root: Path, name: str, configuration: str) -> Path:
    """Write an explicit qualification fixture in a caller-owned scratch directory."""
    path = root / name
    path.mkdir(parents=True, exist_ok=False)
    (path / "agent.yaml").write_text(
        f'name: {name}\nkind: python\napi_version: 2\nentrypoint: "agent.py:create_agent"\nversion: "1.0.0"\n',
        encoding="utf-8")
    (path / "agent.py").write_text(
        'from tools.research.v6.e9.policy import Agent, Variant\n'
        'from tools.research.v6.e9.selectors import Mode, Schedule\n\n'
        f'def create_agent():\n    return Agent({configuration})\n', encoding="utf-8")
    return path
