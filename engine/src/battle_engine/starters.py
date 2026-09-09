"""Install and refresh bundled starter agents in the writable agent catalog."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from battle_engine.paths import get_data_root, get_resource_root

# The first four are native VM starters (manifest-only; resolved against
# the built-in VM programs in battle_engine.builtins by name -- see
# cli.py's SUPPORTED fallback). The remaining seven are Agent API v1 Python
# starters, each shipping its own agent.py implementing a distinct strategy
# against the restricted Python Agent API rather than native VM bytecode --
# see each agent.py's module docstring for its strategy and the reasoning
# behind it. ensure_starter_agents() treats both kinds identically: install
# when absent, refresh when provably an untouched older bundled copy, and
# otherwise preserve, into the same writable agents/ catalog.
#
# Five of the Python starters (claimer, strider, hunter, wanderer,
# adaptive, added in v0.6.1) are expansion-family strategies and are also
# pinned members of the frozen v2 benchmark population -- their source is
# content-addressed in battle_engine/data/benchmarks/v2_baseline.json and
# must never be edited (see docs/V3_PHASE0_RESEARCH_BASELINE.md Sec 3).
# raider and sentinel (added in v3.0.0-alpha2) are deliberately NOT
# benchmark members: they exist to demonstrate the Ruleset-v2 vulnerable-
# core mechanic itself -- attacking a core and defending one -- which no
# expansion starter exercises, and they stay freely maintainable precisely
# because they carry no benchmark identity.
#
# The four v5_* starters (added in v5.0.0a1, V5 Alpha 1 Phase C -- see
# docs/research/v5/V5_ALPHA1_PHASE_C_STARTER_AGENTS.md) are the Agent API
# v2 educational ladder: regional offense, search-and-strike movement,
# READ-driven core defense, and a two-process team. They are ADDITIVE. The
# six v4_* entries above them keep their historical behavior byte for byte
# -- replays, evaluation records and the Phase 0/R3/R4 research corpora all
# refer to those IDs, so a v5_* redesign gets a new ID rather than silently
# replacing an old one.
STARTER_AGENT_NAMES = (
    "runner",
    "writer",
    "seeker",
    "spiral",
    "claimer",
    "strider",
    "hunter",
    "wanderer",
    "adaptive",
    "raider",
    "sentinel",
    "v4_claimer",
    "v4_concentrated_attacker",
    "v4_defender_scout",
    "v4_local_defender",
    "v4_scout",
    "v4_quorum",
    "v5_region_attacker",
    "v5_scout_striker",
    "v5_core_defender",
    "v5_dual_team",
)


def _starter_resource_dir(resource_root: Path) -> Path:
    candidates = (
        resource_root / "battle_engine" / "data" / "starter_agents",
        resource_root / "engine" / "src" / "battle_engine" / "data" / "starter_agents",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    checked = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Starter-agent resource directory not found. Checked: {checked}")


def _validate_starter(source_dir: Path, name: str) -> list[Path]:
    agent_dir = source_dir / name
    manifest = agent_dir / "agent.yaml"
    if not manifest.is_file():
        raise FileNotFoundError(f"Starter agent '{name}' is missing manifest: {manifest}")
    try:
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Starter agent '{name}' has malformed manifest {manifest}: {exc}") from exc
    if not isinstance(metadata, dict) or metadata.get("name") != name:
        raise ValueError(
            f"Starter agent '{name}' manifest must be an object with name={name!r}: {manifest}"
        )
    files = starter_content_files(agent_dir)
    if not files:
        raise ValueError(f"Starter agent '{name}' contains no resource files: {agent_dir}")
    return files


def starter_agent_resource_dir(
    name: str, *, resource_root: Path | None = None
) -> Path:
    """Return one validated bundled starter directory without installing it."""

    resources = (resource_root or get_resource_root()).expanduser().resolve()
    source_dir = _starter_resource_dir(resources)
    if name not in STARTER_AGENT_NAMES:
        raise KeyError(f"Unknown bundled starter agent: {name}")
    _validate_starter(source_dir, name)
    return (source_dir / name).resolve()


# ---------------------------------------------------------------------------
# Bundled-content identity (V5 Alpha 1 Phase E)
# ---------------------------------------------------------------------------

#: Bumped only if the digest algorithm below changes shape. Recorded in every
#: digest so a stored fingerprint can never be silently compared against one
#: produced by different rules -- the same discipline
#: ``agent_api.LOCAL_SOURCE_FINGERPRINT_VERSION`` already applies.
STARTER_CONTENT_DIGEST_VERSION = 1

# Suffixes whose content is normalized to LF before hashing. A starter agent
# package is text by construction (``_validate_starter`` requires a parseable
# ``agent.yaml``; every implementation ships ``.py`` source), and this
# repository checks out ``.py`` with CRLF on Windows (``core.autocrlf=true``)
# while storing and shipping LF -- so the *same* bundled release genuinely has
# different bytes on different platforms. Without normalization a Windows
# install could never be recognized as a pristine copy of the release it came
# from. Anything not listed here is hashed byte for byte.
_TEXT_SUFFIXES = frozenset(
    {".py", ".yaml", ".yml", ".json", ".md", ".txt", ".cfg", ".ini", ".toml"}
)


def starter_content_files(agent_dir: Path) -> list[Path]:
    """Every file that makes up one starter, deterministically ordered.

    ``__pycache__`` is excluded at both ends of the lifecycle: importing a
    bundled starter in a source checkout writes bytecode *into the resource
    tree*, and ``pyproject.toml``'s ``exclude-package-data`` already keeps it
    out of the wheel and sdist. Enumerating it here would make the same
    release's content depend on whether an agent happened to have run before
    the copy -- and would install stale bytecode into a user's catalog.

    A symlinked entry resolving outside ``agent_dir`` is skipped rather than
    followed, matching ``agent_api.local_source_fingerprint``'s containment
    rule.
    """

    if not agent_dir.is_dir():
        return []
    base = agent_dir.resolve()
    files: list[Path] = []
    for candidate in base.rglob("*"):
        if "__pycache__" in candidate.parts:
            continue
        try:
            resolved = candidate.resolve()
            resolved.relative_to(base)
        except (OSError, ValueError):
            continue
        if resolved.is_file():
            files.append(candidate)
    return sorted(files, key=lambda path: path.relative_to(base).as_posix())


def _normalized_content(path: Path) -> bytes:
    content = path.read_bytes()
    if path.suffix.lower() in _TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return content


def starter_content_digest(agent_dir: Path) -> str | None:
    """A platform-stable fingerprint of one starter directory's whole content.

    Covers every file the starter ships -- ``agent.yaml`` included, which is
    the point: Phase D changed manifests, not just implementations. Returns
    ``None`` for a directory that is absent or holds no content files, which
    callers read as "nothing installed here yet" rather than as an empty
    starter.

    Line endings are normalized for text files (see ``_TEXT_SUFFIXES``), so
    two checkouts of one release agree. Two files differing *only* in line
    endings are deliberately equal here: whoever converted them changed no
    agent behavior, so treating that as a user modification would block an
    upgrade for no benefit.
    """

    base = agent_dir.resolve() if agent_dir.is_dir() else agent_dir
    entries = starter_content_files(agent_dir)
    if not entries:
        return None
    hasher = hashlib.sha256()
    hasher.update(str(STARTER_CONTENT_DIGEST_VERSION).encode("ascii"))
    for path in entries:
        hasher.update(b"\0")
        hasher.update(path.relative_to(base).as_posix().encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(hashlib.sha256(_normalized_content(path)).digest())
    return hasher.hexdigest()


#: Content digests of bundled starter releases this repository has *superseded*.
#:
#: This is an allowlist for automatic upgrades, and absence is the safe answer.
#: An installed starter whose digest appears here is provably an untouched copy
#: of a specific past bundled release, so replacing it with current bundled
#: content destroys no user work. An installed starter whose digest appears
#: *neither* here nor in the current bundled tree is treated as user-modified
#: and is never overwritten -- which is why the historical ``v4_*`` and v0.6.1
#: starters need no entries at all: their content has not changed, so they take
#: the "already current" path, and any local edit to one is preserved.
#:
#: Maintenance rule, enforced by
#: ``test_v5_alpha1_phase_e_starter_refresh.py::
#: test_current_bundled_content_matches_its_pinned_digest``: when a bundled
#: starter's content changes, append the digest it had *before* the change to
#: that starter's tuple here. Forgetting to is not dangerous -- it only means
#: existing installs keep the older copy -- but the pinned-digest test fails
#: first and says so.
SUPERSEDED_STARTER_DIGESTS: Mapping[str, tuple[str, ...]] = {
    # The four Agent API v2 educational starters shipped at version 1.0.0 in
    # V5 Alpha 1 Phase C with no ``parameters`` section, and at 1.1.0 in Phase
    # D with one. An installation created between those two phases holds a
    # pristine 1.0.0 copy that the Agent Designer would otherwise show no
    # parameter controls for, forever -- the exact upgrade problem Phase E
    # exists to fix.
    "v5_region_attacker": (
        # 1.0.0 -- V5 Alpha 1 Phase C (69fc958)
        "f09d7fd5720e86b1a0f0c61de042a449bfba09e60065d92d894a24f8a44b6b00",
    ),
    "v5_scout_striker": (
        # 1.0.0 -- V5 Alpha 1 Phase C (69fc958)
        "2324bbf1ecebdca3149c16d3b9be94b6ec6bca409f6a78f0343f482c742f03cd",
    ),
    "v5_core_defender": (
        # 1.0.0 -- V5 Alpha 1 Phase C (69fc958)
        "be1ba8a24aee67fe378d0f90957d023024704697de7b4249d98122e75fac4e22",
    ),
    "v5_dual_team": (
        # 1.0.0 -- V5 Alpha 1 Phase C (69fc958)
        "2088e6b14d36ef2f0283ba11b9430c0eb0cddc4e8002ffeb0b372942ec3e29c0",
    ),
}

#: The digest each bundled starter currently has, pinned so that changing one
#: is a deliberate act. A failure here means the bundled content moved: append
#: the *old* digest printed by the failure to that starter's
#: :data:`SUPERSEDED_STARTER_DIGESTS` entry (so existing pristine installs
#: upgrade instead of being frozen as "customized"), then update the value
#: below. Never update this alone.
CURRENT_STARTER_DIGESTS: Mapping[str, str] = {
    "runner": "f8ec6ebac4425526b1a883d6abd8f55c8e055ba00e78590d562b1542a959686b",
    "writer": "624a5ce1aad0101325e2ac306b4013c1405e9e0ee2658528e61eefa88305f2f8",
    "seeker": "681985583bc07e7811c7fb771677e1daf0de8481bfdf5086558fa291a68ad67b",
    "spiral": "f45fcad27e523945f34ee003a29852a46a80bfdb2ad29af1aca725d118e3ccfd",
    "claimer": "6f3c7acd16b077c74ce4ea87de8eb26c830858042d5f96e5871b881a141ebcec",
    "strider": "b8321e66eca6cba0d7116c6f456eece2c8f8b8a4a4700bb670cec82cbc6b23f0",
    "hunter": "da5108134ac89462cb560fe826d4e4a3104b1c1cbd6dbcb8efb5d840fb6a5d7b",
    "wanderer": "9eb8d8034a9a295129218f9b5d9b0105606b0b708cec8fe9230e3cbfcea77f1a",
    "adaptive": "88964b8f5b4442601f1aecea3a2d02001a3ee9ecab7cccd25de436888697947f",
    "raider": "1fe4b14877d8fa737284bffca47f4d102425d7e3787c1e2441fd90cb6548afde",
    "sentinel": "4fdb2601c287bbd261dc07115082f8dfaf840c4ff47586ca71d58c53ccbd58a0",
    "v4_claimer": "f34d61b83819776368cddf95c597b1997591aa2b97d92949371704596b54b2ed",
    "v4_concentrated_attacker": (
        "94e9b1cd5a674bce2ec35aa60f1677370ecc322d023610a7494a463f89bbd09d"
    ),
    "v4_defender_scout": "ba14eff7ada06f0cd83fe88e600a73e4a817b5fd8d48e4012a3636fc72663d0e",
    "v4_local_defender": "8a7f53d9635467360a57876f044c5c9b752464ae572c484d59bb0a1024b8e619",
    "v4_scout": "8cd6760ffa9057f0513a4d245a2db05194fb5d4a87c4cc668298d5ac934eaa1d",
    "v4_quorum": "20a4ffe6a09110b7d3e636d19aa019cb11619834a638f0c2834e86bd5b95d414",
    "v5_region_attacker": "bacf587a66a25ea1209d634cf782a28570e38789f494093b7206edd5b54719e7",
    "v5_scout_striker": "e23bb1d07f32a5ac06c3b6295fa32fb0f177a5e540cd02b558c84becc6241e1c",
    "v5_core_defender": "f7fcaa52694a77c4f0b96a5d1046f8d282ae48c771a142c66681073d26238dee",
    "v5_dual_team": "9773667d547ec3de0c8ef9e5b17d8f7b7f4271631235742e69aebd9569edf79b",
}


@dataclass(frozen=True)
class StarterBootstrapError:
    """One bundled starter that failed validation, captured rather than raised."""

    name: str
    message: str


@dataclass(frozen=True)
class StarterRefresh:
    """One installed starter safely upgraded to current bundled content."""

    name: str
    path: Path
    previous_digest: str
    digest: str


@dataclass(frozen=True)
class StarterCustomization:
    """One installed starter left alone because it is not a pristine bundled copy."""

    name: str
    path: Path
    digest: str
    bundled_digest: str


@dataclass(frozen=True)
class StarterBootstrapResult:
    """Outcome of :func:`ensure_starter_agents`.

    Each bundled starter is validated and installed independently, so one
    malformed starter is recorded in ``errors`` and skipped rather than
    preventing every other starter in ``installed`` from being copied.

    ``installed`` lists individual files newly written into a catalog that did
    not have them; ``refreshed`` and ``customized`` are per-starter and were
    added in V5 Alpha 1 Phase E, defaulted so every pre-existing caller and
    test constructing or reading this result is unaffected.
    """

    installed: tuple[Path, ...]
    errors: tuple[StarterBootstrapError, ...]
    refreshed: tuple[StarterRefresh, ...] = ()
    customized: tuple[StarterCustomization, ...] = ()


def describe_bootstrap_errors(result: StarterBootstrapResult) -> str | None:
    """Human-readable summary of ``result.errors``, or ``None`` if there were none."""

    if not result.errors:
        return None
    lines = ["starter bootstrap completed with errors:"]
    lines.extend(f"  {error.name}: {error.message}" for error in result.errors)
    return "\n".join(lines)


def describe_starter_refresh(result: StarterBootstrapResult) -> str | None:
    """What the refresh pass changed and what it deliberately left alone.

    ``None`` when there is nothing to say, so a caller stays silent on the
    ordinary run where every starter is already current. The customized list
    is the product-visible half of the safety policy: it tells a user *why* a
    bundled starter they edited did not gain the newer bundled version's
    features, which is otherwise indistinguishable from the feature not
    existing at all.
    """

    if not result.refreshed and not result.customized:
        return None
    lines: list[str] = []
    if result.refreshed:
        names = ", ".join(sorted(entry.name for entry in result.refreshed))
        lines.append(f"updated bundled starter agents to their current version: {names}")
    if result.customized:
        names = ", ".join(sorted(entry.name for entry in result.customized))
        lines.append(
            "kept your edited copies of these starter agents, so they do not have "
            f"the current bundled version's changes: {names}. Rename or delete one "
            "to receive the bundled version."
        )
    return "\n".join(lines)


def _copy_missing(
    source_agent_dir: Path, destination_dir: Path, files: list[Path]
) -> list[Path]:
    """Write only files the catalog does not already have, never overwriting.

    The historical ``ensure_starter_agents`` contract, kept verbatim for the
    fresh-install case and for a starter the refresh policy has classified as
    user-modified: restoring a file the user deleted overwrites nothing, while
    an existing file is always theirs.
    """

    created: list[Path] = []
    for source in files:
        relative = source.relative_to(source_agent_dir)
        destination = destination_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("xb") as output, source.open("rb") as input_file:
                shutil.copyfileobj(input_file, output)
        except FileExistsError:
            continue
        created.append(destination.resolve())
    return created


def _mirror_bundled(
    source_agent_dir: Path, destination_dir: Path, files: list[Path]
) -> None:
    """Make ``destination_dir`` exactly reproduce the bundled starter.

    Only reached for a directory whose digest proved it an untouched copy of a
    known past bundled release, so every file in it came from that release and
    removing one the current release dropped is correct rather than
    destructive. Files whose bytes already match are left untouched, so a
    refresh that changes one file does not churn the rest.
    """

    wanted = {source.relative_to(source_agent_dir): source for source in files}
    for relative, source in wanted.items():
        destination = destination_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = source.read_bytes()
        if destination.is_file() and destination.read_bytes() == payload:
            continue
        destination.write_bytes(payload)
    base = destination_dir.resolve()
    for existing in starter_content_files(destination_dir):
        if existing.relative_to(base) not in wanted:
            existing.unlink()


def ensure_starter_agents(
    *,
    resource_root: Path | None = None,
    data_root: Path | None = None,
) -> StarterBootstrapResult:
    """Install missing starters and refresh untouched outdated ones.

    Validation and installation happen per starter: a malformed starter is
    recorded in the result's ``errors`` and skipped, it does not prevent any
    other bundled starter from being validated and installed. Only a wholly
    missing resource root -- there being no bundled starters to consider at
    all -- still raises ``FileNotFoundError``, since that is an environment/
    packaging failure rather than one corrupt starter.

    Each installed starter takes exactly one of four paths, decided by
    comparing its whole content against the bundled tree (V5 Alpha 1 Phase E;
    before it an installed starter was never updated at all, so an upgraded
    installation silently kept whatever manifest it first received and never
    saw a newer bundled version's parameter schema):

    * **absent** -- the current bundled version is installed;
    * **already current** -- nothing is written;
    * **an untouched copy of a superseded bundled release**
      (:data:`SUPERSEDED_STARTER_DIGESTS`) -- upgraded to current bundled
      content;
    * **anything else** -- treated as user-modified and preserved, with only
      missing files restored, exactly as before this policy existed.

    Idempotent by construction: the second run of any of these lands on
    "already current" or "user-modified with nothing missing", and both write
    nothing.
    """
    resources = (resource_root or get_resource_root()).expanduser().resolve()
    writable = (data_root or get_data_root()).expanduser().resolve()
    source_dir = _starter_resource_dir(resources)

    agents_dir = writable / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    errors: list[StarterBootstrapError] = []
    refreshed: list[StarterRefresh] = []
    customized: list[StarterCustomization] = []
    for name in STARTER_AGENT_NAMES:
        try:
            files = _validate_starter(source_dir, name)
        except (FileNotFoundError, ValueError) as exc:
            errors.append(StarterBootstrapError(name=name, message=str(exc)))
            continue
        source_agent_dir = source_dir / name
        destination_dir = agents_dir / name

        # Computed before anything is written: restoring a missing file would
        # change the very content this classification is about.
        installed_digest = starter_content_digest(destination_dir)
        bundled_digest = starter_content_digest(source_agent_dir)

        if installed_digest is None:
            created.extend(_copy_missing(source_agent_dir, destination_dir, files))
            continue
        if installed_digest == bundled_digest:
            continue
        if installed_digest in SUPERSEDED_STARTER_DIGESTS.get(name, ()):
            _mirror_bundled(source_agent_dir, destination_dir, files)
            refreshed.append(
                StarterRefresh(
                    name=name,
                    path=destination_dir.resolve(),
                    previous_digest=installed_digest,
                    digest=str(bundled_digest),
                )
            )
            continue
        created.extend(_copy_missing(source_agent_dir, destination_dir, files))
        customized.append(
            StarterCustomization(
                name=name,
                path=destination_dir.resolve(),
                digest=installed_digest,
                bundled_digest=str(bundled_digest),
            )
        )
    return StarterBootstrapResult(
        installed=tuple(created),
        errors=tuple(errors),
        refreshed=tuple(refreshed),
        customized=tuple(customized),
    )
