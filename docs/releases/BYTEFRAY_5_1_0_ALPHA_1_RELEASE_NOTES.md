# Bytefray 5.1.0-alpha.1 — Release Notes (Windows Alpha)

Bytefray 5.1 Alpha is a preview of the next Bytefray release. It installs
beside Bytefray 5.0, which remains the stable release. Expect rough edges, and
keep using 5.0 for anything you depend on.

## What 5.1 Alpha includes

- **Classic gameplay** (`bytefray-rules-4`) — the stable Bytefray 5.0 game,
  unchanged, and still the default everywhere.
- **Active Sensing (Alpha)** (`bytefray-rules-6-alpha1`) — an experimental
  Ruleset in which agents see the arena only through what they actively sense.
  You choose it explicitly, in Agent Designer's Advanced and Development
  workflows or with `bytefray run --ruleset bytefray-rules-6-alpha1`.
- **Three Active Sensing teaching agents** — Window Scout, Watchful Keeper and
  Roaming Reacquirer — plus "personal copy" templates of each, so you can
  start your own sensing agent from a working one.
- **Improved replay workflows** — Replay History, View Last Match and the
  Pygame replay viewer's Active Sensing views.
- **Bytefray Spectator** — a separate viewer, included with the installer,
  for completed two-agent Active Sensing matches. Agent Designer's **View Last
  Match** opens such a match in Spectator, with a Broadcast view and an
  Agent A view.
- **Independent component versions** — Rulesets, the Agent API, file formats
  and Spectator each keep their own version. The
  [compatibility record](BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md) lists exactly
  which versions this release ships.

## Installing on Windows

Run `Bytefray-5.1.0-alpha.1-Windows-x64-Setup.exe`. It is for 64-bit x86
(AMD64) Windows and has been qualified on Windows 11. It does not need Python,
Godot or administrator rights: it installs for your Windows account only.

| | Bytefray 5.1 Alpha | Bytefray 5.0 (stable) |
| --- | --- | --- |
| Programs | `%LOCALAPPDATA%\Programs\Bytefray 5.1 Alpha` | `C:\Program Files\Bytefray` |
| Your agents, matches and caches | `%LOCALAPPDATA%\Bytefray 5.1 Alpha` | `C:\ProgramData\Bytefray` |
| Start Menu | **Bytefray 5.1 Alpha** folder | **Bytefray** folder |
| Uninstall entry | Bytefray 5.1 Alpha | Bytefray |

The two never share programs, data, shortcuts or uninstall entries, so
installing, upgrading or removing the Alpha does not change Bytefray 5.0. The
Alpha ignores the `BYTEFRAY_ROOT` setting that Bytefray 5.0 creates.

**Windows SmartScreen.** The Alpha installer is not code-signed. Windows may
show "Windows protected your PC"; choose **More info → Run anyway** only if you
downloaded the installer from the official Bytefray GitHub release and its
SHA-256 matches the published `SHA256SUMS`.

**Upgrading and uninstalling.** A later 5.1 Alpha installer upgrades this one
in place and keeps using the same data folder. Uninstalling (Settings → Apps)
removes the programs and shortcuts and keeps your data folder; delete it
yourself if you no longer want it. Bytefray Spectator keeps its own settings
and logs in `%APPDATA%\Godot\app_userdata\Bytefray Spectator`, which
uninstalling also leaves in place.

**Advanced.** `/BYTEFRAYDATAROOT=<folder>` on the installer's command line
chooses another data folder. `BYTEFRAY_SPECTATOR=off` makes Agent Designer use
the Pygame viewer for every match; `BYTEFRAY_SPECTATOR=<path>` points it at a
different Spectator build.

## First steps

1. Start **Bytefray Agent Designer (5.1 Alpha)** from the Start Menu. It opens
   in Classic, with the bundled starter agents.
2. To try Active Sensing, open **Advanced**, choose **Active Sensing (Alpha)**
   as the Ruleset, and run two of the teaching agents against each other.
3. Click **View Last Match**. The first time, Designer prepares a Spectator
   presentation in the background; this can take from several seconds to a
   few minutes for long matches. Later views of the same match open at once.
4. In Spectator, press **Tab** to switch between Broadcast and Agent A, and
   **H** for the other keys.

## Known limitations

- Active Sensing (Alpha) is experimental; its rules may change in a later
  Ruleset. It is not offered in Designer's Simple workflow, evaluations or
  tournaments.
- Spectator presents only completed two-agent Active Sensing matches, with
  two perspectives: Broadcast and Agent A. Every other match — Classic, three
  agents, tournaments, Replay History — opens in the Pygame replay viewer.
- Preparing a match for Spectator the first time is slow, and the time grows
  quickly with match length.
- Human comprehension evaluation of Active Sensing is planned for 5.2.
- This installer is for Windows AMD64 only. Linux packaging is qualified
  separately, and native Ubuntu on Xorg is not qualified.
- The standalone sensing demonstration generators are available from source
  only.
- The installer and programs are not code-signed (see SmartScreen above).
- Accessibility has not been reviewed for this Alpha. Spectator is operated
  from the keyboard.

See the [compatibility record](BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md) for
the complete list of supported and unsupported combinations.
