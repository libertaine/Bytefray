; Bytefray 5.1 Alpha Windows installer (Inno Setup 6.3 or later). Build from the
; repository root, after tools\build_win.ps1 -SpectatorExe <reviewed build> has
; filled dist\windows, with:
;   ISCC.exe tools\installer.iss
;
; Side-by-side with the stable release. Bytefray 5.0's installer is a
; per-machine installation (AppId {A5B86D38-9A6C-4D7F-9B4E-BA7720000002},
; C:\Program Files\Bytefray, data in C:\ProgramData\Bytefray) that sets
; BYTEFRAY_ROOT machine-wide. This 5.1 Alpha line is a separate product
; identity: its own AppId, a per-user installation that never needs
; administrator rights, its own Start Menu folder and its own data folder. It
; writes no environment variable and nothing under HKLM, so it cannot
; overwrite, upgrade, uninstall or redirect Bytefray 5.0. Every later 5.1 Alpha
; build keeps this AppId and upgrades the previous one in place.
;
; Data root. The installer records the data folder in
; {app}\bin\bytefray-install.json; tools\pyi_rth_bytefray_install.py makes every
; installed executable use it, ignoring a BYTEFRAY_ROOT inherited from
; Bytefray 5.0. The default is %LOCALAPPDATA%\Bytefray 5.1 Alpha. An upgrade
; keeps the previous installation's folder, and /BYTEFRAYDATAROOT=<folder>
; chooses another one (used for isolated validation installations). Nothing in
; the data folder is created or removed by the installer: uninstalling removes
; the program files and keeps agents, runs and caches.
;
; Versions (docs/COMPONENT_VERSIONING.md). AppVersion and ReleaseTag use the
; public SemVer spelling; PackageVersion is the PEP 440 spelling in
; pyproject.toml; FileVersion is the numeric Windows form that
; tools/windows_version_info.py stamps into the executables.
; engine/tests/test_windows_packaging_spec.py checks that all four agree.

#define AppName "Bytefray 5.1 Alpha"
#define ProductName "Bytefray"
#define AppVersion "5.1.0-alpha.1"
#define ReleaseTag "5.1.0-alpha.1"
#define PackageVersion "5.1.0a1"
#define FileVersion "5.1.0.101"
#define AppGuid "30F5713B-F69B-44F1-A759-AC43E33C0889"
#define AppPublisher "Bytefray Project"
#define DataFolderName "Bytefray 5.1 Alpha"
#define DistRoot "..\dist\windows"
#define OutputRoot "..\dist\installer"

