# -SpectatorExe/-SpectatorLicense stage the pinned Bytefray Spectator build
# (tools/spectator_companion.json) beside the frozen applications, as
# tools/installer.iss requires. Without them only the four Python
# applications are built, as in CI.
#
# -Constraints <file> pins every dependency the build installs; a release
# build passes tools/windows-build-constraints.txt (the versions the
# 5.1.0-alpha.1 candidate was built and qualified with). See
# docs/releases/5_1_ALPHA1_WINDOWS_INSTALLER_QUALIFICATION.md for the recipe.
#
# -MsvcRuntimeDir <folder> is the licensed Visual Studio's
# VC\Redist\MSVC\<version>\x64\Microsoft.VC145.CRT folder (or the same files
# from its catalog-verified package). Every Microsoft Visual C++ runtime DLL
# in the frozen applications is replaced by the exact files tools/msvc_runtime.json
# pins (tools/replace_msvc_runtime.py). Required with -SpectatorExe, so a
# release build cannot ship the runtime copies PyInstaller collected.
param(
  [string]$Mode = "Release",
  [string]$SpectatorExe,
  [string]$SpectatorLicense,
  [string]$Constraints,
  [string]$MsvcRuntimeDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = $PSScriptRoot
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

# venv paths
$VenvDir = Join-Path $RepoRoot ".venv"
$PyExe   = Join-Path $VenvDir "Scripts\python.exe"
$ActPs1  = Join-Path $VenvDir "Scripts\Activate.ps1"

# Ensure Python available to create venv if needed
if (-not (Test-Path $VenvDir)) {
  Write-Host "[build] Creating virtual environment at .venv..."
  python -m venv $VenvDir
}

# Activate only if not already active (ok to skip if your policy blocks it)
if (-not $env:VIRTUAL_ENV) {
  try {
    . $ActPs1
  } catch {
    Write-Warning "[build] Activation script blocked; continuing without dot-activation."
  }
}

# Sanity: use venv's python exclusively (avoid PATH/Git '/usr/bin' issues)
if (-not (Test-Path $PyExe)) {
  throw "Venv python not found at $PyExe"
}

# Helper to run 'python -m <module> ...'
function Run-PyMod {
  param([Parameter(Mandatory)][string]$Module, [Parameter()][string[]]$Args)
  & $PyExe -m $Module @Args
  if ($LASTEXITCODE -ne 0) { throw "python -m $Module failed with exit code $LASTEXITCODE" }
}

# --- Dependencies -------------------------------------------------------------
$ConstraintArgs = @()
if ($Constraints) {
  $ConstraintArgs = @("-c", (Resolve-Path -LiteralPath $Constraints).Path)
  Write-Host "[build] Python $(& $PyExe -c 'import sys; print(sys.version.split()[0])'); dependencies pinned by $Constraints"
}
Run-PyMod -Module pip -Args (@("install","--upgrade","pip","wheel") + $ConstraintArgs)
# The editable install builds in an isolated environment, which ordinary
# constraints do not reach; --build-constraint pins that build backend too.
$BuildConstraintArgs = @()
if ($Constraints) { $BuildConstraintArgs = @("--build-constraint", (Resolve-Path -LiteralPath $Constraints).Path) }
Run-PyMod -Module pip -Args (@("install", "-e", ".[replay,designer,windows-build]") + $ConstraintArgs + $BuildConstraintArgs)

# Ensure PyInstaller available (from venv)
Run-PyMod -Module pip -Args @("show","pyinstaller") | Out-Null

# Output dirs
$BuildDir = Join-Path $RepoRoot "build\windows"
$DistDir  = Join-Path $RepoRoot "dist\windows"
Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $DistDir  -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir  | Out-Null

# Keep each app in its own onedir folder so the same
# layout can be copied beneath an installer's bin directory without renaming.
$Artifacts = @(
  @{ Name = "bytefray";                 Spec = "tools\bytefray.spec" },
  @{ Name = "bytefray-cli";             Spec = "tools\bytefray_cli.spec" },
  @{ Name = "bytefray-agent-designer";  Spec = "tools\agent_designer.spec" },
  @{ Name = "bytefray-replay-viewer";   Spec = "tools\replay_viewer.spec" }
)

foreach ($Artifact in $Artifacts) {
  $SpecPath = Join-Path $RepoRoot $Artifact.Spec
  if (-not (Test-Path $SpecPath)) { throw "Missing spec: $($Artifact.Spec)" }
  Write-Host "[build] Building $($Artifact.Name)..."
  & $PyExe -m PyInstaller --noconfirm --clean --workpath $BuildDir --distpath $DistDir $SpecPath
  if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed: $($Artifact.Name)" }

  $ExePath = Join-Path $DistDir "$($Artifact.Name)\$($Artifact.Name).exe"
  if (-not (Test-Path $ExePath)) { throw "Expected artifact was not produced: $ExePath" }
}

# Omit the Qt components Bytefray cannot use -- the GPL-3.0-only Qt Virtual
# Keyboard with the Quick/QML/OpenGL libraries only it needs, and the Qt PDF
# image reader (PDFium) -- then prove from every remaining binary's import table
# that nothing depends on them. See tools/omit_unused_qt.py.
& $PyExe (Join-Path $RepoRoot "tools\omit_unused_qt.py") --dist $DistDir
if ($LASTEXITCODE -ne 0) { throw "Omitting unused Qt components failed with exit code $LASTEXITCODE" }

# One Microsoft-signed Visual C++ runtime in every application (tools/msvc_runtime.json).
# PyInstaller collected CPython's 14.42 copies and Qt-re-signed 14.44 copies, which
# Windows mixed in one process. Replaced here, before the payload checks and every
# smoke test, so those run on the shipped runtime. Each source file must carry its
# own valid Microsoft signature (decoded from the file, not a Windows catalog);
# tools/replace_msvc_runtime.py then checks the pinned names, sizes, SHA-256 values,
# versions and locations, and changes nothing unless all of them match.
$MsvcPin = Join-Path $RepoRoot "tools\msvc_runtime.json"
$MsvcRecord = Join-Path $BuildDir "MSVC_RUNTIME_PROVENANCE.json"
if ($SpectatorExe -and -not $MsvcRuntimeDir) { throw "-MsvcRuntimeDir is required for a release build (with -SpectatorExe)." }
function Get-EmbeddedSignerSubject([string]$Path) {
  $Bytes = [IO.File]::ReadAllBytes($Path)
  $Optional = [BitConverter]::ToInt32($Bytes, 0x3C) + 24
  $Directories = $Optional + $(if ([BitConverter]::ToUInt16($Bytes, $Optional) -eq 0x20B) { 112 } else { 96 })
  $Offset = [BitConverter]::ToInt32($Bytes, $Directories + 32)
  $Length = [BitConverter]::ToInt32($Bytes, $Directories + 36)
  if ($Length -le 8) { return $null }
  $Cms = [System.Security.Cryptography.Pkcs.SignedCms]::new()
  $Cms.Decode($Bytes[($Offset + 8)..($Offset + [BitConverter]::ToInt32($Bytes, $Offset) - 1)])
  $Cms.CheckSignature($true)
  $Cms.SignerInfos[0].Certificate.Subject
}
if ($MsvcRuntimeDir) {
  Add-Type -AssemblyName System.Security
  $Pin = Get-Content -LiteralPath $MsvcPin -Raw | ConvertFrom-Json
  foreach ($Name in $Pin.files.PSObject.Properties.Name) {
    $Source = Join-Path $MsvcRuntimeDir $Name
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) { throw "$MsvcRuntimeDir has no $Name." }
    $Signature = Get-AuthenticodeSignature -LiteralPath $Source
    $Signer = Get-EmbeddedSignerSubject $Source
    if ($Signature.Status -ne "Valid" -or -not $Signer -or $Signer -notmatch [regex]::Escape($Pin.signer_organization)) {
      throw "$Source is not a validly Microsoft-signed file (status $($Signature.Status), embedded signer '$Signer')."
    }
  }
  & $PyExe (Join-Path $RepoRoot "tools\replace_msvc_runtime.py") --dist $DistDir --source $MsvcRuntimeDir --pin $MsvcPin --record $MsvcRecord
  if ($LASTEXITCODE -ne 0) { throw "Replacing the Microsoft Visual C++ runtime failed with exit code $LASTEXITCODE" }
} else {
  Write-Warning "[build] No -MsvcRuntimeDir: the Microsoft runtime copies are PyInstaller's; tools/installer.iss refuses this tree."
}

