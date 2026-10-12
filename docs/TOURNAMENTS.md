# Headless Tournament Service

Phase 5 introduces `TournamentService`, a headless orchestration layer over
`NativeMatchService`. It accepts a `TournamentRequest`, creates a deterministic
round-robin schedule, runs each pair in its own artifact directory, reads the
canonical `battle2.result` v2 artifact, and derives standings.

Each of two or more entrants plays every other entrant once per configured
round. Request order defines stable pair order. Match seeds are derived with
SHA-256 from the tournament seed, round, and ordered entrant IDs. Standings
record played matches, wins, losses, ties, and cumulative canonical score.

The tournament root contains `tournament.json` using schema
`battle2.tournament` version 1. It is atomically checkpointed after every match.
With resume enabled, a match recorded `completed` is only accepted from its
canonical `result.json` (instead of rerun) after verifying that result's own
entrant IDs, entrant order, and seed match the scheduled match, and that its
referenced replay exists and matches its recorded digest. A missing
`result.json`, or one that fails any of these checks -- copied from a
different tournament, stale from a differently-ordered or differently-seeded
request, unparseable, or paired with a missing/modified replay -- is recorded
as `corrupted` instead of `completed`. Failed, rejected, and corrupted matches
are all recorded and excluded from standings; they remain terminal unless
`retry_failures` is set, which retries all three the same way.

Every match has a stable scheduled ID and a directory beneath `matches/` that
contains its replay, canonical result, and compatibility summary where produced.
The canonical match and result IDs are recorded in tournament state.

A division must be entirely VM or entirely Python. Mixed VM/Python divisions
are rejected before artifacts are created. Phase 6a exposes the service through
the supported headless CLI:

```bash
bytefray tournament runner writer seeker \
  --rounds 2 --seed 1337 --ticks 3000 --output runs/league
```

Discovered Python agents use the same syntax, but every entrant in one division
must resolve to Python. Built-ins and blob manifests form VM divisions. The CLI
uses the normal writable data root, starter initialization, and agent discovery.

Rerunning the same request and output directory resumes completed canonical
results. `--retry-failed` reruns state entries recorded as failed, rejected, or
corrupted.
An incompatible request using an existing state directory exits with a controlled
error. Without `--output`, artifacts default beneath
`<data-root>/runs/tournaments/<entrants>-seed-<seed>/`.

Normal output reports the tournament ID, completed/failed/rejected counts,
standings, and state path. `--quiet` suppresses terminal presentation; the
canonical `tournament.json` remains the machine-readable output. Exit status is
0 when every scheduled match completed, 1 when the service completed with one or
more recorded failed/rejected matches, and 2 for invalid requests, unsupported
composition, or incompatible state.

Each match directory contains canonical `result.json` and `replay.jsonl`, plus
the compatibility summary where applicable. Single-match `bytefray run` output
also names its canonical result and replay alongside `summary.json`.

The optional PySide6 Designer exposes a deliberately small launcher at
**Tools → Run Tournament…**. It selects two or more homogeneous entrants,
rounds, seed, and an output directory, then runs this same supported CLI in a
background process. Each launch proposes a new folder beneath
`<data-root>/runs/tournaments/` (`designer-<UTC timestamp>-<suffix>`), so a new
roster never collides with an earlier tournament's state; choosing an existing
compatible output directory still resumes it.

When the process ends, the Designer opens **Tournament Results**, read only
from `tournament.json` and each completed match's `result.json`. It shows the
winner, the output folder, the Ruleset recorded by the matches, entrant and
match counts, the standings exactly as `tournament.json` records them, and
every recorded match in schedule order with its result, seed, and replay
availability. Entrants level on both wins and score share a rank and are shown
as tied for first rather than separated by the agent-ID ordering tiebreak.
Failed, rejected, and corrupted matches are listed with their recorded error;
because standings exclude them, the top entrant is then called the leader. A
`tournament.json` with no standings belongs to a tournament that stopped before
its schedule finished, and is shown as not finished, with no winner. **View
Replay** checks the replay against the digest in the match's `result.json` and
hands it to the normal Replay Viewer; a missing or changed replay is reported
instead of opened. If a run records nothing (the process exits without
replacing `tournament.json`, for example because the chosen folder holds a
different tournament), the Designer says the tournament did not run rather than
presenting the folder's earlier results.

**History → Tournament History…** lists the tournament folders directly beneath
`runs/tournaments/`, newest first, and reopens any of them in Tournament
Results; **Open Tournament Folder…** reads a tournament saved elsewhere. No
index or additional artifact is written. Completion counts and standings are
also written to the Advanced log, and **File → Open Last Output Folder** opens
the last tournament's output directory.

There is no bracket visualization, parallel scheduler, elimination bracket,
rating system, custom tournament scoring UI, or mixed-runtime division.
