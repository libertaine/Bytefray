# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
engine_src = os.path.join(project_root, "engine", "src")
script_path = os.path.join(engine_src, "battle_engine", "cli.py")
pmars_dir = os.path.join(project_root, "pmars", "windows")
icon_path = os.path.join(project_root, "assets", "branding", "bytefray-icon.ico")
starter_agents_dir = os.path.join(engine_src, "battle_engine", "data", "starter_agents")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from tools.packaging_data import collect_data_tree

# See tools/bytefray.spec for why pmars/windows is bundled only on Windows,
# and for why starter_agents is expanded per-file through the shared
# bytecode-filtering collector instead of being passed as a directory tuple.
datas = []
if sys.platform == "win32" and os.path.isdir(pmars_dir):
    datas.extend(
        [
            (os.path.join(pmars_dir, "pmars.exe"), "pmars/windows"),
            (os.path.join(pmars_dir, "COPYING"), "pmars/windows"),
        ]
    )
datas += collect_data_tree(starter_agents_dir, "battle_engine/data/starter_agents")

a = Analysis(
    [script_path],
    pathex=[project_root, engine_src],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("battle_engine"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="bytefray-cli", console=True, icon=icon_path)
coll = COLLECT(exe, a.binaries, a.datas, name="bytefray-cli")
