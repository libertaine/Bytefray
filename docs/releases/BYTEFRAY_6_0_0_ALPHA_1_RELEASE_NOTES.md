# Bytefray 6.0.0-alpha.1 — Release Notes (Windows Alpha)

> **Draft for the release candidate.** Not yet qualified or published. The
> installer qualification (gate G6), the first-use pass (G7) and the hashes
> below are completed before publication, and this banner is removed then.

**Download this:** `Bytefray-6.0.0-alpha.1-Windows-x64-Setup.exe` — the only
file a Windows user needs. Everything else on the release page (the Python
wheel and source distribution, `SHA256SUMS`, third-party notices and the
compliance source archives) is for Python users, verification and licence
compliance.

## What 6 Alpha is

Bytefray 6.0.0-alpha.1 is a deliberately small Alpha. It **removes** more than
it adds, so read this before installing:

- **Classic is gone from this release.** The Classic Ruleset
  (`bytefray-rules-4`) and its ten starter agents were retired after
  5.1.0-alpha.1 ([decision record](CLASSIC_RULESET_RETIREMENT.md)). Active
  Sensing (Alpha) (`bytefray-rules-6-alpha1`) is the only Ruleset. Classic
  replays, results and evaluations stay readable here, but cannot be run.
  Removing an executable Ruleset is why this is version 6.0.
- **Keep 5.1 Alpha if you want Classic.** 6 Alpha installs *beside*
  Bytefray 5.0 and 5.1 Alpha and changes neither of them. 5.1 Alpha remains
  the release that runs Classic, and 5.0.0 the stable release.

What it adds or fixes:

- **A practice opponent.** `v6_practice_hunter` (Practice Hunter) searches
  with `SENSE`, takes over the cores it finds and repairs its own. It is the
  default opponent for `bytefray agents test` and Designer's first matchup.
  The three teaching agents (Window Scout, Watchful Keeper, Roaming
  Reacquirer) are unchanged; they each show one idea and do not fight each
  other. The practice opponent makes no balance claim.
- **`bytefray agents validate` works for sensing agents.** It no longer
  rejects `SENSE` unless `--ruleset` is passed.
- **One arena size.** New matches from `bytefray run`, `bytefray agents test`,
  `bytefray tournament`, `agents validate` and Designer use a 512-cell arena,
  the size `agents evaluate` already used. Every result prints the arena. Pass
  `--arena 4096` for the old command-line default; saved matches and recorded
  evaluations are unchanged.
