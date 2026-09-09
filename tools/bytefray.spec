# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
engine_src = os.path.join(project_root, "engine", "src")
client_src = os.path.join(project_root, "client", "src")
script_path = os.path.join(engine_src, "battle_engine", "__main__.py")
pmars_dir = os.path.join(project_root, "pmars", "windows")
icon_path = os.path.join(project_root, "assets", "branding", "bytefray-icon.ico")
branding_dir = os.path.join(project_root, "app", "assets", "branding")
starter_agents_dir = os.path.join(engine_src, "battle_engine", "data", "starter_agents")

# The scaffold template directories are READ FROM THE PRODUCT's own canonical
# inventory rather than re-listed here by name. This spec used to enumerate
# them literally, which made the frozen build's resource list a second,
# hand-maintained copy of a set the product already defines -- and it fell
# behind that set twice: once when the "annotated" template was added, and
# again when the Agent API v2 template pair was, each time shipping an
# executable whose `bytefray agents create` failed for the new template with
# "Agent template resource directory not found" while source checkouts and
# installed wheels both worked. The wheel never had this failure mode because
# pyproject.toml's package-data is the glob `data/**/*`, which needs no
# per-directory maintenance. Deriving the list restores that property here:
# adding a template or an Agent API generation to
# `agent_scaffold.TEMPLATE_DIRECTORIES_BY_API_VERSION` now packages it
# automatically, and a missing directory fails the build loudly instead of
# silently producing an executable that cannot scaffold.
if engine_src not in sys.path:
    sys.path.insert(0, engine_src)
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION

agent_template_dirs = sorted(
    {
        directory
        for templates in TEMPLATE_DIRECTORIES_BY_API_VERSION.values()
        for directory in templates.values()
    }
)
# pmars/windows only ships a Windows pmars.exe; battle_engine.pmars only ever
# looks under a "pmars/windows" resource subdirectory when os.name == "nt"
# (see _candidate_directories), so bundling it on other platforms would be
# dead weight, not a working redcode94 backend. pMARS itself is unrelated to
# Agent API v2 matches (the `run --mode redcode94` backend only); it is
# deliberately not vendored for Linux (no redistributable Linux binary is
# checked into this repo -- see tools/build_pmars_linux.sh and
# .github/workflows/linux-pmars-build.yml, which build it from a
# separately-downloaded, license-verified source archive and do not persist
# the result). A Linux build's PMARS_CMD/PATH fallback (battle_engine/
# pmars.py) still applies unchanged for a user who supplies their own binary.
datas = []
if sys.platform == "win32" and os.path.isdir(pmars_dir):
    datas.extend(
        [
            (os.path.join(pmars_dir, "pmars.exe"), "pmars/windows"),
            (os.path.join(pmars_dir, "COPYING"), "pmars/windows"),
        ]
    )
if os.path.isdir(branding_dir):
    datas.append((branding_dir, "assets/branding"))
if os.path.isdir(starter_agents_dir):
    datas.append((starter_agents_dir, "battle_engine/data/starter_agents"))
for template_dir_name in agent_template_dirs:
    template_dir = os.path.join(engine_src, "battle_engine", "data", template_dir_name)
    if not os.path.isdir(template_dir):
        raise SystemExit(
            f"Scaffold template resource directory {template_dir!r} is missing; "
            "`bytefray agents create` would fail in the frozen build."
        )
    datas.append((template_dir, f"battle_engine/data/{template_dir_name}"))

hiddenimports = (
    collect_submodules("battle_engine")
    + collect_submodules("battle_client")
    + collect_submodules("app")
)

a = Analysis(
    [script_path],
    pathex=[project_root, engine_src, client_src],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="bytefray", console=True, icon=icon_path)
coll = COLLECT(exe, a.binaries, a.datas, name="bytefray")
