# Replay History date-filter hardening: bounded review

2026-10-12, America/Indianapolis. **CLOSED — final scope audit PASS.**

Baseline: `7f51c2195cb4066d266aa81272dec289daea4019`, `v6-research`.
The preceding large-seed incident is closed. This change is limited to date
filter conversion, query predicates, the Designer date-control adapter, and
their isolated regression coverage. Project Lead accepted final scope audit and
exact five-file staging. Commit and publication require separate authorization.

## Confirmed cause

`replay_history/index.py::_epoch_ns()` converted a datetime through
`int(moment.timestamp() * 1_000_000_000)`. `_filter_clauses()` bound the result
directly to SQLite's signed 64-bit INTEGER comparison parameter.

An isolated synthetic result and temporary cache reproduced
`OverflowError: Python int too large to convert to SQLite INTEGER` at
`HistoryIndex.count()` for a year-2500 lower bound, a year-1600 upper bound,
and a year-9999 lower bound. No recorded timestamp had to overflow; the
failing value was the filter parameter for `effective_timestamp_ns`.

The baseline regression matrix produced **12 failures / 9 passes**:
nine parameter overflows and three incorrect nanosecond-edge inclusion results
caused by floating-point conversion. Ordinary and extreme bounds were tested
against stored integers including both exact SQLite endpoints.

The separate Windows presentation probe also confirmed `OSError: [Errno 22]
Invalid argument` in `day_bounds()`'s naive `datetime.astimezone()` conversion
for years 1600, 1677, 1752 and 9999. The Designer accepts 1752 through 9999;
restricting its dates would discard supported input rather than correct the query.

## Implementation and exact semantics

`_epoch_ns()` now uses integer timedelta days, seconds and microseconds.
Naive query datetimes retain their existing interpretation as UTC; aware
datetimes honor their offsets. No float, truncation, wrapping or date
saturation is used. Offset-aware Python endpoint dates can be compared without
first constructing an out-of-range UTC datetime.

The predicate translator compares the exact bound with the stored INTEGER
domain before choosing a predicate:

| Bound | Exact query behavior |
| --- | --- |
| Lower below signed int64 minimum | No additional numeric restriction |
| Lower within signed int64 | Inclusive `effective_timestamp_ns >= bound` |
| Lower above signed int64 maximum | No rows |
| Upper below signed int64 minimum | No rows |
| Upper within signed int64 | Inclusive `effective_timestamp_ns <= bound` |
| Upper above signed int64 maximum | No additional numeric restriction |

Every active date bound still adds `timestamp_known = 1`, including
mathematically unrestricted outside bounds. Unknown dates remain visible
when no date bound is active. Other filters compose normally, including exact
large seeds. Simply clamping an impossible lower/upper bound would incorrectly
include a row at the maximum/minimum endpoint; this implementation avoids that.

The private Designer adapter first calls the unchanged `day_bounds()`
presentation API, preserving supported ordinary local-day behavior. If Windows
rejects that conversion with OSError or OverflowError, Qt's system timezone
provides the local offset. The resulting Python datetime retains midnight for
From or 23:59:59.999999 for To and is passed through the existing HistoryFilterState
and HistoryQuery APIs. Start and end offsets are resolved separately.

The final calendar audit reproduced an unresolved Qt datetime returning a zero
offset. The adapter now explicitly rejects invalid QDate inputs and invalid
Qt datetime resolution. The window displays the error and retains its prior
query without sending a new request, so invalid calendar input cannot silently
broaden the date filter. Valid dates recover normally. The standalone
`day_bounds()` helper remains byte-for-byte unchanged.

Cache schema **v2**, extractor version **1**, cache locator, table definitions,
public query/service APIs, recorded timestamp ingestion/formatting, and
result/replay/trace schemas are unchanged. No cache invalidation or rebuild is
needed for this query-only correction.

## Exact changed files

| Path | Purpose |
| --- | --- |
| `engine/src/battle_engine/replay_history/index.py` | Exact datetime conversion and safe, inclusive date predicates |
| `app/views/replay_history.py` | Private Windows calendar-date fallback using Qt timezone conversion |
| `engine/tests/test_replay_history.py` | 21 nanosecond-edge/composed-filter cases plus 4 exact int64 endpoint predicate checks |
| `tests/test_v5_replay_history_qualification.py` | 10 date/filter/clipboard, 3 local-day/DST and 4 invalid-calendar rejection/recovery cases |
| `docs/v6/V6_REPLAY_HISTORY_DATE_FILTER_HARDENING_REVIEW_01.md` | This review record |