- **Replay History stability** ([issue #7](https://github.com/libertaine/Bytefray/issues/7)):
  closing Replay History no longer waits on a worker thread's signals, which
  could hang. The Designer GUI tests now also run on Windows.
- **First-run fixes.** `agents validate` and `agents test` find the bundled
  agents even as the first command in a new data folder; the development test
  names its opponent instead of calling it "reference"; Agent Lab reads
  current (schema-2) traces ([#10](https://github.com/libertaine/Bytefray/issues/10),
  [#11](https://github.com/libertaine/Bytefray/issues/11)).

Component versions are listed in the
[6.0.0-alpha.1 compatibility record](BYTEFRAY_6_0_0_ALPHA_1_COMPATIBILITY.md).

## Installing on Windows

Run `Bytefray-6.0.0-alpha.1-Windows-x64-Setup.exe`. It is for 64-bit x86
(AMD64) Windows 11. It does not need Python, Godot or administrator rights: it
installs for your Windows account only.

| | Bytefray 6 Alpha | Bytefray 5.1 Alpha | Bytefray 5.0 (stable) |
| --- | --- | --- | --- |
| Programs | `%LOCALAPPDATA%\Programs\Bytefray 6 Alpha` | `%LOCALAPPDATA%\Programs\Bytefray 5.1 Alpha` | `C:\Program Files\Bytefray` |
| Your agents, matches and caches | `%LOCALAPPDATA%\Bytefray 6 Alpha` | `%LOCALAPPDATA%\Bytefray 5.1 Alpha` | `C:\ProgramData\Bytefray` |
| Start Menu | **Bytefray 6 Alpha** folder | **Bytefray 5.1 Alpha** folder | **Bytefray** folder |
| Uninstall entry | Bytefray 6 Alpha | Bytefray 5.1 Alpha | Bytefray |

The three never share programs, data, shortcuts or uninstall entries.
Installing, upgrading or removing 6 Alpha does not change 5.0 or 5.1 Alpha,
and Setup refuses installation or data folders that overlap theirs.

**Your data folder starts empty.** Nothing is copied, moved or migrated from
5.0 or 5.1 Alpha. To use an agent you wrote earlier, copy its folder into
`%LOCALAPPDATA%\Bytefray 6 Alpha\agents\` yourself. Agents written for Classic
run under Active Sensing, but their contact finding never engages, so they
mostly stand still.

**Microsoft Visual C++ runtime terms.** Bytefray includes Microsoft Visual C++
runtime files redistributed under Microsoft's Visual Studio Community 2026
terms, which require everyone who installs them to agree to terms that protect
them. Setup shows those terms on its License page and continues only after you
select **I accept the agreement**. They apply only to the Microsoft files:
Bytefray stays under the MIT License and every other component under its own
license. An unattended installation (`/SILENT` or `/VERYSILENT`) shows no
pages, so it is refused unless it also passes
`/ACCEPTMICROSOFTRUNTIMETERMS=BYTEFRAY-6.0-MSVC-RUNTIME-TERMS-1`, which accepts
those terms on behalf of the person the installation is for.

**Windows SmartScreen.** The installer is not code-signed. Windows may show
"Windows protected your PC"; choose **More info → Run anyway** only if you
downloaded the installer from the official Bytefray GitHub release and its
SHA-256 matches the published `SHA256SUMS`.

**Upgrading and uninstalling.** A later 6 Alpha installer upgrades this one in
place and keeps the same data folder. Installing an older 6 Alpha build over a
newer one is refused. Uninstalling (Settings → Apps) removes the programs and
shortcuts and keeps your data folder.

**Advanced.** `/BYTEFRAYDATAROOT=<folder>` chooses another data folder.
`BYTEFRAY_SPECTATOR=off` makes Agent Designer use the Pygame viewer;
`BYTEFRAY_SPECTATOR=<path>` points it at a different Spectator build.

## First steps

1. Start **Bytefray Agent Designer (6 Alpha)** from the Start Menu. Its first
   matchup is a teaching agent against the practice opponent.
2. Click **Run Match**, then **View Last Match** to watch it in the bundled
   Bytefray Spectator.
3. Create your own agent from a template, then **Validate** and **Test** it on
   the Agent Development tab.

From the command line, the [README quick start](../../README.md#quick-start)
runs a demonstration match, exports it for Spectator, and creates, validates
and tests an agent.

## Known limitations

- **Gameplay is experimental.** Active Sensing (Alpha) is the only Ruleset and
  is labelled experimental. Decisive matches are short (often under 30 ticks
  at 512 cells), and defending a core has not yet been shown to change
  outcomes: once an attacker finds a core it usually takes it.
- **The practice opponent is for practice.** It has no balance claim. It
  beats the teaching agents, and a simple sensing agent of your own can beat
  it.
- **The teaching agents do not fight each other.** Two of them in one match
  usually tie with nothing written.
- **The 512-cell default changes command-line results.** Scripts that relied
  on `bytefray run`'s or `bytefray agents test`'s earlier 4,096-cell default
  must pass `--arena 4096`.
- **`bytefray agents test` can wait for an agent's child processes.** If an
  agent starts another process that keeps running, the test finishes its
  match but the command returns only when that process exits. Agents are
  trusted local code; the existing hang and timeout containment is unchanged.
- **`bytefray run` writes no trace unless you pass `--trace`.** Without one,
  the match cannot be exported to Spectator.
- **Bytefray Spectator is unchanged** (0.1.0-alpha.1, the build 5.1 Alpha
  bundled). Its Tab key hint is wrong, View Last Match shows no progress while
  a presentation is prepared, and Replay History, tournaments and Advanced
  "View Replay" open in the Pygame viewer.
- The installer and programs are not code-signed (see SmartScreen above).
- Windows 11 AMD64 only. Linux and macOS are not qualified.

## Spectator provenance

The bundled `bytefray-spectator.exe` (SHA-256
`8a3bd1a48430a0edd1faf8ca5c5b287ed1ecd06975c4e683f273562d428fd602`) is the
build 5.1 Alpha shipped, made from Spectator commit `14089a7`. That commit is
not on GitHub; its source tree (`9563b1b3de84a387cccd40bf911dfed59ab70e36`) is
byte-identical to the public commit
[`f62b0cb`](https://github.com/libertaine/Bytefray-Spectator/commit/f62b0cb30a1b8dc95bfc58c76be6637c4ac3bbbc)
on `main`.

## Hashes

Filled in from the release build (gate G5) before publication; `SHA256SUMS` on
the release page is authoritative.

| File | SHA-256 |
| --- | --- |
| `Bytefray-6.0.0-alpha.1-Windows-x64-Setup.exe` | *(from the release build)* |
| `bytefray-6.0.0a1-py3-none-any.whl` | *(from the release build)* |
| `bytefray-6.0.0a1.tar.gz` | *(from the release build)* |