# Verify no Python bytecode/cache reached any distributable tree.
#
# This build runs from the live repository checkout, and the engine imports
# agent modules out of battle_engine/data at runtime, so CPython can write
# __pycache__ directories next to shipped product data as a normal
# consequence of running the product. The specs used to hand those
# directories to PyInstaller as (directory, destination) tuples, which it
# expands by collecting everything beneath them -- Phase F1's first
# remediation build bundled five stale .pyc files that way and was only made
# clean by sweeping the checkout by hand.
#
# tools/packaging_data.py now excludes bytecode by construction, so this is a
# non-destructive backstop rather than the fix: it deliberately does NOT
# delete anything from the checkout (the build must be correct from a dirty
# tree, not merely after a cleanup step), and instead fails the build if a
# future collection path is ever added that bypasses the shared collector.
foreach ($Artifact in $Artifacts) {
  $ArtifactDir = Join-Path $DistDir $Artifact.Name
  $Debris = @(
    Get-ChildItem -LiteralPath $ArtifactDir -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object {
        ($_.PSIsContainer -and $_.Name -eq "__pycache__") -or
        (-not $_.PSIsContainer -and $_.Extension -in ".pyc", ".pyo")
      }
  )
  if ($Debris.Count -gt 0) {
    $Listing = ($Debris | ForEach-Object { $_.FullName }) -join "`n  "
    throw "Python bytecode/cache reached the frozen payload for $($Artifact.Name):`n  $Listing"
  }
}
Write-Host "[build] Frozen payloads contain no Python bytecode/cache."

