"""The installed-build data root: tools/pyi_rth_bytefray_install.py and its record.

The Windows installer records the data folder in
``<install>/bin/bytefray-install.json``; a PyInstaller runtime hook in every
frozen executable points ``BYTEFRAY_ROOT`` at it. The record must win over an
inherited ``BYTEFRAY_ROOT`` (Bytefray 5.0's installer sets one machine-wide),
must do nothing without a record (portable and dist trees), and must refuse a
damaged record instead of quietly using some other data root.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "pyi_rth_bytefray_install.py"
INSTALLER = ROOT / "tools" / "installer.iss"
SPECS = sorted((ROOT / "tools").glob("*.spec"))


@pytest.fixture(scope="module")
def hook():
    spec = importlib.util.spec_from_file_location("pyi_rth_bytefray_install", HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # not frozen here, so the module-level apply() is skipped
    return module


def _installed_executable(root: Path) -> Path:
    executable = root / "bin" / "bytefray-agent-designer" / "bytefray-agent-designer.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"")
    return executable


def _record(root: Path, text: str, *, bom: bool = False) -> None:
    (root / "bin" / "bytefray-install.json").write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def test_loading_the_hook_outside_a_frozen_build_changes_nothing(hook, monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert not getattr(sys, "frozen", False)
    assert hook.INSTALLATION_FILE == "bytefray-install.json"


def test_no_record_means_existing_data_root_rules(hook, tmp_path):
    executable = _installed_executable(tmp_path / "portable")
    environ = {"BYTEFRAY_ROOT": "kept"}
    assert hook.apply(executable, environ) is None
    assert environ == {"BYTEFRAY_ROOT": "kept"}


@pytest.mark.parametrize("bom", [False, True])
def test_the_record_wins_over_an_inherited_root(hook, tmp_path, bom):
    install = tmp_path / "Bytefray 5.1 Alpha Ω"
    executable = _installed_executable(install)
    data_root = tmp_path / "Daten ü" / "Bytefray 5.1 Alpha"
    _record(
        install,
        json.dumps(
            {"schema": "bytefray.installation", "schema_version": 1, "product": "Bytefray 5.1 Alpha",
             "version": "5.1.0-alpha.1", "data_root": str(data_root)},
            ensure_ascii=False,
        ),
        bom=bom,
    )
    environ = {"BYTEFRAY_ROOT": r"C:\ProgramData\Bytefray"}  # what Bytefray 5.0 sets machine-wide
    assert hook.apply(executable, environ) == data_root
    assert environ["BYTEFRAY_ROOT"] == str(data_root)


@pytest.mark.parametrize(
    "text",
    [
        "{not json",
        json.dumps({"schema": "bytefray.installation", "schema_version": 2, "data_root": "C:/x"}),
        json.dumps({"schema": "other", "schema_version": 1, "data_root": "C:/x"}),
        json.dumps({"schema": "bytefray.installation", "schema_version": 1}),
        json.dumps({"schema": "bytefray.installation", "schema_version": 1, "data_root": "relative\\data"}),
        json.dumps({"schema": "bytefray.installation", "schema_version": 1, "data_root": "  "}),
        json.dumps(["not", "an", "object"]),
    ],
)
def test_a_damaged_record_stops_instead_of_guessing(hook, tmp_path, text):
    install = tmp_path / "install"
    executable = _installed_executable(install)
    _record(install, text)
    environ = {"BYTEFRAY_ROOT": "inherited"}
    with pytest.raises(RuntimeError, match="Reinstall Bytefray"):
        hook.apply(executable, environ)
    assert environ == {"BYTEFRAY_ROOT": "inherited"}


def test_installer_writes_the_record_the_hook_reads(hook):
    """tools/installer.iss's [Code] writes the record by hand; keep both sides in step."""

    source = INSTALLER.read_text(encoding="utf-8")
    assert f"InstallRecordName = '{hook.INSTALLATION_FILE}'" in source
    assert f'"schema": "{hook.INSTALLATION_SCHEMA}", "schema_version": {hook.INSTALLATION_SCHEMA_VERSION}' in source
    assert "'\"data_root\": '" in source
    assert "SaveStringsToUTF8FileWithoutBOM(ExpandConstant('{app}\\bin\\') + InstallRecordName" in source
    assert 'Type: files; Name: "{app}\\bin\\bytefray-install.json"' in source  # removed on uninstall


@pytest.mark.parametrize("spec", SPECS, ids=lambda path: path.stem)
def test_every_frozen_application_runs_the_hook_and_carries_a_version(spec: Path):
    source = spec.read_text(encoding="utf-8")
    assert re.search(r'install_hook = os\.path\.join\(project_root, "tools", "pyi_rth_bytefray_install\.py"\)', source)
    assert "runtime_hooks=[install_hook]" in source
    assert "version=executable_version_info(project_root, " in source
