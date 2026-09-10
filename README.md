# Bytefray

<p align="center">
  <img src="assets/branding/bytefray-logo-horizontal.png" alt="Bytefray logo" width="420">
</p>

Bytefray is a deterministic programmable-agent arena: write Python agents that
move, observe, defend their cores, and compete over shared memory. Inspired by
Core War, it combines a shared-memory strategy game with an Agent Designer,
interactive Replay Viewer, and reproducible evaluation and tournament tools.

[![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Bytefray 5 Alpha

**[Bytefray 5.0.0 Alpha 1 is available](https://github.com/libertaine/Bytefray/releases/tag/b5.0.0-alpha1).**
Bytefray 5 is the current development generation, with a qualified Alpha 1
release focused on approachable agent strategies and authoring tools.

| Product version | Release tag | Stable gameplay ruleset |
|---|---|---|
| `5.0.0a1` | `b5.0.0-alpha1` | `bytefray-rules-4` |

V5 builds on the stable V4 gameplay foundation. The product version does not
introduce a `bytefray-rules-5` ruleset.

## What's new in Bytefray 5

- **Four educational starters** teach regional objective pressure, search and
  contact memory, core repair, and multi-process teamwork.
- **Agent API v2 authoring** includes blank and annotated templates, with a
  guide that connects the API to useful strategies.
- **Parameter schemas and presets** declare typed, validated settings that
  flow into agent execution and result/replay metadata.
- **Designer controls** are generated from those schemas, show effective
  values, and offer an explicit **Randomize Seed** action.
- **Deterministic, replayable matches** make it practical to compare changes
  while keeping the seed and configuration fixed.
- **Safe starter refresh** updates recognized pristine bundled copies and
  preserves your customized agents.
- **Packaging improvements** harden scaffold resources, packaged contents,
  Windows installed workflows, and Linux wheel/source installation.

## Quick Start

### Windows

Download **[Bytefray-Setup-5.0.0a1.exe](https://github.com/libertaine/Bytefray/releases/download/b5.0.0-alpha1/Bytefray-Setup-5.0.0a1.exe)**
from the [Alpha 1 release](https://github.com/libertaine/Bytefray/releases/tag/b5.0.0-alpha1).
Run the AMD64/x64 installer with administrative permission, then open
**Bytefray Agent Designer** from the Start Menu. Select V5 starters, choose a
seed, and run a match; open its replay to inspect what happened.

The installer puts the four applications under
`C:\Program Files\Bytefray\bin` and uses `%ProgramData%\Bytefray` for writable
data. It does not modify `PATH`. For the CLI in PowerShell:

```powershell
& 'C:\Program Files\Bytefray\bin\bytefray\bytefray.exe' --help
```

Use that executable path in place of `bytefray` in the examples below.
The release's four individual `.exe` assets require their matching adjacent
runtime directories and resources; use the installer for complete applications.

### Python

Use Python **3.10–3.14** on Windows or Linux. Download
[`bytefray-5.0.0a1-py3-none-any.whl`](https://github.com/libertaine/Bytefray/releases/download/b5.0.0-alpha1/bytefray-5.0.0a1-py3-none-any.whl),
create and activate a virtual environment, then install the downloaded wheel:

```bash
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` in Windows PowerShell, or
`source .venv/bin/activate` on Linux (use `python3` to create the environment
if needed). From the directory containing the wheel:

```bash
python -m pip install ./bytefray-5.0.0a1-py3-none-any.whl
bytefray --version
```

The core CLI requires only PyYAML. To add the Designer and graphical replay
viewer, install the same local wheel with its optional extras:

```bash
python -m pip install "./bytefray-5.0.0a1-py3-none-any.whl[replay,designer]"
bytefray design
```

These commands install the GitHub release asset. The
[`bytefray-5.0.0a1.tar.gz`](https://github.com/libertaine/Bytefray/releases/download/b5.0.0-alpha1/bytefray-5.0.0a1.tar.gz)
source distribution is also available. Alpha 1's Linux qualification covers
wheel and source installation on Ubuntu 24.04 under WSL2; its release inventory
contains no self-contained Linux binary archive. macOS is not a supported or
tested distribution target.

## Try a Match

Bundled starters appear automatically in your writable agent catalog:

```bash
bytefray agents
bytefray run --a-type v5_region_attacker --b-type v5_core_defender --seed 42 --ticks 200 --replay runs/v5-demo/replay.jsonl
bytefray replay --replay runs/v5-demo/replay.jsonl --renderer headless
```

An API-v2 roster defaults to `bytefray-rules-4`; no ruleset flag is needed.
With the replay extra installed, use `--renderer pygame` for interactive
playback. The Designer also provides match configuration and replay opening.

## V5 Starter Agents

| Agent | What it teaches |
|---|---|
| `v5_region_attacker` | Pressure a bounded region large enough to cover an objective. |
| `v5_scout_striker` | Search, remember a contact, and strike before resuming the search. |
| `v5_core_defender` | Observe your own core and repair confirmed losses. |
| `v5_dual_team` | Coordinate a raider and keeper within one shared action budget. |

Read, copy, and adapt them. Each exposes just one or two parameters so you can
see how a decision changes its behavior. The [V5 starter guide](docs/V5_STARTER_AGENTS.md)
explains their lessons and trade-offs. For a larger example, `v4_quorum`
coordinates six processes.

## Build Your Own Agent

Start with the authoritative **[Agent API v2 authoring guide](docs/AGENT_API_V2.md)**:

```bash
bytefray agents create my_agent --api-version 2 --template annotated
bytefray agents validate my_agent
bytefray agents test my_agent --opponent v5_region_attacker
```

Initialize match state in `reset(context)`, then return your fixed roster of
`ProcessDeclaration` objects from `declare_processes()`. Each call to
`act(observation)` receives an `ObservationV2` for the acting process and
returns an action such as `READ`, `WRITE`, or `MOVE`. Use `MatchContextV2.rng`
for deterministic randomness.

Edit the generated `agent.py` and `agent.yaml` with your preferred editor;
the Designer supports creation, validation, testing, and replay inspection.
See the [authoring workflow](docs/AGENT_AUTHORING.md) and
[Agent Lab](docs/AGENT_LAB.md) for tracing, evaluation, and debugging.

## Parameters and Presets

For example, start from the region attacker's `far_sighted` preset and override
its reach:

```bash
bytefray run --a-type v5_region_attacker --b-type v5_core_defender --a-preset far_sighted --a-param attacker_reach=24 --seed 42 --ticks 200 --replay runs/v5-params/replay.jsonl
```

Resolution follows **defaults < preset < explicit override**: the default reach
is `16`, `far_sighted` selects `32`, and this command runs with `24`. Invalid
values are rejected. In the Designer's **Agent Params** tab, typed controls
and preset selection show the effective values before the match starts.
See [parameters and presets](docs/AGENT_API_V2.md#m-parameters-and-presets).

## Deterministic by Design

With deterministic agents, the same agent code, ruleset, seed, effective
parameters, and match configuration produce reproducible semantic execution.
**Randomize Seed** explicitly chooses a new visible seed; keep that value to
repeat the match.

Canonical `result.json` and `replay.jsonl` artifacts preserve match identity
and effective parameters. Replay tools inspect recorded execution without
rerunning the agents. Evaluation and tournaments compare agents across
specified opponents and seeds.

## Compatibility

- Historical V4 starters remain available, including the advanced `v4_quorum`.
- Agent API v1 remains supported on its existing Ruleset v1/v2 path; VM/blob
  matches retain Ruleset v1.
- Stable API-v2 gameplay remains `bytefray-rules-4`. Historical alpha rulesets
  remain explicitly selectable for reproduction.
- V5 development is additive: existing agents and historical result/replay
  formats retain their compatibility paths.

See [Compatibility](docs/COMPATIBILITY.md) for exact boundaries and
[GitHub Releases](https://github.com/libertaine/Bytefray/releases) for earlier
versions, including the stable [Bytefray v4.0.0](https://github.com/libertaine/Bytefray/releases/tag/v4.0.0).

## Documentation

- [Agent API v2 authoring guide](docs/AGENT_API_V2.md) and [V5 starters](docs/V5_STARTER_AGENTS.md)
- [Authoring workflow](docs/AGENT_AUTHORING.md) and [Agent Lab](docs/AGENT_LAB.md)
- [Installation reference](INSTALL.md) and [Linux installation details](docs/LINUX_INSTALL.md) — use the Alpha 1 filenames above; these references also cover earlier releases
- [Stable gameplay rules](docs/RULES_V4.md) and [compatibility](docs/COMPATIBILITY.md)
- [Tournaments](docs/TOURNAMENTS.md), [result schema](docs/RESULT_SCHEMA.md), and [replay schema](docs/REPLAY_SCHEMA.md)
- [Architecture](ARCHITECTURE.md) and [feature specifications](docs/specs/)
- [Changelog](CHANGELOG.md) and [Alpha 1 qualification and publication record](docs/research/v5/V5_ALPHA1_PHASE_F_FINAL_QUALIFICATION.md)

## Development

Clone the repository and select `v5-research` for V5 development. Create and
activate a virtual environment as above, then install development dependencies:

```bash
python -m pip install -e ".[dev,replay,designer]"
python -m pytest
ruff check .
mypy engine/src/battle_engine
mypy client/src/battle_client
```

The default test run excludes display-backed tests marked `gui`. See
[Contributing](CONTRIBUTING.md), [agent development guidance](AGENTS.md), and
[Windows development notes](docs/WINDOWS_DEV_NOTES.md) for workflow details.
No LLM is required to build or run Bytefray; the
[development method](docs/DEVELOPMENT_METHOD.md) describes optional AI assistance.

## Project Status

**Bytefray 5.0.0 Alpha 1 is an Alpha release.** Interfaces, starter behavior,
and UX may continue to evolve before Bytefray 5.0.0 final.

## License, Contributing, and Support

Bytefray uses the [MIT License](LICENSE). pMARS interoperability is separate
GPL-licensed software; Windows distributions that bundle it preserve the
materials in [third_party_licenses/](third_party_licenses/). The Python wheel
does not include a pMARS executable.

[Contributions](CONTRIBUTING.md) and [GitHub issues](https://github.com/libertaine/Bytefray/issues)
are welcome. See [Security](SECURITY.md) for private vulnerability reporting.

If Bytefray has been useful or entertaining, you can
[buy me a coffee or pizza via PayPal](https://www.paypal.com/donate/?hosted_button_id=DRJD388WT8DAL).
Contributions are entirely optional.