# Beta3's Designer identity header uses the shared square branding icon. The
# unified dispatcher imports the Designer dynamically, so prove its frozen
# tree contains the same runtime resource as the standalone GUI build.
$UnifiedBrandingIcon = Join-Path $DistDir "bytefray\_internal\assets\branding\bytefray-icon.png"
if (-not (Test-Path -LiteralPath $UnifiedBrandingIcon -PathType Leaf)) {
  throw "Unified Designer branding resource missing: $UnifiedBrandingIcon"
}

# Every executable carries the application version in its Windows version
# resource (tools/windows_version_info.py), so Explorer, the installer and
# support tooling report the same release. A spec that lost its version=
# argument would otherwise ship binaries that identify as nothing.
$Versions = & $PyExe (Join-Path $RepoRoot "tools\windows_version_info.py") | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "tools/windows_version_info.py failed with exit code $LASTEXITCODE" }
foreach ($Artifact in $Artifacts) {
  $Info = (Get-Item -LiteralPath (Join-Path $DistDir "$($Artifact.Name)\$($Artifact.Name).exe")).VersionInfo
  if ($Info.ProductVersion -ne $Versions.public -or "$($Info.FileVersionRaw)" -ne $Versions.file_version) {
    throw "$($Artifact.Name).exe identifies as '$($Info.ProductVersion)' ($($Info.FileVersionRaw)); expected '$($Versions.public)' ($($Versions.file_version))."
  }
}
Write-Host "[build] Version resources: $($Versions.public) ($($Versions.file_version))."

