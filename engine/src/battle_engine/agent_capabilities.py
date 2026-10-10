"""Versioned manifest capability metadata; preflight never executes agent code."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from battle_engine.agent_api import AgentManifestError, AgentValidationError

KNOWN_CAPABILITIES = frozenset({"sense"})


class AgentCapabilityMismatchError(AgentValidationError):
    code = "agent_capability_unsupported"


def parse_required_capabilities(
    manifest: Mapping[str, Any], *, path: Path | None = None
) -> frozenset[str]:
    """Absent metadata is compatible; present metadata must be exactly v1."""
    if not isinstance(manifest, Mapping):
        raise AgentManifestError("Agent manifest must be an object.", path=path)
    if "capabilities" not in manifest:
        return frozenset()
    block = manifest["capabilities"]
    if not isinstance(block, Mapping) or set(block) != {"version", "required"}:
        raise AgentManifestError(
            "'capabilities' must be an object with version and required fields.", path=path
        )
    version = block["version"]
    if type(version) is not int or version != 1:
        raise AgentManifestError("Capability metadata version must be integer 1.", path=path)
    required = block["required"]
    if not isinstance(required, list) or any(
        not isinstance(name, str) or name not in KNOWN_CAPABILITIES for name in required
    ):
        raise AgentManifestError(
            "Capability required must be a list of known names: sense.", path=path
        )
    if len(set(required)) != len(required):
        raise AgentManifestError("Capability required must contain unique names.", path=path)
    return frozenset(required)


def preflight_agent_capabilities(
    agent: object, *, available: Iterable[str], ruleset_id: str
) -> None:
    """Check the authoritative manifest, including manually constructed specs."""
    manifest = agent if isinstance(agent, Mapping) else getattr(agent, "manifest", {})
    path = getattr(agent, "dir", None)
    if not isinstance(manifest, Mapping):
        raise AgentManifestError("Agent manifest must be an object.", path=path)
    missing = parse_required_capabilities(manifest, path=path) - frozenset(available)
    if missing:
        raise AgentCapabilityMismatchError(
            f"Ruleset {ruleset_id!r} does not provide required capabilities: "
            f"{', '.join(sorted(missing))}. Select an explicitly compatible Ruleset.",
            path=path,
        )
