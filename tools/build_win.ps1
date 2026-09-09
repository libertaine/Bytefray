param([string]$Mode = "Release")

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
Run-PyMod -Module pip -Args @("install","--upgrade","pip","wheel")
Run-PyMod -Module pip -Args @("install", "-e", ".[replay,designer,windows-build]")

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

# Verify no Python bytecode/cache reached any distributable tree.
#
# This build runs from the live repository checkout, and the engine imports
# agent modules out of battle_engine/data at runtime, so CPython writes
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
# silently shipped without it -- first battle_engine/data/agent_template
# itself, then agent_template_annotated, then both Agent API v2 template
# directories, whose absence failed `agents create --api-version 2` with
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
$SmokeVariants = @(
  @{ Id = 'smoke_agent';              CreateArgs = @();                                                     Validate = $false }
  @{ Id = 'smoke_agent_annotated';    CreateArgs = @('--template', 'annotated');                            Validate = $false }
  @{ Id = 'smoke_agent_v2';           CreateArgs = @('--api-version', '2');                                 Validate = $true  }
  @{ Id = 'smoke_agent_v2_annotated'; CreateArgs = @('--api-version', '2', '--template', 'annotated');      Validate = $true  }
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
    if ($Variant.Validate) {
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

Write-Host ""
Write-Host "[build] Success."
foreach ($Artifact in $Artifacts) {
  Write-Host ("[build] {0}: {1}" -f $Artifact.Name, (Join-Path $DistDir "$($Artifact.Name)\$($Artifact.Name).exe"))
}
Write-Host ("[build] Dist dir: {0}" -f $DistDir)