# Bytefray Spectator is a separate Godot application with its own version
# series. The installer bundles exactly the build tools/spectator_companion.json
# pins, beside the frozen applications, where Designer's discovery looks for it
# (app/services/spectator_viewer.py). Any other executable is refused.
$SpectatorDir = Join-Path $DistDir "bytefray-spectator"
Remove-Item -Recurse -Force $SpectatorDir -ErrorAction SilentlyContinue
if ($SpectatorExe) {
  if (-not $SpectatorLicense) { throw "-SpectatorLicense is required with -SpectatorExe." }
  $CompanionPath = Join-Path $RepoRoot "tools\spectator_companion.json"
  $Companion = Get-Content -LiteralPath $CompanionPath -Raw | ConvertFrom-Json
  $SpectatorHash = (Get-FileHash -LiteralPath $SpectatorExe -Algorithm SHA256).Hash.ToLower()
  if ($SpectatorHash -ne $Companion.windows.sha256) {
    throw "Spectator executable $SpectatorExe has SHA-256 $SpectatorHash; tools/spectator_companion.json pins $($Companion.windows.sha256)."
  }
  New-Item -ItemType Directory -Force -Path $SpectatorDir | Out-Null
  $StagedSpectator = Join-Path $SpectatorDir $Companion.windows.file
  Copy-Item -LiteralPath $SpectatorExe -Destination $StagedSpectator
  Copy-Item -LiteralPath $CompanionPath -Destination (Join-Path $SpectatorDir "SPECTATOR_BUILD.json")
  # A GUI-subsystem executable: Start-Process -Wait is what waits for it and
  # reports its exit code. --check verifies a bundled presentation and the
  # cue bank headlessly, from the staged location.
  $CheckOut = Join-Path ([IO.Path]::GetTempPath()) ("bytefray-spectator-check-" + [Guid]::NewGuid().ToString("N") + ".log")
  try {
    $Check = Start-Process -FilePath $StagedSpectator -ArgumentList @("--headless", "--", "--fixture=sample", "--check") `
      -Wait -PassThru -NoNewWindow -RedirectStandardOutput $CheckOut
    Get-Content -LiteralPath $CheckOut | Select-String "PRESENTATION|CUE BANK" | ForEach-Object { Write-Host "[build] Spectator $($_.Line)" }
    if ($Check.ExitCode -ne 0) { throw "The staged Spectator failed its --check (exit $($Check.ExitCode))." }
  } finally {
    Remove-Item -LiteralPath $CheckOut -Force -ErrorAction SilentlyContinue
  }
  Write-Host "[build] Staged Bytefray Spectator $($Companion.version) ($SpectatorHash)."
}

# License texts for everything the distribution bundles (dist\windows\licenses).
$NoticeArgs = @((Join-Path $RepoRoot "tools\collect_third_party_notices.py"), "--dist", $DistDir)
if ($SpectatorExe) { $NoticeArgs += @("--spectator-license", $SpectatorLicense) }
& $PyExe @NoticeArgs
if ($LASTEXITCODE -ne 0) { throw "Third-party notice collection failed with exit code $LASTEXITCODE" }

# The Microsoft runtime terms the installer's License page shows, and the record of
# the replacement, installed beside the other notices (after collection, which
# rewrites dist\windows\licenses). tools/installer.iss requires the record.
$MsvcTerms = Join-Path $RepoRoot "docs\releases\BYTEFRAY_5_1_0_ALPHA_1_MICROSOFT_RUNTIME_TERMS.txt"
if ($MsvcRuntimeDir) {
  $MsvcNotices = Join-Path $DistDir "licenses\microsoft-visual-cpp-runtime"
  New-Item -ItemType Directory -Force -Path $MsvcNotices | Out-Null
  Copy-Item -LiteralPath $MsvcTerms -Destination $MsvcNotices
  Copy-Item -LiteralPath $MsvcRecord -Destination $MsvcNotices
}

# Exercise the dynamically imported Designer from the unified dispatcher and
# the standalone Designer. The internal timeout enters the Qt event loop and
# closes deterministically without requiring desktop automation.
#
# AgentDesigner.__init__ eagerly calls ensure_starter_agents() against
# whatever data root get_data_root() resolves; a portable/frozen app with no
# BYTEFRAY_ROOT set defaults to writing beside its own executable
# (battle_engine.paths), so without isolation this smoke test previously
# left a runtime-generated agents/ directory inside the distributable trees,
# contaminating the exact tree
# tools/installer.iss and the portable ZIP both package verbatim. Isolated
# the same way the 'agents create' smoke block below already isolates
# BYTEFRAY_ROOT, so build qualification cannot pollute the distributable
# tree regardless of what a smoked GUI happens to initialize on startup.
$PreviousSmokeExit = $env:BYTEFRAY_GUI_SMOKE_EXIT_MS
$PreviousGuiSmokeRoot = $env:BYTEFRAY_ROOT
$GuiSmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("bytefray-gui-smoke-" + [Guid]::NewGuid().ToString("N"))
try {
  New-Item -ItemType Directory -Force -Path $GuiSmokeRoot | Out-Null
  $env:BYTEFRAY_GUI_SMOKE_EXIT_MS = "750"
  $env:BYTEFRAY_ROOT = $GuiSmokeRoot
  foreach ($Smoke in @(
    @{ Path = (Join-Path $DistDir "bytefray\bytefray.exe"); Args = @("design") },
    @{ Path = (Join-Path $DistDir "bytefray-agent-designer\bytefray-agent-designer.exe"); Args = @() }
  )) {
    Write-Host ("[build] GUI import/startup smoke: {0}" -f $Smoke.Path)
    # PowerShell does not wait for a Windows GUI-subsystem executable when
    # invoked with `&`. Start-Process -Wait is therefore required for the
    # standalone Designer: without it, $LASTEXITCODE is stale and the temp
    # root can be deleted before the still-starting child writes to it.
    # -ArgumentList rejects an empty array on some PowerShell versions
    # ("argument is null, empty, or an element ... contains a null value"),
    # so it's only included via splatting when there are real arguments.
    $StartProcessArgs = @{
      FilePath    = $Smoke.Path
      Wait        = $true
      PassThru    = $true
      WindowStyle = "Hidden"
    }
    if ($Smoke.Args.Count -gt 0) {
      $StartProcessArgs["ArgumentList"] = $Smoke.Args
    }
    $SmokeProcess = Start-Process @StartProcessArgs
    if ($SmokeProcess.ExitCode -ne 0) {
      throw "GUI import/startup smoke failed with exit code $($SmokeProcess.ExitCode)`: $($Smoke.Path)"
    }
  }
} finally {
  if ($null -eq $PreviousSmokeExit) {
    Remove-Item Env:BYTEFRAY_GUI_SMOKE_EXIT_MS -ErrorAction SilentlyContinue
  } else {
    $env:BYTEFRAY_GUI_SMOKE_EXIT_MS = $PreviousSmokeExit
  }
  if ($null -eq $PreviousGuiSmokeRoot) {
    Remove-Item Env:BYTEFRAY_ROOT -ErrorAction SilentlyContinue
  } else {
    $env:BYTEFRAY_ROOT = $PreviousGuiSmokeRoot
  }
  if (Test-Path -LiteralPath $GuiSmokeRoot) {
    Remove-Item -LiteralPath $GuiSmokeRoot -Recurse -Force -ErrorAction Stop
  }
  if (Test-Path -LiteralPath $GuiSmokeRoot) {
    throw "GUI smoke temporary root could not be removed: $GuiSmokeRoot"
  }
}

