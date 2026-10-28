# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
engine_src = os.path.join(project_root, "engine", "src")
script_path = os.path.join(engine_src, "battle_engine", "cli.py")
icon_path = os.path.join(project_root, "assets", "branding", "bytefray-icon.ico")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from tools.packaging_data import collect_data_tree, collect_starter_agents
from tools.windows_version_info import executable_version_info

# Installed builds take their data root from the installer's record; see the hook.
install_hook = os.path.join(project_root, "tools", "pyi_rth_bytefray_install.py")

# See tools/bytefray.spec for why starter_agents is expanded per-file through
# the shared bytecode-filtering collector instead of being passed as a
# directory tuple.
datas = []
datas += collect_starter_agents(engine_src, "battle_engine/data/starter_agents")

a = Analysis(
    [script_path],
    pathex=[project_root, engine_src],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("battle_engine"),
    hookspath=[],
    runtime_hooks=[install_hook],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="bytefray-cli", console=True, icon=icon_path,
    version=executable_version_info(project_root, "bytefray-cli", "Bytefray legacy match command"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="bytefray-cli")
