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
branding_dir = os.path.join(project_root, "app", "assets", "branding")
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
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from battle_engine.agent_scaffold import TEMPLATE_DIRECTORIES_BY_API_VERSION
from tools.packaging_data import collect_data_tree

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
# Expanded per-file through the shared bytecode-filtering collector for the
# reason documented in tools/bytefray.spec's equivalent block: a
# `(directory, destination)` tuple collects the whole tree unfiltered, and
# this build runs from the live repository checkout.
#
# Only the runtime branding icon is bundled here, matching tools/bytefray.spec
# -- not the full repository-root assets/ directory, which also holds
# documentation/marketing images (a brand sheet, a horizontal logo) that no
# runtime code ever loads. The destination "assets/branding" is unchanged:
# it is the same path battle_engine.paths.get_branding_icon_path() already
# checks first, so the frozen executable resolves its window icon identically
# to before (FIND-06, V5 Alpha 1 Post-Release Hardening Audit).
datas = []
datas += collect_data_tree(branding_dir, "assets/branding")
datas += collect_data_tree(starter_agents_dir, "battle_engine/data/starter_agents")
for template_dir_name in agent_template_dirs:
    template_dir = os.path.join(engine_src, "battle_engine", "data", template_dir_name)
    if not os.path.isdir(template_dir):
        raise SystemExit(
            f"Scaffold template resource directory {template_dir!r} is missing; "
            "the Designer's 'New Agent' workflow would fail in the frozen build."
        )
    datas += collect_data_tree(
        template_dir, f"battle_engine/data/{template_dir_name}", required=True
    )

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