# Exercise 'bytefray agents create' against the actual frozen bytefray.exe in
# an isolated, throwaway BYTEFRAY_ROOT. This is a regression check for real,
# previously-shipped defects of one class: the unified executable spec listed
# its bundled resource directories by literal name, so each time the product
# gained a scaffold template the spec was left behind and the frozen build
# silently shipped without it. The retained Agent API v2 template pair must
# both remain available; absence fails `agents create --api-version 2` with
# "Agent template resource directory not found" (exit 2) in the distributed
# application while source checkouts and installed wheels both worked. The
# specs now derive that list from battle_engine.agent_scaffold's own
# inventory, engine/tests/test_windows_packaging_spec.py covers the derived
# data list without a real build, and engine/tests/
# test_frozen_scaffold_resources.py covers a built executable when
# BYTEFRAY_FROZEN_EXE points at one; this block is the build's own
# executable-level proof, run unconditionally on every build.
#
# Every supported (api-version, template) pair is exercised, not just the
# historical default -- covering only the default is precisely why three
# separate template omissions reached shipped executables.
#
# The three personal-copy templates copy an Active Sensing teaching starter,
# whose manifest requires the `sense` capability: validation must refuse it
# under the default Classic Ruleset (exit 2) and accept it under Active
# Sensing (Alpha).
$SmokeVariants = @(
  @{ Id = 'smoke_agent_v2';           CreateArgs = @('--api-version', '2');                            Validate = $true; Sensing = $false }
  @{ Id = 'smoke_agent_v2_annotated'; CreateArgs = @('--api-version', '2', '--template', 'annotated'); Validate = $true; Sensing = $false }
  @{ Id = 'smoke_window_scout';       CreateArgs = @('--api-version', '2', '--template', 'window_scout');       Validate = $true; Sensing = $true }
  @{ Id = 'smoke_watchful_keeper';    CreateArgs = @('--api-version', '2', '--template', 'watchful_keeper');    Validate = $true; Sensing = $true }
  @{ Id = 'smoke_roaming_reacquirer'; CreateArgs = @('--api-version', '2', '--template', 'roaming_reacquirer'); Validate = $true; Sensing = $true }
)
$SmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("bytefray-agents-create-smoke-" + [Guid]::NewGuid().ToString("N"))
$PreviousBytefrayRoot = $env:BYTEFRAY_ROOT
try {
  New-Item -ItemType Directory -Force -Path $SmokeRoot | Out-Null
  $env:BYTEFRAY_ROOT = $SmokeRoot
  $BytefrayExe = Join-Path $DistDir "bytefray\bytefray.exe"
  foreach ($Variant in $SmokeVariants) {
    $Label = ("agents create " + $Variant.Id + " " + ($Variant.CreateArgs -join ' ')).TrimEnd()
    Write-Host "[build] '$Label' smoke test against $BytefrayExe (BYTEFRAY_ROOT=$SmokeRoot)"
    & $BytefrayExe agents create $Variant.Id @($Variant.CreateArgs)
    if ($LASTEXITCODE -ne 0) {
      throw "'bytefray.exe $Label' failed with exit code $LASTEXITCODE"
    }
    $AgentDir = Join-Path (Join-Path $SmokeRoot 'agents') $Variant.Id
    $ManifestPath = Join-Path $AgentDir 'agent.yaml'
    $SourcePath = Join-Path $AgentDir 'agent.py'
    if (-not (Test-Path $ManifestPath) -or -not (Test-Path $SourcePath)) {
      throw "'bytefray.exe $Label' did not write the expected agent.yaml/agent.py under $SmokeRoot"
    }
    # A created Agent API v2 scaffold must also be usable, not merely
    # written: validation loads the manifest and the agent module through
    # the normal supported path, so a bundled-but-broken template fails here
    # rather than at a user's first match.
    if ($Variant.Validate -and $Variant.Sensing) {
      & $BytefrayExe agents validate $Variant.Id 2>$null | Out-Null
      if ($LASTEXITCODE -ne 2) {
        throw "'bytefray.exe agents validate $($Variant.Id)' under Classic exited $LASTEXITCODE; expected the capability refusal (2)"
      }
      & $BytefrayExe agents validate $Variant.Id --ruleset bytefray-rules-6-alpha1
      if ($LASTEXITCODE -ne 0) {
        throw "'bytefray.exe agents validate $($Variant.Id) --ruleset bytefray-rules-6-alpha1' failed with exit code $LASTEXITCODE"
      }
    } elseif ($Variant.Validate) {
      & $BytefrayExe agents validate $Variant.Id
      if ($LASTEXITCODE -ne 0) {
        throw "'bytefray.exe agents validate $($Variant.Id)' failed with exit code $LASTEXITCODE"
      }
    }
  }
  Write-Host "[build] 'agents create' smoke tests passed."
} finally {
  if ($null -eq $PreviousBytefrayRoot) {
    Remove-Item Env:BYTEFRAY_ROOT -ErrorAction SilentlyContinue
  } else {
    $env:BYTEFRAY_ROOT = $PreviousBytefrayRoot
  }
  if (Test-Path -LiteralPath $SmokeRoot) {
    Remove-Item -LiteralPath $SmokeRoot -Recurse -Force -ErrorAction Stop
  }
  if (Test-Path -LiteralPath $SmokeRoot) {
    throw "'agents create' smoke temporary root could not be removed: $SmokeRoot"
  }
}

