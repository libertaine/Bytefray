# Native Ubuntu confirmation of the M2-5 source candidate

**M2-5: PASS WITH CONDITIONS. Native Ubuntu is not yet qualified.**
M2-6 remains paused/HOLD pending actual human evaluation. Run only these bounded
confirmation checks; do not start the full M2-5 campaign. Preserve failures,
process exits and environment evidence without changing source or fixtures.

From an existing Bytefray clone, fetch only the new branch and create a separate
checkout. Replace the destination if that directory already exists; do not reset
or reuse another working tree. Use the exact published commit from the handoff
as EXPECTED_COMMIT before continuing.

```bash
set -euo pipefail
EXPECTED_COMMIT='<published commit from the publication handoff>'
git fetch origin refs/heads/v6-alpha1-m2-5-qualified:refs/remotes/origin/v6-alpha1-m2-5-qualified
test "$(git rev-parse refs/remotes/origin/v6-alpha1-m2-5-qualified)" = "$EXPECTED_COMMIT"
git worktree add --detach ../bytefray-m2-5-ubuntu "$EXPECTED_COMMIT"
cd ../bytefray-m2-5-ubuntu
test "$(git rev-parse HEAD)" = "$EXPECTED_COMMIT"
test "$(git rev-parse HEAD^)" = 10c3530f035335b89716d5bda7ce138440767a71
git diff --exit-code
git diff --cached --exit-code
```

Verify the full source and inherited fixture manifest before installing or
running anything. Existing attributes intentionally materialize five inherited
PowerShell scripts with CRLF even on Linux; the hashes below are raw working
bytes, so do not normalize them. The manifest itself is protected by the
verified commit identity.

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
m = json.loads(Path('docs/v6/V6_ALPHA_M2_5_SOURCE_MANIFEST_01.json').read_text())
assert len(m['source_sha256']) == 1249
for group in ('source_sha256', 'portable_fixture_sha256'):
    for name, expected in m[group].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
    print(group, len(m[group]), 'verified')
PY
```

Use native Ubuntu Python 3.10-3.14. The WSL qualification used Python 3.12;
prefer native Python 3.12 where available for the closest comparison. These
commands use the selected system `python3`; record its version. Install Qt X11
runtime libraries following the repository's existing Linux GUI workflow:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv libegl1 libgl1 libxkbcommon-x11-0  \
  libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1  \
  libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[replay,designer,dev]'
```

Dependencies resolve from the supported extras, rather than silently claiming
an exact historical dependency environment. Record their actual versions. For
comparison, retained WSL evidence used pygame-ce 2.5.8 and PySide6 6.12.0;
Windows used pygame-ce 2.5.8 and PySide6 6.11.2.

Log in at the physical Ubuntu desktop using **Ubuntu on Xorg** (or another
native X11 session). Run from a terminal inside that desktop, with its existing
DISPLAY and XAUTHORITY. A Wayland session running XWayland is a different scope.
Do not invent DISPLAY=:0 or use WSLg, Xvfb, offscreen Qt, or SDL dummy drivers
for native confirmation. If no native X11 login is offered, record that gate
as untested and obtain a suitable desktop before continuing.

```bash
printf 'session=%s display=%s\n' "${XDG_SESSION_TYPE:-}" "${DISPLAY:-}"
test "${XDG_SESSION_TYPE:-}" = x11
test -n "${DISPLAY:-}"
unset SDL_VIDEODRIVER SDL_AUDIODRIVER QT_QPA_PLATFORM WAYLAND_DISPLAY
export QT_QPA_PLATFORM=xcb SDL_VIDEODRIVER=x11
export PYTHONDONTWRITEBYTECODE=1
export BYTEFRAY_ROOT="$(mktemp -d "$HOME/bytefray-m2-5-data.XXXXXX")"
mkdir -p .pytest-tmp
confirmation_id="$(date -u +%Y%m%dT%H%M%SZ)"
confirmation_out="$(mktemp -d "$HOME/bytefray-m2-5-confirmation.XXXXXX")"
{
  git rev-parse HEAD
  uname -a
  cat /etc/os-release
  printf 'session=%s display=%s\n' "$XDG_SESSION_TYPE" "$DISPLAY"
  python --version
  python -m pip freeze
} > "$confirmation_out/environment.txt"
```

Run the focused 25-case PD-1/calendar selection in fresh processes for UTC,
Tokyo and canonical Indianapolis. Resolve the Qt timezone and offset first;
expected September offsets are 0, +32400 and -14400 seconds, respectively.
The environment passed to Python sets both Python's and Qt's local calendar.
Each command logs through `tee`; `pipefail` preserves failure. A timeout or
crash is a failed/incomplete confirmation, not permission to exclude a node.

