# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ
from PyInstaller.building.api import EXE, COLLECT

# Invoke pyinstaller from repo root so "." is project root
project_root = os.path.abspath(".")
engine_src   = os.path.join(project_root, "engine", "src")
client_src   = os.path.join(project_root, "client", "src")
assets_dir   = os.path.join(project_root, "assets")
starter_agents_dir = os.path.join(engine_src, "battle_engine", "data", "starter_agents")

# Derived from the product's canonical scaffold inventory, never re-listed by
# name here -- see the equivalent block in tools/bytefray.spec for the two
# shipped defects that hand-maintained literal lists caused. The Designer
# calls battle_engine.agent_scaffold.create_agent in-process from its own
# "New Agent" workflow, so it needs the same bundled resource set the CLI
# does; deriving it keeps the two executables from drifting apart or falling
# behind a newly added template or Agent API generation.
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
script_path  = os.path.join(project_root, "app", "agent_designer.py")  # ABSOLUTE
icon_path    = os.path.join(project_root, "assets", "branding", "bytefray-icon.ico")

block_cipher = None
hiddenimports = collect_submodules("battle_engine") + collect_submodules("battle_client")
datas = []
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "assets"))
if os.path.isdir(starter_agents_dir):
    datas.append((starter_agents_dir, "battle_engine/data/starter_agents"))
for template_dir_name in agent_template_dirs:
    template_dir = os.path.join(engine_src, "battle_engine", "data", template_dir_name)
    if not os.path.isdir(template_dir):
        raise SystemExit(
            f"Scaffold template resource directory {template_dir!r} is missing; "
            "the Designer's 'New Agent' workflow would fail in the frozen build."
        )
    datas.append((template_dir, f"battle_engine/data/{template_dir_name}"))

a = Analysis(
    [script_path],
    pathex=[project_root, engine_src, client_src],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['PySide6.scripts.deploy', 'PySide6.scripts.deploy_lib', 'project_lib'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='bytefray-agent-designer',
    console=False,
    icon=icon_path,
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name='bytefray-agent-designer')