# Exercise 'bytefray spectator' against the frozen bytefray.exe: a real
# two-entrant Active Sensing (Alpha) match, then export, verify, prepare and a
# cached prepare. Designer runs these same frozen commands with their output
# redirected, so they run redirected here too, in an isolated root whose path
# has spaces and a character (U+03A9) the Windows ANSI code page cannot encode.
$SpectatorSmokeRoot = Join-Path ([IO.Path]::GetTempPath()) ("bytefray spectator smoke " + [char]0x03A9 + " " + [Guid]::NewGuid().ToString("N"))
$PreviousBytefrayRoot = $env:BYTEFRAY_ROOT
try {
  New-Item -ItemType Directory -Force -Path $SpectatorSmokeRoot | Out-Null
  $env:BYTEFRAY_ROOT = $SpectatorSmokeRoot
  $BytefrayExe = Join-Path $DistDir "bytefray\bytefray.exe"
  $SmokeMatch = Join-Path $SpectatorSmokeRoot "runs\smoke match"
  $SmokePresentation = Join-Path $SpectatorSmokeRoot "presentation"
  $SmokeCache = Join-Path $SpectatorSmokeRoot "cache"
  $SmokeLog = Join-Path $SpectatorSmokeRoot "spectator-smoke.log"
  New-Item -ItemType Directory -Force -Path $SmokeMatch | Out-Null
  $Steps = @(
    @{ Label = "run (Active Sensing, 2 entrants)"; Args = @("run", "--ruleset", "bytefray-rules-6-alpha1", "--a-type", "v6_window_scout",
        "--b-type", "v6_watchful_keeper", "--ticks", "120", "--seed", "7",
        "--replay", (Join-Path $SmokeMatch "replay.jsonl"), "--trace", (Join-Path $SmokeMatch "trace.jsonl")) },
    @{ Label = "spectator export"; Args = @("spectator", "export", "--source", $SmokeMatch, "--out", $SmokePresentation) },
    @{ Label = "spectator verify"; Args = @("spectator", "verify", "--presentation", $SmokePresentation, "--source", $SmokeMatch) }
  )
  foreach ($Step in $Steps) {
    Write-Host "[build] 'bytefray $($Step.Label)' smoke (BYTEFRAY_ROOT=$SpectatorSmokeRoot)"
    & $BytefrayExe @($Step.Args) *>> $SmokeLog
    if ($LASTEXITCODE -ne 0) {
      throw "'bytefray.exe $($Step.Label)' failed with exit code $LASTEXITCODE; see $SmokeLog"
    }
  }
  foreach ($Expected in @($false, $true)) {
    $Status = & $BytefrayExe spectator prepare --source $SmokeMatch --cache $SmokeCache 2>> $SmokeLog |
      Select-Object -Last 1 | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $Status.status -ne "ok" -or $Status.reused -ne $Expected) {
      throw "'bytefray.exe spectator prepare' (reused=$Expected expected) returned exit $LASTEXITCODE, $($Status | ConvertTo-Json -Compress)"
    }
  }
  Write-Host "[build] 'bytefray spectator' smoke tests passed (export, verify, prepare, cached prepare)."
} finally {
  if ($null -eq $PreviousBytefrayRoot) {
    Remove-Item Env:BYTEFRAY_ROOT -ErrorAction SilentlyContinue
  } else {
    $env:BYTEFRAY_ROOT = $PreviousBytefrayRoot
  }
  if (Test-Path -LiteralPath $SpectatorSmokeRoot) {
    Remove-Item -LiteralPath $SpectatorSmokeRoot -Recurse -Force -ErrorAction Stop
  }
}

