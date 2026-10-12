# Replay History seed overflow: bounded hotfix review

2026-10-11, America/Indianapolis. **Ready for Project Lead review.**
Published baseline: `043cbac527e015a7b8b0ba48e64eacf46cf2b282`.
Branch: `v6-research`. No staging, commit, or push.

## Confirmed cause and isolated reproduction

Discovery preserves arbitrary Python integer seeds. The baseline index binds
those integers directly to `occurrence.seed INTEGER`, and also binds the seed
filter as an integer. Python's SQLite adapter rejects values outside the
signed 64-bit range before SQLite can execute the statement. A failed refresh
rolls back its complete transaction, so one large seed can hide ordinary entries
from a first build as well.

Only new synthetic artifacts and temporary caches were used. Every integer
binding in the synthetic occurrence and entrant tuples was tested independently
with `SELECT ?`; **seed was the only overflowing column in the seed cases**.

| Seed | Baseline refresh and seed filter | Hotfix |
| --- | --- | --- |
| `-9223372036854775808` | Succeeds | Exact integer readback |
| `9223372036854775807` | Succeeds | Exact integer readback |
| `-9223372036854775809` | Overflow | Exact integer readback |
| `9223372036854775808` | Overflow | Exact integer readback |
| `18446744073709551615` | Overflow | Exact integer readback |

Minimal reproducer, run from the repository using its Python interpreter:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from battle_engine.replay_history import ReplayHistoryService
from engine.tests.test_replay_history import _write_run

with TemporaryDirectory() as temporary:
    root = Path(temporary)
    _write_run(root / "runs", "ordinary", seed=42)
    _write_run(root / "runs", "large", seed=2**64 - 1)
    with ReplayHistoryService.open(data_root=root) as history:
        history.refresh()  # Baseline: OverflowError; hotfix: committed.
        assert history.count() == 2