```bash
for zone in UTC Asia/Tokyo America/Indiana/Indianapolis; do
  label="${zone//\//_}"
  TZ="$zone" python - <<'PY'
from PySide6.QtCore import QDate, QDateTime, QTime, QTimeZone
z = QTimeZone.systemTimeZone()
d = QDateTime(QDate(2026, 9, 11), QTime(12, 0), z)
print(z.id().data().decode(), d.offsetFromUtc())
PY
  TZ="$zone" timeout 180s python -m pytest \
    tests/test_v5_replay_history_qualification.py -m gui -k 'date or calendar' \
    --basetemp=".pytest-tmp/${confirmation_id}_${label}" \
  --junitxml="$confirmation_out/${label}.xml" \
  2>&1 | tee "$confirmation_out/${label}.log"
done
```

Then run this small native X11 startup check and the focused M2-4 semantic
checks in separate processes. The startup check is only startup/quit coverage.
The semantic module's renderer tests use offscreen fixtures internally, so only
the following non-GUI partition is requested here; it is semantic evidence,
not native workflow qualification.

```bash
timeout 90s python -m pytest client/tests/test_linux_pygame_smoke.py::test_pygame_renders_replay_and_exits_on_quit -m gui \
  --basetemp=".pytest-tmp/${confirmation_id}_pygame" \
  --junitxml="$confirmation_out/pygame.xml" 2>&1 | tee "$confirmation_out/pygame.log"
timeout 180s python -m pytest client/tests/test_v6_alpha_m2_4_views.py -m 'not gui' \
  --basetemp=".pytest-tmp/${confirmation_id}_views" \
  --junitxml="$confirmation_out/views.xml" 2>&1 | tee "$confirmation_out/views.log"
```

For visible native confirmation, open the committed Keeper seat-A replay:

```bash
body=docs/v6/evidence/m2_2/keeper/seat_A
python -m battle_engine replay --renderer pygame --replay "$body/replay.jsonl" \
  --trace "$body/trace.jsonl" --result "$body/result.json" --perspective A \
  2>&1 | tee "$confirmation_out/keeper-viewer.log"
```

Record opened artifact/hash, viewer PID, visible A/B/Omni transitions (keys
2/3/1), Home/End, backward steps, Help and clean Escape/exit. Repeat with
`docs/v6/evidence/m2_3/reacquirer/seat_B`. Assess focus and responsiveness on the
actual Ubuntu desktop. Record waits honestly: retained Windows selected loads
were about 12.2 seconds and perspective switches about 6 seconds (about 4 seconds
on WSL), with Windows "Not Responding" during measured C2 switches. These are
limitations, not native Ubuntu measurements or acceptance thresholds.

To check actual History handoff, copy the four manifest-bound public bodies to
the fresh data root, then start Designer:

```bash
mkdir -p "$BYTEFRAY_ROOT/runs"
for seat in A B; do
  cp -R "docs/v6/evidence/m2_2/keeper/seat_$seat" "$BYTEFRAY_ROOT/runs/keeper_$seat"
  cp -R "docs/v6/evidence/m2_3/reacquirer/seat_$seat" "$BYTEFRAY_ROOT/runs/reacquirer_$seat"
done
python -m battle_engine design 2>&1 | tee "$confirmation_out/designer.log"
```

Use History > Replay History, refresh, select each copied occurrence and Open
Replay. Verify the selected replay is actually opened by the viewer, its PID,
hash and clean exit; Designer startup or a launch signal alone is insufficient.
Open the sensing guide through the Development UI, check Space/PageDown/Escape,
focus return, mouse Close and reopening. Record missing keyboard alternatives
and any host/window-manager focus assistance. This is technical confirmation;
do not conduct participant evaluation or infer M2-6 closure.

No ignored Windows data is needed for these focused tests or the four public
replays: all 20 portable fixture files are inherited and manifest-bound. Exact
reproduction of the historical **I3/C2 performance workload** additionally needs
the retained Keeper Development Test replay, trace and result. The minimum is:

| File | SHA-256 |
| --- | --- |
| `replay.jsonl` | `98edb90ddda6d5d28b3ff76431d6c1ed9e4b7f792b48144173408fc17d9305de` |
| `trace.jsonl` | `47268aa8139bf676bbfa050d2c9f7ec21195a0ac047e68cb8e7bc208cbd9c7e9` |
| `result.json` | `62003072f4280d1ed9a260bf67bdc98a3bed320ed6ee29c5f346b311dde4553f` |

A local three-file, hash-verified transfer archive was prepared outside Git;
it was not uploaded and requires separate review before any public upload.
Its `SHA256SUMS` verifies after extraction with `sha256sum -c SHA256SUMS` inside
its I3 directory. No summary sidecar is needed for this viewer. The archive
omits harnesses, logs, E9 inputs and participant records. It does not reproduce
the entire historical campaign or all its generated workload inputs.

Return the verified commit/manifest, OS/dependency/display identities, resolved
timezones, JUnit/logs, workflow artifact identities, focus and exit observations,
any failures and remaining gates. Preserve original evidence and stop on source
drift, a crash/hang or a new integrity failure. Do not rerun the full campaign
or modify assertions to obtain a pass.