# Final proof, not just a hope, that build qualification above (GUI smoke,
# 'agents create' smoke) left no runtime-generated data root under any of
# the four distributable application trees -- both smoke blocks isolate
# their own BYTEFRAY_ROOT, so an agents\ directory appearing here means
# something still resolved the frozen app's default (beside-the-exe) data
# root instead of the isolated one.
foreach ($Artifact in $Artifacts) {
  $ResidueDir = Join-Path $DistDir "$($Artifact.Name)\agents"
  if (Test-Path $ResidueDir) {
    throw "Build qualification left runtime-generated data under $ResidueDir -- smoke tests must run against an isolated BYTEFRAY_ROOT, not the app's default data root."
  }
}

# Every file tools/installer.iss installs except this list itself, as
# "<sha256>  <path relative to the installation folder>". Setup ships it as
# bin\bytefray-files.txt. After an upgrade has installed its files, Setup deletes
# a file the previous build's list names only when this build no longer ships it
# and it is still byte-identical to what was installed -- never a folder
# recursively, so nothing else in the installation folder can be lost. The
# documents are the sources installer.iss copies into docs\
# (engine/tests/test_windows_installer_side_by_side.py keeps the two in step).
$InstalledDocuments = @("README.md", "LICENSE", "CHANGELOG.md", "docs\releases\BYTEFRAY_5_1_0_ALPHA_1_RELEASE_NOTES.md",
  "docs\releases\BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md", "docs\releases\BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.json")
