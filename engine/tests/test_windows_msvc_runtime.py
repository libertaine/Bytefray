"""One Microsoft-signed Visual C++ runtime ships, and recipients accept its terms.

The first 5.1.0-alpha.1 Windows build shipped CPython's 14.42 runtime copies and
Qt-re-signed 14.44 copies, which Windows mixed in each Qt process; the re-signed
files are not the unmodified Distributable Code Visual Studio's terms allow to be
redistributed, and nothing asked recipients to agree to the terms those require.
tools/replace_msvc_runtime.py (run by tools/build_win.ps1) replaces every copy
with the files tools/msvc_runtime.json pins, and tools/installer.iss presents the
terms and refuses an unattended installation that does not accept them. The real
build and the installed qualification are the behavioral tests; these checks keep
the mechanism from regressing between them.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from tools import replace_msvc_runtime as rmr

ROOT = Path(__file__).resolve().parents[2]
PIN = json.loads((ROOT / "tools" / "msvc_runtime.json").read_text(encoding="utf-8"))
BUILD = (ROOT / "tools" / "build_win.ps1").read_text(encoding="utf-8")
SCRIPT = (ROOT / "tools" / "installer.iss").read_text(encoding="utf-8")
TERMS_PATH = ROOT / "docs" / "releases" / "BYTEFRAY_5_1_0_ALPHA_1_MICROSOFT_RUNTIME_TERMS.txt"
APPLICATIONS = ("bytefray", "bytefray-cli", "bytefray-agent-designer", "bytefray-replay-viewer")


def _define(name: str) -> str:
    match = re.search(rf'^#define {name} "([^"]+)"$', SCRIPT, re.MULTILINE)
    assert match is not None, name
    return match.group(1)


def test_the_pin_names_one_version_from_the_licensed_visual_studio() -> None:
    assert (PIN["schema"], PIN["schema_version"]) == ("bytefray.msvc-runtime-pin", 1)
    assert PIN["version"] == "14.51.36247.0"
    assert PIN["grant"]["eulaid"] == "VS2026_Comm_ENU.1033"
    assert PIN["grant"]["distributable_list"] == "https://aka.ms/vs/18/redistribution"
    assert PIN["source"]["package"] == "Microsoft.VC.14.51.CRT.Redist.X64.base"
    assert PIN["source"]["folder"].endswith("\\x64\\Microsoft.VC145.CRT")
    assert sorted(PIN["files"]) == ["msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll",
                                    "vcruntime140_1.dll"]
    for entry in PIN["files"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) and entry["bytes"] > 0


def test_the_pin_covers_every_runtime_copy_pyinstaller_collects() -> None:
    locations = PIN["locations"]
    assert len(locations) == len({location.lower() for location in locations}) == 24
    for location in locations:
        tree, internal, *_ = location.split("/")
        assert tree in APPLICATIONS and internal == "_internal", location
        assert location.rsplit("/", 1)[1].lower() in PIN["files"], location
    # Each application's own runtime at its root; Qt's beside PySide6 and Shiboken6.
    for tree in APPLICATIONS:
        assert f"{tree}/_internal/VCRUNTIME140.dll" in locations


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict]:
    """A dist tree holding old copies at the pinned locations, and pinned source files."""

    source, dist = tmp_path / "Microsoft.VC145.CRT", tmp_path / "dist"
    source.mkdir()
    files = {}
    for name in PIN["files"]:
        body = f"new {name}".encode()
        (source / name).write_bytes(body)
        files[name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    for location in PIN["locations"]:
        target = dist / location
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"old " + location.encode())
    (dist / "bytefray-spectator").mkdir()
    (dist / "bytefray-spectator" / "vcruntime140.dll").write_bytes(b"not PyInstaller output")
    pin = {**PIN, "files": files}
    return dist, source, pin


def _version(path: Path) -> str:
    return PIN["version"]


def _snapshot(dist: Path) -> dict[str, bytes]:
    return {path.relative_to(dist).as_posix(): path.read_bytes() for path in dist.rglob("*") if path.is_file()}


def test_every_copy_is_replaced_by_the_pinned_file(tmp_path: Path) -> None:
    dist, source, pin = _fixture(tmp_path)
    replaced = rmr.replace(dist, source, pin, _version)
    assert len(replaced) == 24
    for location in PIN["locations"]:
        name = location.rsplit("/", 1)[1].lower()
        assert (dist / location).read_bytes() == (source / name).read_bytes()
    assert (dist / "bytefray-spectator" / "vcruntime140.dll").read_bytes() == b"not PyInstaller output"


@pytest.mark.parametrize("damage", ["source-hash", "source-version", "source-missing", "extra-runtime",
                                    "missing-location", "unpinned-name"])
def test_any_mismatch_stops_before_a_file_changes(tmp_path: Path, damage: str) -> None:
    dist, source, pin = _fixture(tmp_path)
    version = _version
    if damage == "source-hash":
        (source / "msvcp140.dll").write_bytes(b"re-signed")
    elif damage == "source-version":
        def version(path: Path) -> str:
            return "14.44.35211.0"
    elif damage == "source-missing":
        (source / "vcruntime140_1.dll").unlink()
    elif damage == "extra-runtime":
        (dist / "bytefray" / "_internal" / "concrt140.dll").write_bytes(b"unexpected")
    elif damage == "missing-location":
        (dist / "bytefray-cli" / "_internal" / "VCRUNTIME140_1.dll").unlink()
    elif damage == "unpinned-name":
        pin = {**pin, "locations": [*pin["locations"], "bytefray/_internal/ucrtbase.dll"]}
        (dist / "bytefray" / "_internal" / "ucrtbase.dll").write_bytes(b"ucrt")
    before = _snapshot(dist)
    with pytest.raises(rmr.RuntimeMismatch):
        rmr.replace(dist, source, pin, version)
    assert _snapshot(dist) == before


def test_release_builds_must_replace_the_runtime_before_the_smoke_tests() -> None:
    assert "[string]$MsvcRuntimeDir" in BUILD
    assert 'if ($SpectatorExe -and -not $MsvcRuntimeDir) { throw' in BUILD
    replacement = BUILD.index('tools\\replace_msvc_runtime.py")')
    assert BUILD.index('tools\\omit_unused_qt.py") --dist $DistDir') < replacement
    assert replacement < BUILD.index("# Verify no Python bytecode/cache") < BUILD.index("# Exercise the dynamically imported Designer")
    # Each source file's own Microsoft signature, decoded from the file, is checked first.
    assert 'Get-AuthenticodeSignature -LiteralPath $Source' in BUILD
    assert "$Cms.CheckSignature($true)" in BUILD
    assert "[regex]::Escape($Pin.signer_organization)" in BUILD
    assert BUILD.index("Get-EmbeddedSignerSubject $Source") < replacement


def test_the_terms_and_the_record_ship_and_the_list_is_checked_against_the_pin() -> None:
    notices = BUILD.index("& $PyExe @NoticeArgs")
    copy = BUILD.index('Copy-Item -LiteralPath $MsvcRecord -Destination $MsvcNotices')
    assert notices < copy < BUILD.index("$InstalledDocuments = @(")
    assert '"licenses\\microsoft-visual-cpp-runtime"' in BUILD
    listing = BUILD.index("[IO.File]::WriteAllLines($FileList")
    check = BUILD.index("if ($Runtime.Count -ne $Pinned.Count -or $Wrong.Count -gt 0)")
    assert listing < check < BUILD.index('"[build] Success."')


def test_setup_presents_the_terms_and_will_not_compile_without_the_pinned_runtime() -> None:
    assert "LicenseFile={#MsvcTermsFile}" in SCRIPT
    assert (ROOT / "tools" / _define("MsvcTermsFile").replace("\\", "/")).resolve() == TERMS_PATH.resolve()
    assert _define("MsvcRuntimeFolder") == "licenses\\microsoft-visual-cpp-runtime"
    assert '+ MsvcRuntimeFolder + "\\MSVC_RUNTIME_PROVENANCE.json")' in SCRIPT
    assert SCRIPT.count("#error ") == 2


def test_the_terms_file_is_the_one_setup_names() -> None:
    raw = TERMS_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "Inno Setup reads a UTF-8 License page only with a BOM"
    text = raw.decode("utf-8-sig")
    terms_id = _define("MsvcTermsId")
    assert f"Terms identifier: {terms_id}" in text and f"End of terms {terms_id}." in text
    for name in ("VCRUNTIME140.dll", "VCRUNTIME140_1.dll", "MSVCP140.dll", "MSVCP140_1.dll", "MSVCP140_2.dll"):
        assert name in text
    flat = " ".join(text.split())
    assert PIN["version"] in flat and "EULAID VS2026_Comm_ENU.1033" in flat
    assert "These terms apply only to the Microsoft Runtime Files." in flat
    assert "licensed under the MIT License" in flat
    assert "to reverse engineer for debugging such modifications" in flat
    assert "You may not modify these files." in flat
    for heading in ("11. SCOPE OF LICENSE.", "14. COMPLIANCE WITH TRADE LAWS.", "16. CONSUMER RIGHTS; REGIONAL VARIATIONS.",
                    "17. DISCLAIMER OF WARRANTY.", "18. LIMITATION ON DAMAGES."):
        assert heading in flat


def test_an_unattended_installation_must_accept_the_terms_explicitly() -> None:
    accepted = SCRIPT[SCRIPT.index("function TermsAccepted") : SCRIPT.index("function PrepareToInstall")]
    assert "if WizardSilent then" in accepted
    assert "CompareText(ExpandConstant('{param:ACCEPTMICROSOFTRUNTIMETERMS|}'), '{#MsvcTermsId}') = 0" in accepted
    assert "Result := WizardForm.LicenseAcceptedRadio.Checked;" in accepted
    prepare = SCRIPT[SCRIPT.index("function PrepareToInstall") : SCRIPT.index("function JsonString")]
    # The first refusal, before any folder is examined.
    assert prepare.index("if not TermsAccepted() then") < prepare.index("else if HasUnresolvedLink(App)")
    notes = (ROOT / "docs" / "releases" / "BYTEFRAY_5_1_0_ALPHA_1_RELEASE_NOTES.md").read_text(encoding="utf-8")
    assert f"/ACCEPTMICROSOFTRUNTIMETERMS={_define('MsvcTermsId')}" in notes


def test_setup_records_how_by_whom_and_when_the_terms_were_accepted() -> None:
    prepare = SCRIPT[SCRIPT.index("function PrepareToInstall") : SCRIPT.index("function JsonString")]
    assert "Log('Microsoft runtime terms {#MsvcTermsId} accepted: ' + TermsAcceptance);" in prepare
    assert "GetUserNameString()" in prepare and "GetDateTimeString(" in prepare
    register = SCRIPT[SCRIPT.index("procedure RegisterPreviousData") : SCRIPT.index("{ True when the folder still contains")]
    for name in ("MicrosoftRuntimeTerms", "MicrosoftRuntimeTermsSha256", "MicrosoftRuntimeTermsAcceptance"):
        assert f"SetPreviousData(PreviousDataKey, '{name}'," in register
