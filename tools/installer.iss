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
;
; Microsoft Visual C++ runtime. Every runtime DLL in the frozen applications is
; the exact Microsoft-signed file tools/msvc_runtime.json pins
; (tools\build_win.ps1 -MsvcRuntimeDir), redistributed under the Visual Studio
; Community 2026 Distributable Code terms, which require every recipient to agree
; to terms that protect it. The License page shows those terms (MsvcTermsFile);
; an unattended installation must accept them explicitly with
; /ACCEPTMICROSOFTRUNTIMETERMS=<MsvcTermsId> and is refused otherwise. Setup
; records how, by whom and when they were accepted with the uninstall entry. The
; compiler refuses a dist tree whose runtime was not replaced.

#define AppName "Bytefray 5.1 Alpha"
#define ProductName "Bytefray"
#define AppVersion "5.1.0-alpha.1"
#define ReleaseTag "5.1.0-alpha.1"
#define PackageVersion "5.1.0a1"
#define FileVersion "5.1.0.1011"
#define AppGuid "30F5713B-F69B-44F1-A759-AC43E33C0889"
#define AppPublisher "Bytefray Project"
#define DataFolderName "Bytefray 5.1 Alpha"
#define DistRoot "..\dist\windows"
#define OutputRoot "..\dist\installer"
#define MsvcTermsFile "..\docs\releases\BYTEFRAY_5_1_0_ALPHA_1_MICROSOFT_RUNTIME_TERMS.txt"
#define MsvcTermsId "BYTEFRAY-5.1-MSVC-RUNTIME-TERMS-1"
; Written by tools\build_win.ps1 beside the installed copy of the terms.
#define MsvcRuntimeFolder "licenses\microsoft-visual-cpp-runtime"

#if !FileExists(AddBackslash(AddBackslash(SourcePath) + DistRoot) + MsvcRuntimeFolder + "\MSVC_RUNTIME_PROVENANCE.json")
  #error dist\windows does not carry the pinned Microsoft runtime (run tools\build_win.ps1 with -MsvcRuntimeDir).
#endif
#if !FileExists(AddBackslash(SourcePath) + MsvcTermsFile)
  #error The Microsoft runtime terms file is missing.
