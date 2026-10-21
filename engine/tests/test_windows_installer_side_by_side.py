"""tools/installer.iss installs Bytefray 5.1 Alpha beside Bytefray 5.0 and keeps user data.

Bytefray 5.0's installer (AppId {A5B86D38-...-BA7720000002}) is a per-machine
installation that sets BYTEFRAY_ROOT machine-wide and removes it on uninstall.
The 5.1 Alpha line must never share that identity, write that variable or
touch anything per-machine, and its own install, upgrade and uninstall steps
may remove only files it owns. The real installer run is qualified separately
(docs/releases/5_1_ALPHA1_WINDOWS_INSTALLER_QUALIFICATION.md); these checks keep
the script's safety properties from regressing between qualifications.
"""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (ROOT / "tools" / "installer.iss").read_text(encoding="utf-8")
# Everything except ;-comment lines (the header explains what the script avoids).
STATEMENTS = "\n".join(line for line in SCRIPT.splitlines() if not line.lstrip().startswith(";"))
STABLE_APP_ID = "A5B86D38-9A6C-4D7F-9B4E-BA7720000002"
APPLICATION_FOLDERS = (
    "bytefray",
    "bytefray-cli",
    "bytefray-agent-designer",
    "bytefray-replay-viewer",
    "bytefray-spectator",
)


def _section(name: str) -> list[str]:
    match = re.search(rf"^\[{name}\]\n(.*?)(?=^\[|\Z)", SCRIPT, re.MULTILINE | re.DOTALL)
    assert match is not None, f"[{name}] section missing"
    return [line for line in match.group(1).splitlines() if line.strip() and not line.lstrip().startswith(";")]


def _define(name: str) -> str:
    match = re.search(rf'^#define {name} "([^"]+)"$', SCRIPT, re.MULTILINE)
    assert match is not None, name
    return match.group(1)


def test_own_product_identity_beside_the_stable_release() -> None:
    guid = _define("AppGuid")
    assert re.fullmatch(r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}", guid)
    assert guid != STABLE_APP_ID
    assert "AppId={{{#AppGuid}}" in _section("Setup")
    assert _define("AppName") == "Bytefray 5.1 Alpha"
    setup = "\n".join(_section("Setup"))
    assert "DefaultDirName={autopf}\\{#AppName}" in setup
    assert "DefaultGroupName={#AppName}" in setup


def test_per_user_installation_writes_nothing_per_machine() -> None:
    setup = _section("Setup")
    assert "PrivilegesRequired=lowest" in setup
    assert not any(line.startswith("PrivilegesRequiredOverridesAllowed") for line in setup)
    assert not any(line.startswith("ChangesEnvironment") for line in setup)
    assert "[Registry]" not in STATEMENTS
    assert not re.search(r"\bRegWrite|\bRegDelete|\bSetEnvironment", STATEMENTS)
    # The only per-machine access is reading Bytefray 5.0's uninstall entry, to refuse its folder.
    reads_stable_entry = "RegQueryStringValue(HKLM, StableUninstallKey(), 'InstallLocation', Location)"
    assert reads_stable_entry in STATEMENTS
    for forbidden in ("HKLM", "Session Manager\\Environment", "{commonappdata}", "{commonpf}", "{commondesktop}",
                      "{commonprograms}", "uninsdeletevalue", "BYTEFRAY_ROOT"):
        assert forbidden not in STATEMENTS.replace(reads_stable_entry, ""), forbidden