[Setup]
; Bytefray 5.1 Alpha product identity. Keep this AppId unchanged across 5.1 Alpha builds.
AppId={{{#AppGuid}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} ({#AppVersion})
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/libertaine/Bytefray
AppSupportURL=https://github.com/libertaine/Bytefray/issues
AppUpdatesURL=https://github.com/libertaine/Bytefray/releases
AppCopyright=Copyright (c) 2025 Rod Satterfield
VersionInfoVersion={#FileVersion}
VersionInfoProductVersion={#FileVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductTextVersion={#AppVersion}
VersionInfoProductName={#ProductName}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} Setup
UninstallDisplayName={#AppName}
SetupIconFile=..\assets\branding\bytefray-icon.ico
UninstallDisplayIcon={app}\bin\bytefray-agent-designer\bytefray-agent-designer.exe
; Per-user: {autopf} is %LOCALAPPDATA%\Programs and {group} the user's Start Menu.
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputRoot}
OutputBaseFilename=Bytefray-{#ReleaseTag}-Windows-x64-Setup
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut for Agent Designer"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[InstallDelete]
; An upgrade or repair replaces each application folder instead of layering new
; files over the previous build's: a stale Qt plugin or DLL left behind could
; otherwise be loaded by the new build. Only these installer-owned folders are
; removed, and only when this AppId is already installed in this same folder.
Type: filesandordirs; Name: "{app}\bin\bytefray"; Check: IsUpgradeOfThisInstallation
Type: filesandordirs; Name: "{app}\bin\bytefray-cli"; Check: IsUpgradeOfThisInstallation
Type: filesandordirs; Name: "{app}\bin\bytefray-agent-designer"; Check: IsUpgradeOfThisInstallation
Type: filesandordirs; Name: "{app}\bin\bytefray-replay-viewer"; Check: IsUpgradeOfThisInstallation
Type: filesandordirs; Name: "{app}\bin\bytefray-spectator"; Check: IsUpgradeOfThisInstallation
Type: filesandordirs; Name: "{app}\licenses"; Check: IsUpgradeOfThisInstallation

[Files]
; Preserve each canonical PyInstaller onedir tree and their sibling relationship.
Source: "{#DistRoot}\bytefray\*"; DestDir: "{app}\bin\bytefray"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DistRoot}\bytefray-cli\*"; DestDir: "{app}\bin\bytefray-cli"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DistRoot}\bytefray-agent-designer\*"; DestDir: "{app}\bin\bytefray-agent-designer"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DistRoot}\bytefray-replay-viewer\*"; DestDir: "{app}\bin\bytefray-replay-viewer"; Flags: ignoreversion recursesubdirs createallsubdirs
; The independently versioned Bytefray Spectator companion and its build identity.
Source: "{#DistRoot}\bytefray-spectator\*"; DestDir: "{app}\bin\bytefray-spectator"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#DistRoot}\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\releases\BYTEFRAY_5_1_0_ALPHA_1_RELEASE_NOTES.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "..\docs\releases\BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[UninstallDelete]
; Written by [Code] below rather than [Files], so uninstall names it explicitly.
Type: files; Name: "{app}\bin\bytefray-install.json"

[Icons]
Name: "{group}\Bytefray Agent Designer (5.1 Alpha)"; Filename: "{app}\bin\bytefray-agent-designer\bytefray-agent-designer.exe"; WorkingDir: "{app}\bin"; Comment: "Create agents and run Bytefray matches"
Name: "{group}\Bytefray Replay Viewer (5.1 Alpha)"; Filename: "{app}\bin\bytefray-replay-viewer\bytefray-replay-viewer.exe"; WorkingDir: "{app}\bin"; Comment: "Open Bytefray replays"
Name: "{group}\Bytefray Spectator (5.1 Alpha)"; Filename: "{app}\bin\bytefray-spectator\bytefray-spectator.exe"; WorkingDir: "{app}\bin\bytefray-spectator"; Comment: "Watch verified Active Sensing presentations"
Name: "{autodesktop}\Bytefray Agent Designer (5.1 Alpha)"; Filename: "{app}\bin\bytefray-agent-designer\bytefray-agent-designer.exe"; WorkingDir: "{app}\bin"; Tasks: desktopicon

[Run]
Filename: "{app}\bin\bytefray-agent-designer\bytefray-agent-designer.exe"; WorkingDir: "{app}\bin"; Description: "Start Bytefray Agent Designer"; Flags: nowait postinstall skipifsilent

[Code]
const
  InstallRecordName = 'bytefray-install.json';

var
  ChosenDataRoot: String;

function UninstallKey(): String;
begin
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{' + '{#AppGuid}' + '}_is1';
end;

function SamePath(A, B: String): Boolean;
begin
  Result := AnsiLowercase(RemoveBackslashUnlessRoot(A)) = AnsiLowercase(RemoveBackslashUnlessRoot(B));
end;

{ /BYTEFRAYDATAROOT=<folder>, else the folder an earlier installation of this
  AppId recorded, else %LOCALAPPDATA%\Bytefray 5.1 Alpha. }
function DataRoot(): String;
begin
  if ChosenDataRoot = '' then
  begin
    ChosenDataRoot := ExpandConstant('{param:BYTEFRAYDATAROOT|}');
    if ChosenDataRoot = '' then
      ChosenDataRoot := GetPreviousData('DataRoot', '');
    if ChosenDataRoot = '' then
      ChosenDataRoot := ExpandConstant('{localappdata}\{#DataFolderName}');
    ChosenDataRoot := RemoveBackslashUnlessRoot(ExpandFileName(ChosenDataRoot));
  end;
  Result := ChosenDataRoot;
end;

function IsUpgradeOfThisInstallation(): Boolean;
var
  PreviousLocation: String;
begin
  Result := RegQueryStringValue(HKA, UninstallKey(), 'InstallLocation', PreviousLocation) and
    SamePath(PreviousLocation, ExpandConstant('{app}'));
end;

function IsSameOrInside(Path, Folder: String): Boolean;
begin
  Path := AddBackslash(AnsiLowercase(Path));
  Folder := AddBackslash(AnsiLowercase(Folder));
  Result := Copy(Path, 1, Length(Folder)) = Folder;
end;

{ The data folder must stay outside the program folder, which upgrades replace
  and uninstall removes, and must not contain it. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  App: String;
begin
  Result := '';
  App := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  if IsSameOrInside(DataRoot(), App) or IsSameOrInside(App, DataRoot()) then
    Result := 'The Bytefray data folder (' + DataRoot() + ') and the installation folder (' + App +
      ') must be separate folders, neither inside the other.';
end;

function JsonString(Value: String): String;
begin
  StringChangeEx(Value, '\', '\\', True);
  StringChangeEx(Value, '"', '\"', True);
  Result := '"' + Value + '"';
end;

procedure WriteInstallRecord();
var
  Lines: TArrayOfString;
begin
  SetArrayLength(Lines, 1);
  Lines[0] := '{"schema": "bytefray.installation", "schema_version": 1, ' +
    '"product": ' + JsonString('{#AppName}') + ', ' +
    '"version": ' + JsonString('{#AppVersion}') + ', ' +
    '"data_root": ' + JsonString(DataRoot()) + '}';
  if not SaveStringsToUTF8FileWithoutBOM(ExpandConstant('{app}\bin\') + InstallRecordName, Lines, False) then
    RaiseException('Could not write ' + ExpandConstant('{app}\bin\') + InstallRecordName);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    WriteInstallRecord();
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'DataRoot', DataRoot());
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine +
    'Data folder (agents, matches and caches; kept when Bytefray is uninstalled):' + NewLine +
    Space + DataRoot();
  if MemoGroupInfo <> '' then
    Result := Result + NewLine + NewLine + MemoGroupInfo;
  if MemoTasksInfo <> '' then
    Result := Result + NewLine + NewLine + MemoTasksInfo;
end;
