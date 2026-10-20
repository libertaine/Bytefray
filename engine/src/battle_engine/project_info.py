"""Package-safe project metadata shared by user interfaces."""

from __future__ import annotations

import platform
import re
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

from battle_engine.agent_api import AGENT_API_VERSION
from battle_engine.replay import SCHEMA_VERSION as REPLAY_SCHEMA_VERSION
from battle_engine.result_model import SCHEMA_VERSION as RESULT_SCHEMA_VERSION

PROJECT_NAME = "Bytefray"
PROJECT_URL = "https://github.com/libertaine/Bytefray"
LICENSE_NAME = "MIT"

_PEP440_RELEASE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?$")
_SEMVER_STAGES = {"a": "alpha", "b": "beta", "rc": "rc"}


def public_version(package_version: str) -> str:
    """Return the public SemVer spelling of a PEP 440 release version.

    ``5.1.0a1`` -> ``5.1.0-alpha.1`` (docs/COMPONENT_VERSIONING.md §4.1). A
    final release is spelled the same both ways, and anything else (a dev
    build, a local version, "development checkout") is returned unchanged.
    Display only: ``result.json`` keeps recording the PEP 440 form.
    """

    match = _PEP440_RELEASE.match(package_version)
    if match is None:
        return package_version
    major, minor, patch, stage, number = match.groups()
    suffix = "" if stage is None else f"-{_SEMVER_STAGES[stage]}.{number}"
    return f"{major}.{minor}.{patch}{suffix}"


@dataclass(frozen=True)
class ProjectInfo:
    version: str
    agent_api_version: int
    result_schema_version: int
    replay_schema_version: int
    python_version: str
    project_name: str = PROJECT_NAME
    project_url: str = PROJECT_URL
    license_name: str = LICENSE_NAME

    @property
    def display_version(self) -> str:
        """The public version, plus the package spelling when they differ."""

        public = public_version(self.version)
        return public if public == self.version else f"{public} (package {self.version})"


def get_project_info() -> ProjectInfo:
    try:
        package_version = version("bytefray")
    except PackageNotFoundError:
        package_version = "development checkout"
    return ProjectInfo(
        version=package_version,
        agent_api_version=AGENT_API_VERSION,
        result_schema_version=RESULT_SCHEMA_VERSION,
        replay_schema_version=REPLAY_SCHEMA_VERSION,
        python_version=platform.python_version(),
    )