def test_upgrade_cleanup_deletes_only_obsolete_unchanged_files_after_installing() -> None:
    """Nothing is ever deleted recursively or before the new build is in place: after
    an upgrade has installed its files, Setup removes a file only when the previous
    build's integrity-checked list names it, the new build no longer ships it, it is
    still byte-identical to what was installed, and it is reached at exactly that path."""

    assert "[InstallDelete]" not in STATEMENTS
    assert "filesandordirs" not in STATEMENTS and "DelTree" not in STATEMENTS
    # The list is installed after every file it names.
    files = _section("Files")
    assert files[-1] == 'Source: "{#DistRoot}\\bytefray-files.txt"; DestDir: "{app}\\bin"; Flags: ignoreversion'
    # Read before [Files] replaces it, trusted only for this AppId's own, unchanged list.
    read = SCRIPT[SCRIPT.index("procedure ReadPreviousFileList") : SCRIPT.index("(* At ssPostInstall")]
    assert "not IsUpgradeOfThisInstallation()" in read
    assert "(FileSha256(List) <> GetPreviousData('FileListSha256', ''))" in read
    assert "SetPreviousData(PreviousDataKey, 'FileListSha256', FileSha256(" in SCRIPT
    parse = SCRIPT[SCRIPT.index("function ParseListedFile") : SCRIPT.index("{ At ssInstall")]
    for rule in ("(Pos('..', Relative) = 0)", "(Pos(':', Relative) = 0)", "(Pos('/', Relative) = 0)",
                 "(Copy(Relative, 1, 1) <> '\\')", "(Copy(Line, 65, 2) = '  ')", "IsInstalledTreePath(Relative)"):
        assert rule in parse, rule
    # Only the folders [Files] installs: never the record, the list or anything else in {app}.
    trees = SCRIPT[SCRIPT.index("function IsInstalledTreePath") : SCRIPT.index("{ One bin\\bytefray-files.txt line")]
    for folder in (*(f"bin\\\\{name}\\\\" for name in APPLICATION_FOLDERS), "licenses\\\\", "docs\\\\"):
        assert f"Pos('{folder}', Lower) = 1".replace("\\\\", "\\") in trees, folder
    assert "bin\\bytefray-install.json" not in trees and "bytefray-files.txt" not in trees
    remove = SCRIPT[SCRIPT.index("procedure RemoveObsoleteFiles") : SCRIPT.index("procedure CurStepChanged")]
    assert "(Shipped.IndexOf(Lowercase(Relative)) >= 0)" in remove
    assert "(AnsiLowercase(FinalPath(Target)) <> AnsiLowercase(AppFinal + '\\' + Relative))" in remove
    assert "(FileSha256(Target) <> Hash)" in remove
    assert remove.count("DeleteFile(") == 1 and "RemoveDir(Folder)" in remove
    steps = SCRIPT[SCRIPT.index("procedure CurStepChanged") : SCRIPT.index("procedure RegisterPreviousData")]
    assert "if CurStep = ssInstall then\n    ReadPreviousFileList();" in steps
    assert steps.index("ssPostInstall") < steps.index("RemoveObsoleteFiles();")


def test_an_upgrade_is_recognized_by_location_and_by_its_own_uninstall_log() -> None:
    assert "RegQueryStringValue(HKA, UninstallKey(), 'InstallLocation', PreviousLocation)" in SCRIPT
    assert "SamePath(PreviousLocation, App) and HasOwnUninstallLog(App)" in SCRIPT
    own = SCRIPT[SCRIPT.index("function HasOwnUninstallLog") : SCRIPT.index("function IsUpgradeOfThisInstallation")]
    assert "FindFirst(App + '\\unins*.dat', Found)" in own


def test_links_inside_the_installation_stop_setup_and_the_uninstaller() -> None:
    links = SCRIPT[SCRIPT.index("function FirstLink") : SCRIPT.index("{ The data folder must stay outside")]
    assert "(Found.Attributes and ReparsePointAttribute) <> 0" in links
    # A folder that cannot be listed is reported, not taken as "no link".
    assert "Result := Path + ' (a folder that cannot be listed)';" in links
    for folder in ("bin", "docs", "licenses"):
        assert f"FirstLink(App + '\\{folder}')" in links
    prepare = SCRIPT[SCRIPT.index("function PrepareToInstall") : SCRIPT.index("function JsonString")]
    assert "Link := LinkInInstalledFolders(App);" in prepare and "Setup does not install through links" in prepare
    # The uninstaller also refuses a folder that no longer holds this installation
    # (redirected since installation) before looking for links inside it.
    uninstall = SCRIPT[SCRIPT.index("function InitializeUninstall") : SCRIPT.index("function UpdateReadyMemo")]
    assert "if HasUnresolvedLink(App) or not HasOwnUninstallLog(App) then" in uninstall
    assert "Problem := LinkInInstalledFolders(App);" in uninstall and "Result := Problem = '';" in uninstall


