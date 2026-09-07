# Bytefray Linux installation

Bytefray supports Python 3.10 through 3.14 and offers two Linux distribution
paths: a self-contained binary archive (no local Python required) and a
Python wheel/source install. No AppImage, Debian, or Flatpak artifact is
provided. (See [README.md](../README.md#-downloads) for the current release;
exact filenames below track that latest tag as later versions ship.)

## Self-contained Linux binary distribution

Download `bytefray-4.0.0-rc2-linux-x86_64.tar.gz` from the release and
extract it; do not copy only the top-level executables, since their
adjacent shared libraries, Qt plugins, and resources are required:

```bash
tar -xzf bytefray-4.0.0-rc2-linux-x86_64.tar.gz
./bytefray/bytefray --version
```

This produces four self-contained onedir applications (`bytefray`,
`bytefray-cli`, `bytefray-agent-designer`, `bytefray-replay-viewer`); no
local Python interpreter, `pip`, or virtual environment is required. As with
the Windows portable ZIP, each application defaults its writable data to its
own directory beside its executable unless `BYTEFRAY_ROOT` is set once to a
shared directory before launching any of them.

**Official release-build baseline.** The frozen artifact is built on
**Ubuntu 24.04 LTS** (not a newer or arbitrary Ubuntu release) and qualified
byte-for-byte, unrebuilt, on **Ubuntu 26.04**. The measured maximum required
glibc symbol version is `GLIBC_2.38`. Ubuntu 22.04 LTS (glibc 2.35) and
Debian 12 "Bookworm" (glibc 2.36) are **not** claimed as compatible, and no
universal Linux compatibility is claimed; only the two Ubuntu releases
actually tested are called out above. See
[`docs/research/v4/V4_RC2_LINUX_RELEASE_BASELINE_QUALIFICATION.md`](research/v4/V4_RC2_LINUX_RELEASE_BASELINE_QUALIFICATION.md)
for the full qualification record.

## Python wheel installation

Advanced/development users can instead install the wheel or an editable
source checkout on a supported Python version. Create an isolated
environment and install the wheel:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ./bytefray-4.0.0rc2-py3-none-any.whl
```

The core install supports native matches and headless replay. Optional desktop
dependencies are separate:

```bash
python -m pip install 'bytefray[replay]'    # pygame-ce replay viewer
python -m pip install 'bytefray[designer]'  # PySide6 Agent Designer
```

PySide6 and pygame-ce are not required for the core CLI. Replay rendering
uses [pygame-ce](https://pyga.me/), a maintained, actively-released fork of
Pygame, through the standard `pygame` Python namespace -- application and
agent code continues to `import pygame` unchanged. pygame-ce publishes
binary wheels for current CPython releases (including 3.14) promptly, so a
supported Python normally installs `replay`/`gui` without needing SDL2
development headers or a local compiler; classic Pygame's Linux wheel
coverage can lag a new CPython release, which forces pip to fall back to a
source build that fails without `sdl2-config` and the SDL2 dev packages
installed. CI validates pygame-ce and Designer startup under X11/Xvfb across
the package's minimum and current-generation Python versions. That is not
full visible/input GUI validation, and native Wayland remains unvalidated,
so the Linux wheel should still be treated as headless-first.

## Writable data and starter agents

`BYTEFRAY_ROOT` selects the writable data root. When it is unset, an installed
Linux wheel uses `$XDG_DATA_HOME/bytefray`, or `~/.local/share/bytefray` when
`XDG_DATA_HOME` is unset. Recognized source and editable checkouts continue to
use the repository root.

Packaged starter manifests are read-only resources. `bytefray agents` initializes
missing Runner, Writer, Seeker, and Spiral manifests before listing the catalog,
without overwriting user files:

```bash
bytefray agents
```

With no `--replay` option, matches write
`<data-root>/runs/_loose/replay.jsonl` and its sibling `summary.json`. An
explicit relative `--replay` path remains relative to the current working
directory; an explicit absolute path is preserved. The canonical summary is
always beside the selected replay.

## Headless operation

```bash
bytefray --help
bytefray run --ticks 500 --quota 2 --a-type writer --b-type runner
bytefray replay --replay ~/.local/share/bytefray/runs/_loose/replay.jsonl \
  --renderer headless
```

The wheel does not bundle a Linux pMARS executable or select the repository's
Windows PE executables on Linux. `PMARS_CMD` remains authoritative and an
executable `pmars` may be discovered through `PATH`. Upstream supports a
console-only build, but the audited Ubuntu 0.9.5 package is compiled with X11;
`-b` means brief output and does not disable its display. Bytefray now provides a
pinned, experimental build script for the authoritative pMARS 0.9.5 source in
`tools/build_pmars_linux.sh`; it produces a libc-only console executable without
patching or modifying the supplied source. Linux Redcode operation still requires
a user-provided executable and is not part of wheel validation.
Any future bundled pMARS build must comply with GPL-2.0-or-later distribution
requirements, including the license notice and corresponding source offer or
delivery; the current wheel deliberately contains neither pMARS nor its source.
The corresponding-source and separately licensed documentation layout for a
future binary release remains a release-policy task; see `tools/pmars/README.md`.

Select one console-only executable path without fixed arguments:

```bash
PMARS_CMD=/absolute/path/to/pmars bytefray run --mode redcode94 \
  --red-a path/to/a.red --red-b path/to/b.red
```