```

The helper writes synthetic JSON fixtures; it executes no match or research
controller. On the baseline, catching the exception and querying the cache
returns zero rows. The corrected cache contains both entries.

## Correction and compatibility

The sole runtime implementation change is in `replay_history/index.py`:

- Declare `seed TEXT` with real TEXT affinity.
- Bind known seeds as canonical decimal strings; absent seeds remain SQL NULL.
- Convert seeds to Python integers on both page and detail readback.
- Bind exact seed filters as canonical decimal strings.
- Increase `CACHE_SCHEMA_VERSION` from 1 to 2.

No float conversion, truncation, wrapping, substitution, wire-schema change,
or public `int | None` API change is introduced. Existing presentation and
clipboard code receives exact Python integers. Discovery's existing invalid
seed policy remains intact: booleans, strings, floats, containers, null, and
missing values produce no seed.

The locator remains `cache/replay_history/index-v1.sqlite3` so the normal
maintenance owner detects the existing cache's `PRAGMA user_version` mismatch
and uses its existing recovery/rebuild path. The filename does not determine
the stored schema version. Schema metadata is also updated to 2. No manual
cache deletion or authoritative artifact migration is required. A read-only
query owner refuses incompatible caches until maintenance prepares them.
The existing blocked-deletion/session-only fallback is unchanged.

## Exact changed files

| File | Purpose |
| --- | --- |
| `engine/src/battle_engine/replay_history/index.py` | TEXT seed storage, integer readback, string filtering, cache version 2 |
| `engine/tests/test_replay_history.py` | Boundary/adjacent seed values, result-backed and replay-only readback, rebuild/reopen, exact filtering, invalid/absent seeds, incremental updates, transaction rollback, real v1 INTEGER-affinity cache recovery |
| `engine/tests/test_replay_history_concurrency.py` | Extend existing commit/rollback/cancellation and rebuild/reconcile matrix to large positive/negative seeds and exact reader filters |
| `engine/tests/test_v5_replay_history_presentation.py` | Service-backed seed display, detail, filter and Copy Seed presentation |
| `tests/test_v5_replay_history_browser.py` | Exact clipboard contents for signed boundaries and large seeds |
| `tests/test_v5_replay_history_qualification.py` | Real two-worker History window refresh, filtering, clipboard and repeated refresh over mixed ordinary/large seeds |
| `docs/v6/V6_REPLAY_HISTORY_SEED_OVERFLOW_HOTFIX_REVIEW_01.md` | This review record and reproducible limitations |

## Validation

All commands used `.venv/Scripts/python.exe -B`. Pytest invocations were
sequential, with separate fresh temporary roots beneath `.pytest-tmp`.

| Check | Result |
| --- | --- |
| New result-backed seed contract tests before runtime edit | 11 expected failures: overflow or previous INTEGER storage type |
| `python -m pytest engine/tests/test_replay_history.py engine/tests/test_replay_history_concurrency.py engine/tests/test_v5_replay_history_presentation.py --basetemp=.pytest-tmp/seed-overflow-focused-20261011 --tb=short` | **229 passed**, 13.66 s |
| `python -m pytest tests/test_v5_replay_history_browser.py tests/test_v5_replay_history_qualification.py -m gui --basetemp=.pytest-tmp/seed-overflow-gui-20261011 --tb=short`, `QT_QPA_PLATFORM=offscreen` | **107 passed**, 97.40 s |
| `python -m ruff check .` | PASS |
| `python -m mypy engine/src/battle_engine` | PASS, 102 source files |
| `python -m mypy client/src/battle_client` | PASS, 19 source files |
| `git diff --check` | PASS |

The normal Designer History window successfully indexes six synthetic entries
with seeds 42, the signed minimum and maximum, both one-beyond-boundary values,
and the unsigned 64-bit maximum. All six appear together; the large seed filters
exactly, copies exactly to the clipboard, and survives a further refresh.
Backend coverage also checks adjacent large integers, positive/negative
`2**128`, zero, ordinary seeds, artifact-byte/mtime preservation, failed-refresh
rollback, and concurrent reader visibility. GUI evidence is Qt offscreen, not
a manual native desktop acceptance claim. No unrelated broad research suite
was executed.

## Remaining independently reproduced failure cases

Other integer columns were inspected rather than assumed safe. These separate
synthetic cases still overflow and are outside this seed-only correction:

| Input | Overflowing binding |
| --- | --- |
| `result.ticks = 2**63` | `occurrence.ticks` |
| Entrant metadata `api_version = 2**63` | `occurrence_entrant.api_version` |
| `completed_at = "2500-01-01T00:00:00Z"` | `occurrence.effective_timestamp_ns` |
| History date filter starting at year 2500 | Timestamp range parameter |

Each artifact case was confirmed to fail refresh and leave the transaction
uncommitted after the seed fix. No range restriction, float conversion, or
silent replacement was added for those fields. Their disposition needs a
separate bounded change. Filesystem size/mtime bindings were within range in
the synthetic cases; that observation does not prove every possible filesystem
timestamp fits. Schema versions pass through supported-version readers;
flags are 0/1, counts/ordinals derive from bounded artifact collections, and
generation values are internal cache counters. None caused the reproduced
large-seed failure.

## Preservation

The already retained historical baseline at
`work/m1_1_frozen_baseline_20261010` was rehashed against the implementation
and qualification final-08 manifests before and after the work:
**329/329 raw pins match**. Manifests and historical copies were not changed.
In the live product checkout, 11 pre-existing differences from those historical
source pins were present at entry; the only additional manifested live-source
change is the explicitly requested product `replay_history/index.py` correction.

Historical result/replay/trace files, user caches, research outputs, private
artifacts, and inherited untracked work were not edited or deleted. No E9
scientific controller or research seed generator was executed. No unrelated
M2 development was begun. The hotfix remains unstaged for lead review.

## Closure

2026-10-11. **CLOSED.** The Project Lead accepted the hotfix and chose
option A: the date-filter overflow becomes a separate bounded fix.

Final audit of the seven-file manifest: every change supports the seed
correction, cache compatibility, tests, or this record. Seeds are written,
filtered, and read back only through canonical decimal TEXT and exact
integers. No `ORDER BY`, keyset, or facet clause uses the seed column. The
v1 cache is replaced through the existing schema-version recovery path. No
result, replay, or trace schema changed. Discovery, the Designer, research
code, and Alpha 1 files are untouched.

The closure audit reran the retained validation on the exact bytes to be
staged:

- 229 focused tests passed.
- 107 GUI tests passed (Qt offscreen).
- Ruff and engine/client mypy passed.
- `git diff --check` passed.
- 329/329 historical pins still match.

### Residual integer overflow disposition

| Case | Reachable from normal use | Disposition |
| --- | --- | --- |
| History date filter: From on or after 2262-04-12, or To on or after 2262-04-11 (US Eastern) | **Yes.** The From/To `QDateEdit` widgets set no range and accept dates up to 9999-12-31 | **Separate bounded fix** |
| `result.ticks` at or above `2**63` | No. Ticks are executed ticks, so only a hand-edited result reaches this | Post-hotfix hardening |
| Entrant `api_version` at or above `2**63` | No. The engine records it only for Python entrants, which must declare API version 2 | Post-hotfix hardening |
| `completed_at` outside 1677-09-21 to 2262-04-11 | No. Requires a hand edit or a clock beyond that range | Post-hotfix hardening |
| `result.json` mtime outside the same range | No. Requires a deliberate `os.utime`, a wrong clock, or a faulty tool | Post-hotfix hardening |
| Seed literal longer than 4300 digits | Bounded. JSON parsing rejects it, the entry records no seed, and the refresh commits | None |

The date-filter defect reproduces through the real History window. The
status line reports `History could not be updated — Python int too large to
convert to SQLite INTEGER` while the previous unfiltered rows stay visible.
Clear Filters recovers it, and no artifact or cache data is lost. The code
path was not changed by this hotfix, and the defect already existed at the
baseline.

The recommended remedy saturates both date-bound parameters in
`_filter_clauses` to the signed 64-bit range. Every stored
`effective_timestamp_ns` value already fits in that range, so saturation
selects exactly the same rows.

Each hardening case above aborts the whole refresh, so a first build shows
no rows. The recommended remedy is per-entry containment: range-check the
integer columns and degrade only the affected entry, with a diagnostic. No
remedy is implemented here.

E9 scientific execution remains **LOCKED**. Requirement C remains **NOT
ESTABLISHED**.