$FileList = Join-Path $DistDir "bytefray-files.txt"
function Format-ListedFile([string]$Source, [string]$Installed) {
  "{0}  {1}" -f (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant(), $Installed
}
$Listed = @()
foreach ($Folder in @(@($Artifacts | ForEach-Object Name) + @("bytefray-spectator") | Where-Object { Test-Path -LiteralPath (Join-Path $DistDir $_) })) {
  $Listed += Get-ChildItem -LiteralPath (Join-Path $DistDir $Folder) -Recurse -File |
    ForEach-Object { Format-ListedFile $_.FullName ("bin\" + $_.FullName.Substring($DistDir.Length).TrimStart('\')) }
}
$Listed += Get-ChildItem -LiteralPath (Join-Path $DistDir "licenses") -Recurse -File |
  ForEach-Object { Format-ListedFile $_.FullName $_.FullName.Substring($DistDir.Length).TrimStart('\') }
$Listed += $InstalledDocuments | ForEach-Object { Format-ListedFile (Join-Path $RepoRoot $_) ("docs\" + (Split-Path -Leaf $_)) }
[IO.File]::WriteAllLines($FileList, [string[]]$Listed, [Text.UTF8Encoding]::new($false))
Write-Host "[build] Installed-file list: $($Listed.Count) files ($FileList)."

# The list -- what Setup installs -- must name exactly the pinned runtime copies, each
# with the pinned file's SHA-256: nothing after the replacement changed them.
if ($MsvcRuntimeDir) {
  $Pinned = @{}
  foreach ($Location in $Pin.locations) { $Pinned[("bin\" + $Location.Replace("/", "\")).ToLowerInvariant()] = $Pin.files.((Split-Path -Leaf $Location).ToLowerInvariant()).sha256 }
  $Runtime = @($Listed | Where-Object { (Split-Path -Leaf $_.Substring(66)) -match '^(vcruntime|msvcp|concrt|vccorlib|ucrtbase|api-ms-win-crt-)' })
  $Wrong = @($Runtime | Where-Object { $Pinned[$_.Substring(66).ToLowerInvariant()] -ne $_.Substring(0, 64) })
  if ($Runtime.Count -ne $Pinned.Count -or $Wrong.Count -gt 0) {
    throw "The installed-file list carries $($Runtime.Count) runtime files, $($Wrong.Count) not as pinned:`n  $($Wrong -join "`n  ")"
  }
  Write-Host "[build] Microsoft Visual C++ runtime: $($Runtime.Count) copies of $($Pin.version), as pinned."
}

Write-Host ""
Write-Host "[build] Success."
foreach ($Artifact in $Artifacts) {
  Write-Host ("[build] {0}: {1}" -f $Artifact.Name, (Join-Path $DistDir "$($Artifact.Name)\$($Artifact.Name).exe"))
}
if ($SpectatorExe) {
  Write-Host ("[build] bytefray-spectator: {0}" -f (Join-Path $SpectatorDir "bytefray-spectator.exe"))
} else {
  Write-Host "[build] Bytefray Spectator not staged (no -SpectatorExe); tools/installer.iss needs it."
}
Write-Host ("[build] Dist dir: {0}" -f $DistDir)
