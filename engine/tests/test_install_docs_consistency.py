"""Guard against version-pinned artifact filenames in installation docs.

A denylist of specific superseded version strings only catches a version
already seen going stale once; it says nothing about the *next* release and
has to be hand-extended forever. Bytefray publishes an alpha/RC/final
cadence, so these docs are instead required to name artifacts with a
``<version>`` placeholder and point readers at README.md (updated on every
release) for the concrete current filename, rather than embedding a
resolved version number that goes stale the moment the next release ships.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Installation instructions a user follows *today* to get the current
# release. This is deliberately a short, explicit list of the "how do I
# install right now" documents -- not every doc that happens to mention a
# version number. Design/compatibility/changelog/roadmap/research documents
# intentionally discuss historical releases by name for provenance and are
# out of scope.
CURRENT_INSTALL_DOCS = (
    ROOT / "INSTALL.md",
    ROOT / "docs" / "LINUX_INSTALL.md",
)

# A resolved Bytefray release version embedded in a *Bytefray* artifact
# filename or release URL, e.g. "4.0.0-rc2" in "Bytefray-Setup-4.0.0-rc2.exe",
# "4.0.0rc2" in "bytefray-4.0.0rc2-py3-none-any.whl", or "4.0.0-rc2" in
# "releases/tag/v4.0.0-rc2". Anchored to Bytefray's own naming (not a bare
# X.Y.Z scan) so it doesn't flag unrelated version numbers these docs
# legitimately cite, such as a bundled pMARS or glibc version.
RESOLVED_VERSION_RE = re.compile(
    r"(?:[Bb]ytefray-(?:[Ss]etup-)?|releases/(?:tag/v|download/[^/\s]*/bytefray-))"
    r"\d+\.\d+\.\d+(?:[-.]?(?:a|alpha|b|beta|rc)\d+)?"
)


def test_current_install_docs_use_version_neutral_artifact_names() -> None:
    """Installation docs must never embed a resolved release version.

    A ``<version>`` placeholder (or an unversioned mention like
    ``bytefray-<version>-windows.zip``) stays correct across every future
    alpha/RC/final release; a literal ``4.0.0-rc2`` does not.
    """

    for doc in CURRENT_INSTALL_DOCS:
        text = doc.read_text(encoding="utf-8")
        for match in RESOLVED_VERSION_RE.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            raise AssertionError(
                f"{doc.relative_to(ROOT)}:{line_no} embeds a resolved "
                f"release version {match.group(0)!r}; use a <version> "
                "placeholder and point readers at README.md instead"
            )