def test_the_installation_record_is_replaced_not_rewritten_in_place() -> None:
    """A hard link in place of the record must not carry the new record into another file."""

    record = SCRIPT[SCRIPT.index("procedure WriteInstallRecord") : SCRIPT.index("function FileSha256")]
    assert record.index("not DeleteFile(ExpandConstant('{app}\\bin\\') + InstallRecordName)") < record.index(
        "SaveStringsToUTF8FileWithoutBOM(")


def test_an_upgrade_recognizes_only_its_own_uninstall_log_header() -> None:
    own = SCRIPT[SCRIPT.index("function HasOwnUninstallLog") : SCRIPT.index("function IsUpgradeOfThisInstallation")]
    assert "(Copy(Header, 1, 24) <> 'Inno Setup Uninstall Log')" in own
    assert "(Copy(Header, 65, 39) <> '{' + '{#AppGuid}' + '}' + #0)" in own


def test_folders_reached_through_links_setup_cannot_follow_are_refused() -> None:
    """Under Windows RedirectionGuard (enabled by Inno Setup) Setup cannot follow a
    junction a standard user created, so a comparison through one would silently use
    the unresolved path; Setup refuses such folders before any other check."""

    check = SCRIPT[SCRIPT.index("function HasUnresolvedLink") : SCRIPT.index("{ The data folder must stay outside")]
    assert "((Found.Attributes and ReparsePointAttribute) <> 0) and (FinalPath(Part) = '')" in check
    prepare = SCRIPT[SCRIPT.index("function PrepareToInstall") : SCRIPT.index("function JsonString")]
    first = prepare.index("if HasUnresolvedLink(App) or HasUnresolvedLink(DataRoot()) then")
    assert first < prepare.index("HoldsAnotherInstallation(App)") < prepare.index("IsSameOrInside(DataRoot(), App)")


def test_the_file_list_names_the_documents_the_installer_copies() -> None:
    build = (ROOT / "tools" / "build_win.ps1").read_text(encoding="utf-8")
    listed = re.search(r"\$InstalledDocuments = @\(([^)]*)\)", build, re.DOTALL)
    assert listed is not None
    documents = sorted(re.findall(r'"([^"]+)"', listed.group(1)))
    shipped = sorted(re.findall(r'^Source: "\.\.\\([^"]+)"; DestDir: "\{app\}\\docs"', SCRIPT, re.MULTILINE))
    assert documents == shipped
    # Each entry carries the SHA-256 of the file as installed.
    assert '"{0}  {1}" -f (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant(), $Installed' in build


def test_uninstall_removes_only_what_it_installed() -> None:
    assert _section("UninstallDelete") == ['Type: files; Name: "{app}\\bin\\bytefray-install.json"']
    assert "[UninstallRun]" not in SCRIPT
    assert "[Dirs]" not in SCRIPT  # the data folder is created by the application, never by setup


def test_a_folder_holding_another_installation_is_refused() -> None:
    """A custom /DIR must not copy this product over Bytefray 5.0 (registered or an
    unregistered tree) or any other Inno Setup application's folder."""

    assert f"{{{STABLE_APP_ID}}}_is1" in SCRIPT
    body = SCRIPT[SCRIPT.index("function HoldsAnotherInstallation") : SCRIPT.index("{ The first junction")]
    for clue in ("FindFirst(App + '\\unins*.exe'", "DirExists(App + '\\bin\\bytefray')",
                 "RegQueryStringValue(HKLM, StableUninstallKey(), 'InstallLocation', Location) and Overlaps(Location, App)",
                 "RegQueryStringValue(HKCU, StableUninstallKey(), 'InstallLocation', Location) and Overlaps(Location, App)"):
        assert clue in body, clue
    # A leftover installation record must not make a foreign folder look like ours.
    assert "InstallRecordName" not in body.split("begin", 1)[1]
    # Checked on every run: a registered location may since point at another folder.
    assert "  else if HoldsAnotherInstallation(App) then" in SCRIPT
    assert "not IsUpgradeOfThisInstallation() and HoldsAnotherInstallation" not in SCRIPT