#endif

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
; The terms for the Microsoft runtime files; Next stays disabled until they are accepted.
LicenseFile={#MsvcTermsFile}
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
Source: "..\docs\releases\BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json"; DestDir: "{app}\docs"; Flags: ignoreversion
; bin\bytefray-files.txt lists every file above with its SHA-256 (tools\build_win.ps1
; writes it). After an upgrade has installed them, RemoveObsoleteFiles in [Code]
; deletes the files the previous build's list names that this build no longer
; ships, so a stale Qt plugin or DLL cannot be loaded by the new build. Installed
; last, so an interrupted upgrade leaves the previous list for the next attempt.
Source: "{#DistRoot}\bytefray-files.txt"; DestDir: "{app}\bin"; Flags: ignoreversion

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
  FileListName = 'bytefray-files.txt';
  DirectoryAttribute = $10;
  ReparsePointAttribute = $400;

var
  ChosenDataRoot: String;
  { The previous build's bin\bytefray-files.txt, read before [Files] replaces it. }
  PreviousFiles: TArrayOfString;
  { How, by whom and when the Microsoft runtime terms were accepted; set by PrepareToInstall. }
  TermsAcceptance: String;

function GetLongPathName(ShortPath: String; LongPath: String; Size: Cardinal): Cardinal;
  external 'GetLongPathNameW@kernel32.dll stdcall';
function CreateFile(Name: String; Access, Share, Security, Disposition, Flags, Template: Cardinal): THandle;
  external 'CreateFileW@kernel32.dll stdcall';
function GetFinalPathNameByHandle(Handle: THandle; Path: String; Size, Flags: Cardinal): Cardinal;
  external 'GetFinalPathNameByHandleW@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';
function GetFileAttributes(Name: String): Cardinal;
  external 'GetFileAttributesW@kernel32.dll stdcall';

{ Path's attributes, or $FFFFFFFF. Missing is True only when Path does not exist
  (ERROR_FILE_NOT_FOUND or ERROR_PATH_NOT_FOUND), not when it cannot be examined.
  Unlike a directory search, this needs no right to list the parent folder. }
function PathAttributes(Path: String; var Missing: Boolean): Cardinal;
var
  Error: Integer;
begin
  Result := GetFileAttributes(Path);
  Missing := False;
  if Result = $FFFFFFFF then
  begin
    Error := DLLGetLastError();
    Missing := (Error = 2) or (Error = 3);
  end;
end;

function UninstallKey(): String;
begin
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{' + '{#AppGuid}' + '}_is1';
end;

{ Bytefray 5.0's (stable) uninstall key; see the header comment. }
function StableUninstallKey(): String;
begin
  Result := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{A5B86D38-9A6C-4D7F-9B4E-BA7720000002}_is1';
end;

{ The final path of an existing file or folder: 8.3 aliases expanded and
  junctions and symbolic links followed (GetFinalPathNameByHandleW), or '' when
  it cannot be opened. }
function FinalPath(Existing: String): String;
var
  Handle: THandle;
  Buffer: String;
  Count: Cardinal;
begin
  Result := '';
  { access 0, share read/write/delete, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS (folders) }
  Handle := CreateFile(Existing, 0, 7, 0, 3, $02000000, 0);
  if (Handle = 0) or (Handle = THandle(-1)) then
    Exit;
  SetLength(Buffer, 32767);
  Count := GetFinalPathNameByHandle(Handle, Buffer, 32767, 0);
  CloseHandle(Handle);
  if (Count = 0) or (Count >= 32767) then
    Exit;
  Result := Copy(Buffer, 1, Count);
  if Copy(Result, 1, 8) = '\\?\UNC\' then
    Result := '\\' + Copy(Result, 9, Length(Result))
  else if Copy(Result, 1, 4) = '\\?\' then
    Result := Copy(Result, 5, Length(Result));
end;

{ The absolute path with its existing part resolved -- long names, junctions and
  links -- so that an alias cannot make one folder look like another. The
  installed applications repeat this check (tools\pyi_rth_bytefray_install.py). }
function LongPath(Path: String): String;
var
  Existing, Tail, Buffer, Resolved: String;
  Count: Cardinal;
begin
  Existing := RemoveBackslashUnlessRoot(ExpandFileName(Path));
  Tail := '';
  while not DirExists(Existing) and not FileExists(Existing) and (ExtractFileDir(Existing) <> Existing) do
  begin
    Tail := ExtractFileName(Existing) + '\' + Tail;
    Existing := ExtractFileDir(Existing);
  end;
  Resolved := FinalPath(Existing);
  if Resolved = '' then
  begin
    SetLength(Buffer, 32767);
    Count := GetLongPathName(Existing, Buffer, 32767);
    if (Count > 0) and (Count < 32767) then
      Resolved := Copy(Buffer, 1, Count)
    else
      Resolved := Existing;
  end;
  Result := RemoveBackslashUnlessRoot(AddBackslash(Resolved) + Tail);
end;

function SamePath(A, B: String): Boolean;
begin
  Result := AnsiLowercase(LongPath(A)) = AnsiLowercase(LongPath(B));
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

{ True when the folder holds at least one Inno Setup uninstall log and every one
  of them is this AppId's (the AppId is stored in the log's header): the folder's
  installed files are this product's. A registered location alone is not proof,
  because the path may since have been redirected to another folder. }
function HasOwnUninstallLog(App: String): Boolean;
var
  Found: TFindRec;
  LogData: AnsiString;
  Header: String;
begin
  Result := False;
  if not FindFirst(App + '\unins*.dat', Found) then
    Exit;
  try
    repeat
      if not LoadStringFromFile(App + '\' + Found.Name, LogData) then
      begin
        Result := False;
        Exit;
      end;
      { The log's signature, then its AppId field at offset $40, NUL-terminated. }
      Header := Copy(LogData, 1, 448);
      if (Copy(Header, 1, 24) <> 'Inno Setup Uninstall Log') or
         (Copy(Header, 65, 39) <> '{' + '{#AppGuid}' + '}' + #0) then
      begin
        Result := False;
        Exit;
      end;
      Result := True;
    until not FindNext(Found);
  finally
    FindClose(Found);
  end;
end;

function IsUpgradeOfThisInstallation(): Boolean;
var
  PreviousLocation, App: String;
begin
  App := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  Result := RegQueryStringValue(HKA, UninstallKey(), 'InstallLocation', PreviousLocation) and
    SamePath(PreviousLocation, App) and HasOwnUninstallLog(App);
end;

function IsSameOrInside(Path, Folder: String): Boolean;
begin
  Path := AddBackslash(AnsiLowercase(LongPath(Path)));
  Folder := AddBackslash(AnsiLowercase(LongPath(Folder)));
  Result := Copy(Path, 1, Length(Folder)) = Folder;
end;

function Overlaps(A, B: String): Boolean;
begin
  Result := (A <> '') and (B <> '') and (IsSameOrInside(A, B) or IsSameOrInside(B, A));
end;

{ True when the folder holds, overlaps or belongs to an installation other than
  this AppId's own -- Bytefray 5.0, registered or not, or any other Inno Setup
  application -- which copying this product's files over would damage. Checked
  on every run, upgrades included. A leftover installation record proves
  nothing, so it is not consulted. }
function HoldsAnotherInstallation(App: String): Boolean;
var
  Found: TFindRec;
  Location: String;
  Own: Boolean;
begin
  Own := IsUpgradeOfThisInstallation();
  Result := False;
  if FindFirst(App + '\unins*.exe', Found) then
  begin
    FindClose(Found);
    Result := not Own;
  end;
  if not Own and (DirExists(App + '\bin\bytefray') or DirExists(App + '\bin\bytefray-agent-designer')) then
    Result := True;
  if RegQueryStringValue(HKLM, StableUninstallKey(), 'InstallLocation', Location) and Overlaps(Location, App) then
    Result := True;
  if RegQueryStringValue(HKCU, StableUninstallKey(), 'InstallLocation', Location) and Overlaps(Location, App) then
    Result := True;
end;

{ The first junction or symbolic link (any reparse point) at or below Path, or ''.
  Anything there that cannot be examined, or a folder that cannot be listed, is
  reported as well: an incomplete scan must not pass for one that found no link.
  Path itself is examined by name, so an unlistable parent cannot hide it. }
function FirstLink(Path: String): String;
var
  Found: TFindRec;
  Attributes: Cardinal;
  Missing: Boolean;
begin
  Result := '';
  Attributes := PathAttributes(Path, Missing);
  if Attributes = $FFFFFFFF then
  begin
    if not Missing then
      Result := Path + ' (cannot be examined)';
    Exit;
  end;
  if (Attributes and ReparsePointAttribute) <> 0 then
    Result := Path
  else if (Attributes and DirectoryAttribute) <> 0 then
  begin
    if not FindFirst(Path + '\*', Found) then
    begin
      Result := Path + ' (a folder that cannot be listed)';
      Exit;
    end;
    try
      repeat
        if (Found.Name <> '.') and (Found.Name <> '..') then
          Result := FirstLink(Path + '\' + Found.Name);
      until (Result <> '') or not FindNext(Found);
    finally
      FindClose(Found);
    end;
  end;
end;

{ A link inside the folders Setup installs into (or the uninstaller removes from)
  would make it write or delete files elsewhere, such as in a data folder, so
  neither proceeds while one exists. The installation folder itself may be one. }
function LinkInInstalledFolders(App: String): String;
begin
  Result := FirstLink(App + '\bin');
  if Result = '' then
    Result := FirstLink(App + '\docs');
  if Result = '' then
    Result := FirstLink(App + '\licenses');
end;

{ True when Path passes through a junction or symbolic link whose target Setup
  cannot resolve (a dangling link, or one Setup may not follow: Inno Setup enables
  Windows RedirectionGuard, under which Setup does not follow links created
  without administrator rights). Folder comparisons through such a link would
  silently compare the wrong paths, so callers refuse it instead. Links Setup can
  follow are resolved by LongPath and compared normally. Each existing component is
  examined by name; one that exists but cannot be examined (as below a link Setup
  may not follow) makes the path unverifiable too. }
function HasUnresolvedLink(Path: String): Boolean;
var
  Part: String;
  Attributes: Cardinal;
  Missing: Boolean;
begin
  Result := False;
  Part := RemoveBackslashUnlessRoot(ExpandFileName(Path));
  while not Result and (ExtractFileDir(Part) <> Part) do
  begin
    Attributes := PathAttributes(Part, Missing);
    if Attributes = $FFFFFFFF then
      Result := not Missing
    else
      Result := ((Attributes and ReparsePointAttribute) <> 0) and (FinalPath(Part) = '');
    Part := ExtractFileDir(Part);
  end;
end;

{ True when a newer build of this AppId is installed: its numeric file version,
  recorded with the uninstall entry, is higher than this build's. Installing an
  older build over it is refused -- its cleanup would act on the newer build's
  files, a path this build was not qualified for. }
function IsDowngrade(): Boolean;
var
  Previous: String;
  PreviousVersion, ThisVersion: Int64;
begin
  Previous := GetPreviousData('FileVersion', '');
  Result := (Previous <> '') and StrToVersion(Previous, PreviousVersion) and
    StrToVersion('{#FileVersion}', ThisVersion) and (ComparePackedVersion(PreviousVersion, ThisVersion) > 0);
end;

{ True when the Microsoft runtime terms were accepted: on the License page, or for an
  unattended installation (which shows no pages) by /ACCEPTMICROSOFTRUNTIMETERMS
  naming exactly these terms. }
function TermsAccepted(): Boolean;
begin
  if WizardSilent then
    Result := CompareText(ExpandConstant('{param:ACCEPTMICROSOFTRUNTIMETERMS|}'), '{#MsvcTermsId}') = 0
  else
    Result := WizardForm.LicenseAcceptedRadio.Checked;
end;

{ The data folder must stay outside the program folder, whose files upgrades replace
  and uninstall removes, and must not contain it; the program folder must not
  belong to another installation; and the folders Setup writes into must not be
  redirected by links. Folders whose location Setup cannot verify are refused, and
  so is any installation whose Microsoft runtime terms were not accepted. }
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  App, Link: String;
begin
  Result := '';
  App := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  Link := LinkInInstalledFolders(App);
  if not TermsAccepted() then
    Result := 'Bytefray includes Microsoft Visual C++ runtime files that may be installed only by someone who ' +
      'accepts their terms ({#MsvcTermsId}). An unattended installation must accept them with ' +
      '/ACCEPTMICROSOFTRUNTIMETERMS={#MsvcTermsId}. Nothing has been installed.'
  else if HasUnresolvedLink(App) or HasUnresolvedLink(DataRoot()) then
    Result := 'The installation folder (' + App + ') or the data folder (' + DataRoot() + ') is reached ' +
      'through a junction or symbolic link that Setup cannot follow, so Setup cannot check where it ' +
      'leads. Choose folders reached without such links.'
  else if HoldsAnotherInstallation(App) then
    Result := 'The folder ' + App + ' already holds another installation (for example Bytefray 5.0). ' +
      'Choose an empty folder for Bytefray 5.1 Alpha.'
  else if IsUpgradeOfThisInstallation() and IsDowngrade() then
    Result := 'A newer Bytefray 5.1 Alpha build (' + GetPreviousData('FileVersion', '') + ') is installed in ' +
      App + '. Installing this older build ({#FileVersion}) over it is not supported; uninstall it first.'
  else if IsSameOrInside(DataRoot(), App) or IsSameOrInside(App, DataRoot()) then
    Result := 'The Bytefray data folder (' + DataRoot() + ') and the installation folder (' + App +
      ') must be separate folders, neither inside the other.'
  else if Link <> '' then
    Result := 'The installation folder contains a link (junction or symbolic link) or a folder that ' +
      'cannot be listed: ' + Link + '. Setup does not install through links; remove it, or choose another folder.';
  if Result = '' then
  begin
    if WizardSilent then
      TermsAcceptance := 'unattended /ACCEPTMICROSOFTRUNTIMETERMS={#MsvcTermsId}'
    else
      TermsAcceptance := 'License page, I accept the agreement';
    TermsAcceptance := TermsAcceptance + '; Windows user ' + GetUserNameString() + '; local time ' +
      GetDateTimeString('yyyy/mm/dd hh:nn:ss', '-', ':');
    Log('Microsoft runtime terms {#MsvcTermsId} accepted: ' + TermsAcceptance);
  end;
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
  { Replace the old record's directory entry instead of rewriting the file in
    place: were it a hard link to some other file, rewriting would overwrite that. }
  if FileExists(ExpandConstant('{app}\bin\') + InstallRecordName) and
     not DeleteFile(ExpandConstant('{app}\bin\') + InstallRecordName) then
    RaiseException('Could not replace ' + ExpandConstant('{app}\bin\') + InstallRecordName);
  if not SaveStringsToUTF8FileWithoutBOM(ExpandConstant('{app}\bin\') + InstallRecordName, Lines, False) then
    RaiseException('Could not write ' + ExpandConstant('{app}\bin\') + InstallRecordName);
end;

function FileSha256(Path: String): String;
begin
  try
    Result := Lowercase(GetSHA256OfFile(Path));
  except
    Result := '';
  end;
end;

{ True for a path inside one of the folders [Files] installs: the five application
  trees, licenses and docs -- never the installation record, the list itself or
  anything else in the installation folder. }
function IsInstalledTreePath(Relative: String): Boolean;
var
  Lower: String;
begin
  Lower := Lowercase(Relative);
  Result := (Pos('bin\bytefray\', Lower) = 1) or (Pos('bin\bytefray-cli\', Lower) = 1) or
    (Pos('bin\bytefray-agent-designer\', Lower) = 1) or (Pos('bin\bytefray-replay-viewer\', Lower) = 1) or
    (Pos('bin\bytefray-spectator\', Lower) = 1) or (Pos('licenses\', Lower) = 1) or (Pos('docs\', Lower) = 1);
end;

{ One bin\bytefray-files.txt line, '<sha256>  <path relative to the installation
  folder>'. False for anything malformed, absolute, rooted, climbing out, or outside
  the folders [Files] installs. }
function ParseListedFile(Line: String; var Hash, Relative: String): Boolean;
begin
  Hash := Lowercase(Copy(Line, 1, 64));
  Relative := Copy(Line, 67, Length(Line));
  Result := (Length(Line) > 66) and (Copy(Line, 65, 2) = '  ') and (Trim(Relative) = Relative) and
    (Pos('..', Relative) = 0) and (Pos(':', Relative) = 0) and (Pos('/', Relative) = 0) and
    (Copy(Relative, 1, 1) <> '\') and IsInstalledTreePath(Relative);
end;

{ At ssInstall, before [Files] replaces it: the previous build's list, trusted only
  when this AppId's own installation is being upgraded and the list is unchanged
  since that build installed it (its SHA-256 is kept with the uninstall entry). }
procedure ReadPreviousFileList();
var
  List: String;
begin
  SetArrayLength(PreviousFiles, 0);
  List := ExpandConstant('{app}\bin\') + FileListName;
  if not IsUpgradeOfThisInstallation() or (GetPreviousData('FileListSha256', '') = '') or
     (FileSha256(List) <> GetPreviousData('FileListSha256', '')) or
     not LoadStringsFromFile(List, PreviousFiles) then
    SetArrayLength(PreviousFiles, 0);
end;

(* At ssPostInstall, after every new file is in place: delete each file the previous
   build installed that this build no longer ships -- named by the previous list,
   still byte-identical to what was installed, and reached at exactly that path with
   no link on the way -- then remove folders left empty. Anything else in the
   installation folder, including data a user keeps there, is never touched; nothing
   is deleted recursively; and an interrupted upgrade has deleted nothing. *)
procedure RemoveObsoleteFiles();
var
  Current: TArrayOfString;
  Shipped: TStringList;
  I: Integer;
  App, AppFinal, Hash, Relative, Target, Folder: String;
begin
  App := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  AppFinal := FinalPath(App);
  if (GetArrayLength(PreviousFiles) = 0) or (AppFinal = '') or
     not LoadStringsFromFile(App + '\bin\' + FileListName, Current) then
    Exit;
  Shipped := TStringList.Create;
  try
    for I := 0 to GetArrayLength(Current) - 1 do
      if ParseListedFile(Current[I], Hash, Relative) then
        Shipped.Add(Lowercase(Relative));
    Shipped.Sorted := True;
    for I := 0 to GetArrayLength(PreviousFiles) - 1 do
    begin
      if not ParseListedFile(PreviousFiles[I], Hash, Relative) or (Shipped.IndexOf(Lowercase(Relative)) >= 0) then
        Continue;
      Target := App + '\' + Relative;
      if not FileExists(Target) or (AnsiLowercase(FinalPath(Target)) <> AnsiLowercase(AppFinal + '\' + Relative)) or
         (FileSha256(Target) <> Hash) or not DeleteFile(Target) then
        Continue;
      Folder := ExtractFileDir(Target);
      { RemoveDir only removes empty folders. }
      while (Length(Folder) > Length(App)) and RemoveDir(Folder) do
        Folder := ExtractFileDir(Folder);
    end;
  finally
    Shipped.Free;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    ReadPreviousFileList();
  if CurStep = ssPostInstall then
  begin
    WriteInstallRecord();
    RemoveObsoleteFiles();
  end;
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'DataRoot', DataRoot());
  SetPreviousData(PreviousDataKey, 'FileListSha256', FileSha256(ExpandConstant('{app}\bin\') + FileListName));
  SetPreviousData(PreviousDataKey, 'FileVersion', '{#FileVersion}');
  SetPreviousData(PreviousDataKey, 'MicrosoftRuntimeTerms', '{#MsvcTermsId}');
  SetPreviousData(PreviousDataKey, 'MicrosoftRuntimeTermsSha256',
    FileSha256(ExpandConstant('{app}\{#MsvcRuntimeFolder}\') + ExtractFileName('{#MsvcTermsFile}')));
  SetPreviousData(PreviousDataKey, 'MicrosoftRuntimeTermsAcceptance', TermsAcceptance);
end;

{ True when the folder still contains the installed-file list whose SHA-256 Setup
  recorded with this AppId's uninstall entry -- a content check that a moved,
  substituted or redirected folder fails, not proof of identity (a deliberately
  planted copy of the list would pass). The uninstaller keeps its own uninstall
  log open, so it cannot read that log instead. }
function HoldsThisInstallation(App: String): Boolean;
var
  Recorded: String;
begin
  Result := RegQueryStringValue(HKA, UninstallKey(), 'Inno Setup CodeFile: FileListSha256', Recorded) and
    (Recorded <> '') and (FileSha256(App + '\bin\' + FileListName) = Recorded);
end;

{ The uninstaller removes the files Setup logged by their paths, so it refuses to
  run unless the installation folder still holds this installation -- reached
  without a link that cannot be followed, and with the installed-file list Setup
  recorded (the folder may have been moved or redirected since installation) --
  and contains no link, or unlistable folder, that could redirect a deletion. }
function InitializeUninstall(): Boolean;
var
  App, Problem: String;
begin
  App := RemoveBackslashUnlessRoot(ExpandConstant('{app}'));
  Problem := '';
  if HasUnresolvedLink(App) or not HoldsThisInstallation(App) then
    Problem := 'The folder ' + App + ' no longer holds this Bytefray 5.1 Alpha installation as it was ' +
      'installed (it was moved, changed or redirected, or is reached through a link that cannot be ' +
      'followed). Run the Bytefray 5.1 Alpha installer again to repair it, then uninstall.'
  else
  begin
    Problem := LinkInInstalledFolders(App);
    if Problem <> '' then
      Problem := 'The Bytefray 5.1 Alpha installation folder contains a link (junction or symbolic link) or a ' +
        'folder that cannot be listed: ' + Problem + '. Remove it, then uninstall again.';
  end;
  Result := Problem = '';
  if not Result then
    SuppressibleMsgBox(Problem + ' Nothing has been removed.', mbError, MB_OK, IDOK);
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