## Validation

All pytest cases use isolated temporary artifacts and caches under fresh
repo-local `.pytest-tmp` roots. Pytest runs were sequential. GUI runs used
Qt offscreen on Windows; no real Designer data-root history was opened.

| Check | Result |
| --- | --- |
| Backend exact nanosecond matrix | 21 passed |
| Focused backend/concurrency/presentation suite | **250 passed**, 13.61 s |
| Designer History browser/qualification suite | **120 passed**, 100.55 s |
| Final boundary audit, including exact min/max predicates | **25 passed**, 0.78 s |
| Final calendar, valid-date and large-seed clipboard audit | **18 passed**, 4.92 s |
| `python -m ruff check .` | PASS |
| Engine mypy | PASS, 102 source files |
| Client mypy | PASS, 19 source files |
| `git diff --check` | PASS |

The 250/120 results are the retained bounded regression runs before the final
calendar validity guards. The final guards and valid date paths were verified
by the separate focused 25/18 audit runs, along with fresh Ruff and both mypy
checks. These selections overlap and are not added together. No broad research
or product campaign was repeated for staging.

Python datetimes cannot encode either exact signed-int64 nanosecond endpoint.
The four endpoint audit cases substitute the exact converter result and query
the synthetic edge cache, directly proving inclusive lower/upper predicates at
both minimum and maximum. Unknown-date exclusion remains active.

Backend coverage includes int64 endpoint rows and neighboring nanoseconds,
1677/2262 boundary datetimes, year 1600/2500, offset-aware year 1/9999,
pre-epoch dates, exact equal bounds, inverted intervals, unknown timestamps,
keyset continuation, count/page agreement and combined filters. Existing
arbitrary-size positive/negative seed regression coverage also passes.

Designer coverage includes the minimum selectable 1752 date, ordinary local
days, spring/autumn DST transition days, 2262 boundary dates, years 2500 and
9999, inverted ranges, clear-filter recovery and exact large-seed copying.
Synthetic artifact bytes and modification times are checked unchanged.

## Preservation and residual risks

The real 158,866-entry cache was not opened for maintenance or rebuilt.
Its SHA-256 before and after is identical:

`8083e44a977844751ad5b040b80bf2133fbdb5917a66947a6e20b4fe43768348`.

A read-only audit verifies all **35,197 retained research-file hashes** and
**329/329 frozen final-08 pins** unchanged. Inherited untracked files remain
preserved. Accepted M1 records/contracts and scientific research outputs were
not edited. There was no E9 execution, extreme tick/API-version hardening or M2 work.

Residual boundaries for review:

- Existing timestamp ingestion and display conversions remain unchanged,
  including any previously rounded stored timestamp values. Exact queries
  compare the integers already stored; no timestamp migration is performed.
- Recorded timestamp ingestion, including out-of-range recorded values,
  remains a separate follow-up; this correction handles query bounds only.
- Extreme tick-count integer bindings remain a separate follow-up.
- Entrant API-version integer overflow remains a separate follow-up.
- The unchanged public `day_bounds()` helper alone still has platform C-runtime
  year limits. The Designer adapter handles those failures without adding a Qt
  dependency to the Qt-free presentation service.
- Far-calendar fallback offsets follow Qt/system timezone data. Ordinary and
  DST dates retain the original presentation conversion. Linux native GUI and
  a new real-corpus qualification were not run for this bounded change.
- From/To remain inclusive Python datetime bounds with microsecond precision;
  their public meaning has not been expanded to hypothetical sub-microsecond
  calendar-day endpoints.

## Final acceptance and staging authorization

Project Lead disposition: **ACCEPTED FOR FINAL SCOPE AUDIT AND STAGING**.
The final audit passes: exactly the five files above, exact integer bounds,
inclusive endpoint predicates, unknown-date exclusion, AND composition,
contradictory-range emptiness, preserved local-day conversion, explicit invalid
calendar rejection and no remaining demonstrated valid-input blocker.

Cache schema v2 and extractor version 1 remain unchanged. The preservation
audit is refreshed read-only before staging. Residual follow-ups above remain
separate and do not authorize additional implementation.

Approved commit subject:

`fix(history): handle out-of-range date filters safely`

Only the five reviewed files may be staged. Index manifest, reviewed blob
identities, working-tree/index parity and cached whitespace checks are verified
before reporting staging complete. No cache, generated artifacts, research
material, backups or inherited unrelated files belong in the index.

**Stop after staging verification. No commit, push or M2 authorization.**