def test_folder_comparisons_resolve_aliases_and_links() -> None:
    """An 8.3 alias or a junction must not make an overlapping data folder look separate."""

    assert "external 'GetFinalPathNameByHandleW@kernel32.dll stdcall'" in SCRIPT
    assert "external 'GetLongPathNameW@kernel32.dll stdcall'" in SCRIPT
    long_path = SCRIPT[SCRIPT.index("function LongPath") : SCRIPT.index("function SamePath")]
    assert "Resolved := FinalPath(Existing);" in long_path
    same = SCRIPT[SCRIPT.index("function SamePath") : SCRIPT.index("{ /BYTEFRAYDATAROOT")]
    inside = SCRIPT[SCRIPT.index("function IsSameOrInside") : SCRIPT.index("function HoldsAnotherInstallation")]
    assert "LongPath(A)" in same and "LongPath(B)" in same
    assert "LongPath(Path)" in inside and "LongPath(Folder)" in inside


def test_data_folder_is_separate_kept_and_reused_on_upgrade() -> None:
    assert _define("DataFolderName") == "Bytefray 5.1 Alpha"
    assert "ExpandConstant('{param:BYTEFRAYDATAROOT|}')" in SCRIPT
    assert "GetPreviousData('DataRoot', '')" in SCRIPT
    assert "SetPreviousData(PreviousDataKey, 'DataRoot', DataRoot())" in SCRIPT
    assert "ExpandConstant('{localappdata}\\{#DataFolderName}')" in SCRIPT
    # PrepareToInstall refuses a data folder inside the program folder (or vice versa).
    assert "IsSameOrInside(DataRoot(), App) or IsSameOrInside(App, DataRoot())" in SCRIPT


def test_every_application_and_the_spectator_companion_are_installed() -> None:
    files = "\n".join(_section("Files"))
    for folder in APPLICATION_FOLDERS:
        assert (
            f'Source: "{{#DistRoot}}\\{folder}\\*"; DestDir: "{{app}}\\bin\\{folder}"; '
            "Flags: ignoreversion recursesubdirs createallsubdirs"
        ) in files
    assert 'Source: "{#DistRoot}\\licenses\\*"; DestDir: "{app}\\licenses"' in files
    documents = re.findall(r'^Source: "\.\.\\([^"]+)"; DestDir: "\{app\}\\docs"', files, re.MULTILINE)
    # Windows path syntax on every host (the suite also runs on Linux).
    assert sorted(PureWindowsPath(document).name for document in documents) == sorted(
        ("README.md", "LICENSE", "CHANGELOG.md", "BYTEFRAY_5_1_0_ALPHA_1_RELEASE_NOTES.md",
         "BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md", "BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json")
    )
    for document in documents:  # sources are relative to tools/
        assert (ROOT / document.replace("\\", "/")).is_file(), document


def test_shortcuts_point_into_the_installed_layout() -> None:
    icons = _section("Icons")
    designer = "{app}\\bin\\bytefray-agent-designer\\bytefray-agent-designer.exe"
    assert any(line.startswith('Name: "{group}\\Bytefray Agent Designer (5.1 Alpha)"') and designer in line for line in icons)
    assert any("{autodesktop}" in line and "Tasks: desktopicon" in line for line in icons)
    for line in icons:
        target = re.search(r'Filename: "\{app\}\\bin\\([^\\]+)\\', line)
        assert target is not None and target.group(1) in APPLICATION_FOLDERS, line


def test_installer_file_name_and_metadata_use_the_public_version() -> None:
    setup = "\n".join(_section("Setup"))
    assert "OutputBaseFilename=Bytefray-{#ReleaseTag}-Windows-x64-Setup" in setup
    assert "AppVersion={#AppVersion}" in setup
    assert "VersionInfoVersion={#FileVersion}" in setup
    assert "VersionInfoTextVersion={#AppVersion}" in setup
    assert "ArchitecturesAllowed=x64os" in setup
