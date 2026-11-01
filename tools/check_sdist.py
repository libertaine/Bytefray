"""Inspect a buildable source distribution and validate the wheel built from it."""
from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
from email.parser import Parser
from pathlib import Path, PurePosixPath


def check(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        roots = {PurePosixPath(m.name).parts[0] for m in members}
        assert len(roots) == 1, roots
        root = roots.pop()
        names = {m.name.removeprefix(root + "/") for m in members}
        required = {"pyproject.toml", "PKG-INFO", "README.md", "LICENSE",
                    "engine/src/battle_engine/__init__.py", "client/src/battle_client/__init__.py",
                    "app/__init__.py"}
        assert required <= names, required - names
        assert not any("__pycache__" in n or n.endswith((".pyc", ".pyo")) for n in names)
        assert not any(n.startswith(("tests/", "engine/tests/", "client/tests/", "tools/research/"))
                       for n in names)
        metadata_file = archive.extractfile(root + "/PKG-INFO")
        assert metadata_file is not None
        metadata = Parser().parsestr(metadata_file.read().decode())
        assert metadata["Requires-Python"] == ">=3.11"
        with tempfile.TemporaryDirectory(prefix="bytefray-sdist-") as temporary:
            work = Path(temporary)
            archive.extractall(work, filter="data")
            output = work / "wheels"
            subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(output),
                            str(work / root)], check=True)
            wheels = list(output.glob("*.whl"))
            assert len(wheels) == 1, wheels
            subprocess.run([sys.executable, str(Path(__file__).with_name("check_wheel.py")),
                            str(wheels[0])], check=True)
    print(f"sdist structure, metadata and rebuilt wheel: PASS ({path.name})")


if __name__ == "__main__":
    import glob
    paths = [Path(p) for arg in sys.argv[1:] for p in glob.glob(arg)]
    if len(paths) != 1:
        raise SystemExit("expected exactly one sdist archive")
    check(paths[0])
