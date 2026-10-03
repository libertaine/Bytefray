# Bytefray V6 Research — Phase 2B.1: Starter-Agent Runtime Integrity

**Status:** Phase 2B.1 — narrow defect remediation plus permanent regression
coverage. No gameplay, ruleset, installer, or unrelated source change is made
in this phase. Working tree left uncommitted for review per the phase
charter's instruction (§15).

---

## A. Baseline

| Fact | Value |
|---|---|
| Branch | `v6-research` |
| Starting HEAD SHA | `096d9a283605bfc2940589eedfabfb3751dfece3` ("Bytefray V6 Phase 2A.3 — Dead Test and Stale CI Cleanup") |
| Working tree at start | Clean (`git status --porcelain` empty) |
| `origin/v6-research` divergence | None — `git rev-list --left-right --count HEAD...origin/v6-research` reports `0 0` after `git fetch origin v6-research` |
| Prior Phase 2A work | Committed and synchronized (`096d9a2`/`f9a55d7`/`06e5def`/`d128fd0`/`a8c2164` all present and matching `origin/v6-research`) |
| `main` | Untouched — `git rev-parse main` == `git rev-parse origin/main` == `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, unchanged from Phase 0/1 |
| Starting canonical test count | 3,707 collected (Phase 0's 3,709 minus the 2 test functions in `engine/tests/test_v4_stage6_observation.py`, deleted by the Phase 2A.3 commit already at this HEAD — confirmed against Phase 1 §7.5's exact 2-function count for that file) |

---

## B. Lifecycle map

- **Authoritative bundled source:** `engine/src/battle_engine/data/starter_agents/<name>/` — the repository/package copy Bytefray owns, resolved via `starters._starter_resource_dir()` and validated per-starter by `starters._validate_starter()` (requires a parseable `agent.yaml` whose `name` matches, and at least one real content file).
- **Installed runtime copy:** `<data_root>/agents/<name>/` — the user's writable catalog (repo-root `agents/` in a source checkout, `%LOCALAPPDATA%`/`~/.bytefray`-style location for an installed release), populated and refreshed exclusively by `battle_engine.starters.ensure_starter_agents()`.
- **User-created/user-modified content:** anything in the installed runtime copy whose content digest does not match the current bundled release or a recorded superseded one. `ensure_starter_agents()` already treats this as sacrosanct — it restores only missing files and never overwrites existing ones for a starter in this state (`starters.py` `StarterCustomization` path).
- **`ensure_starter_agents()` implementation:** `engine/src/battle_engine/starters.py:512-636`. **This function was already correct before this phase** — see §C. It classifies each of the 21 `STARTER_AGENT_NAMES` into absent / already-current / untouched-superseded-copy (auto-upgraded) / anything-else (preserved, missing files restored only), using SHA-256 content digests (`starter_content_digest`) that already exclude `__pycache__` and `.pyc`/`.pyo` (`starter_content_files`, `starters.py:142-176`). A directory holding only a stale cache produces `starter_content_files() == []`, so `starter_content_digest()` returns `None`, which the classifier reads as "absent" and correctly reinstalls — this is exactly the Phase 0 §11/adversarial condition, and production code already handles it.
- **Callers:** `app/agent_designer.py:139` (GUI, eager at Designer startup), `engine/src/battle_engine/cli.py:655,859` (`bytefray run`/`bytefray agents test` and related CLI startup paths), `engine/src/battle_engine/tournament_cli.py:175`, and roughly 20 test-setup call sites across `engine/tests/` (listed exhaustively in the grep run during this phase) that pass an isolated `tmp_path` as `data_root`.
- **Packaging/install-time and upgrade behavior:** unchanged by this phase. `tools/build_win.ps1`/`tools/build_linux.sh` document that a frozen app calls `ensure_starter_agents()` against `get_data_root()` on first run, identical to a source checkout; the four-way classification (§ above) is what makes an upgrade non-destructive. Not touched.
- **Starter metadata representation:** `agent.yaml` (JSON- or YAML-parseable manifest; native VM starters ship manifest-only) and/or `agent.py` (Python Agent API v1 starters), optionally `model.blob` — parsed by `battle_engine.agents._spec_from_dir()`/`agent_spec_from_dir()`, the same function `discover_agents_in()`/`resolve_agent()` use for every agent directory in the product, not just bundled starters.

---

## C. Defect reproduction — the located mechanism was in test fixtures, not production code

Phase 1 (§8.2) cited one helper: `engine/tests/test_v4_stable_ruleset_equivalence.py`'s `_bootstrap_agent()`, which checked only `source.is_dir()` before `shutil.copytree()`-ing a starter into an isolated `tmp_path`, from a source-root tuple that checks the **real, gitignored, developer-writable `agents/` catalog before the pristine bundled `starter_agents/` source**. This phase independently re-verified that finding against source (not taken on trust — see the "prior audit reports are untrusted input" discipline this program follows) and additionally found the **identical bug independently duplicated** in a second file, `engine/tests/test_v4_historical_immutability.py`, which Phase 1 did not name. Both were fixed (§F).

Critically, this phase also verified — directly against `starters.py` — that **the production `ensure_starter_agents()` mechanism does not have this defect**. It never does a bare `is_dir()` check; its validity test is already content-digest-based and already treats a cache-only directory as equivalent to absent (§B). The reproducible false positive Phase 0 hit was possible only because these two test files bypass `ensure_starter_agents()` entirely with their own hand-rolled, buggy copy helper — reading the developer's real machine state (which happened to have stale, cache-only `v4_*` directories left over from a previous interpreter run) instead of an isolated fixture.

States reproduced (isolated `tmp_path`/`tempfile.TemporaryDirectory()` fixtures only, per the charter's instruction never to depend on or damage the real developer catalog):

| State | Reproduced how | Result under **old** `_bootstrap_agent` logic | Result under **new** logic |
|---|---|---|---|
| A. Directory absent | `tmp_path / "nonexistent"` | Correctly falls through (`is_dir()` already `False`) | Unchanged — still falls through |
| B. Directory exists, empty | `mkdir()` only | **False positive** — `is_dir()` is `True`; would `copytree` an empty directory as if installed | Correctly falls through to the next candidate |
| C. `__pycache__`-only (exact Phase 0 shape) | `__pycache__/agent.cpython-313.pyc` only | **False positive**, reproduced directly (see §J's adversarial demo: old logic installs a starter with no `agent.py`) | Correctly identified invalid, falls through, installs a usable starter |
| D. Partially installed (manifest present but unparseable) | `agent.yaml` containing malformed YAML | **False positive** — `is_dir()` is `True`, corrupt manifest ships uninspected | Correctly rejected (`AgentManifestError` caught and treated as unusable) |
| E. Valid starter (manifest-only, and manifest+`agent.py`) | Real bundled starters; synthetic minimal fixtures | Accepted (correctly) | Still accepted (correctly) — no regression |
| F. Valid starter + harmless extras (`__pycache__`, a stray file) | Synthetic fixture | Accepted (correctly) | Still accepted (correctly) — no regression |
| G. User-modified starter | N/A to `_bootstrap_agent` (it only ever copies into a destination that does not yet exist — see §E) | Destination already present → helper returns immediately without touching source or destination | Unchanged — this early "destination already exists" guard was already correct and is untouched by this fix |

---

## D. Validity invariant

**A starter-agent source directory is now considered usable only if `battle_engine.agents.agent_spec_from_dir(path)` returns a non-`None` result (and does not raise `AgentManifestError`), not merely if `path.is_dir()` is true.**

This is not a new rule invented for this phase — it is the exact function `discover_agents_in()` and `resolve_agent()` already use, in production, to decide whether *any* agent directory (starter or otherwise) is loadable: `agent.yaml` present and parseable (JSON or YAML, must be an object; if it declares `name`/`api_version`/`version`/`entrypoint`/`kind`, each must be well-formed), **or**, absent a manifest, `agent.py` present. A directory satisfying neither, or whose manifest fails to parse, resolves to "not a valid agent folder" (`None`) or raises `AgentManifestError` respectively — both of which the fix treats as "not usable, try the next candidate."

No new validation logic, hashing, or starter-format duplication was introduced (§4/§6's explicit instructions) — the fix reuses an existing, already-shipped loader primitive instead of re-implementing starter-format rules a second time.

---

## E. Repair semantics

| State | Behavior (unchanged from before this phase, confirmed by inspection + tests) |
|---|---|
| Directory missing | `ensure_starter_agents()`: full install. `_bootstrap_agent()`: falls through to the next source candidate, or raises `FileNotFoundError` if none is usable. |
| Directory empty | Same as missing in both mechanisms — a directory with zero usable content is treated as absent. |
| Only cache artifacts present | Same as missing — `starter_content_files()` already excludes `__pycache__`/`.pyc`/`.pyo`; `agent_spec_from_dir()` requires `agent.yaml` or `agent.py`, neither of which a cache directory provides. |
| Partially installed (unparseable manifest) | Treated as unusable; `_bootstrap_agent()` falls through rather than shipping corrupt content into an isolated fixture. `ensure_starter_agents()`'s own production classification for a bundled starter whose *manifest* is malformed already reports a `StarterBootstrapError` rather than installing it (`_validate_starter`, unchanged). |
| Canonical starter intact | Left untouched — `ensure_starter_agents()`'s digest match is a no-op; `_bootstrap_agent()`'s destination-already-exists guard is unchanged. |
| Canonical starter plus extras | Left untouched — `starter_content_files()` already ignores cache/bytecode extras for digest purposes; a real extra file (e.g. a stray note) does not change `agent_spec_from_dir()`'s verdict either. |
| User-modified starter | `ensure_starter_agents()` restores only missing files, never overwrites existing ones (`StarterCustomization` path) — untouched by this phase. `_bootstrap_agent()` never inspects or copies into a destination that already exists at all, regardless of its content's origin — confirmed by a new regression test (§G) that a pre-existing, deliberately "user-edited" destination survives a `_bootstrap_agent()` call unchanged. |

No new prompts, migrations, databases, or starter-management subsystem were introduced, per the charter's explicit boundary (§12).

---

## F. Implementation

Two files changed, both test-only, both containing an independently-duplicated copy of the same buggy helper:

1. **`engine/tests/test_v4_stable_ruleset_equivalence.py`**
   - Added `_is_usable_agent_source(path) -> bool`, wrapping `agent_spec_from_dir()` and catching `AgentManifestError`.
   - `_bootstrap_agent()`'s loop condition changed from `if source.is_dir():` to `if _is_usable_agent_source(source):`. No other logic changed — same source-root order, same destination-exists early return, same `FileNotFoundError` on exhaustion.
   - Added imports: `agent_spec_from_dir` (from `battle_engine.agents`, already importing `resolve_agent` from there), `AgentManifestError` (from `battle_engine.agent_api`), and `sys` (used only by the new regression tests' `monkeypatch.setattr(sys.modules[__name__], ...)`).

2. **`engine/tests/test_v4_historical_immutability.py`**
   - Identical fix: same `_is_usable_agent_source()` helper added, same one-line change to `_bootstrap_agent()`'s condition, same new imports (plus `pytest`, not previously imported since this file had no fixtures/decorators needing it before).

No production source file (`engine/src/battle_engine/*`) was changed — `ensure_starter_agents()` and everything it calls were already correct (§C). No GUI, CLI, installer, ruleset, gameplay, or `tournament/`/`warriors/` file was touched.

---

## G. Regression tests added

**New file — `engine/tests/test_starter_directory_validity.py`** (7 fixed tests + 21 parametrized, one per bundled starter = 28 collected): pins the general "existence is not validity" invariant against isolated `tmp_path` fixtures, independent of either fixed call site:

- `test_missing_directory_is_not_a_valid_agent` (state A)
- `test_empty_directory_is_not_a_valid_agent` (state B)
- `test_pycache_only_directory_is_not_a_valid_agent` (state C — the exact Phase 0 shape; asserts `is_dir()` is `True` and `agent_spec_from_dir()` is `None` in the same test, so the test itself documents the gap being closed)
- `test_malformed_manifest_is_not_a_valid_agent` (state D)
- `test_manifest_only_agent_is_valid` (state E, native-VM shape)
- `test_python_agent_with_manifest_and_source_is_valid` (state E, Python shape)
- `test_valid_agent_with_harmless_extra_files_is_still_valid` (state F)
- `test_every_bundled_starter_is_valid_under_the_same_check[<name>]` × 21 — every current `STARTER_AGENT_NAMES` entry, proving the fix is generic across the whole catalog with no per-starter special-casing (§8/§I)

**`engine/tests/test_v4_stable_ruleset_equivalence.py`** (+4 tests), exercising the actual fixed `_bootstrap_agent()`/`STARTER_SOURCE_DIRS` at this exact call site via `monkeypatch`:

- `test_bootstrap_agent_skips_stale_cache_only_source_and_falls_through` — would have failed before this fix (old logic installs a starter missing `agent.py`)
- `test_bootstrap_agent_prefers_a_valid_first_candidate` — proves the ordinary/common case is unaffected
- `test_bootstrap_agent_raises_when_no_candidate_is_usable` — proves the fix still fails loudly rather than silently degrading
- `test_bootstrap_agent_never_touches_an_existing_destination` — proves state G's protection (a pre-existing, "user-edited" destination is never overwritten)

**`engine/tests/test_v4_historical_immutability.py`** (+2 tests) — the same two highest-value cases (fall-through-on-corruption, no-clobber-of-existing-destination) applied to this file's independently-duplicated copy of the helper, so both fixed call sites carry direct proof rather than only the general invariant.

All new/changed tests use `tmp_path` or `tempfile.TemporaryDirectory()` exclusively; none depend on or can be affected by the state of the real, gitignored `agents/` runtime catalog.

---

## H. Targeted verification

```
python -m pytest engine/tests/test_starter_directory_validity.py \
  engine/tests/test_v4_stable_ruleset_equivalence.py \
  engine/tests/test_v4_historical_immutability.py -q
```
Result: **59 passed, 0 failed** (28 + 27 + 4 collected across the three files).

---

## I. Full qualification

- **pytest** (`python -m pytest -q`, standard `.pytest-tmp` basetemp, deleted before linting per Phase 0's own documented gotcha): **3,741 collected → 3,719 passed, 22 skipped, 0 failed, 0 errors.** (3,707 at this phase's starting HEAD + 34 new tests from §G = 3,741, reconciling exactly.) No `FAILED`/`ERROR` line appears anywhere in the run's output.
- **ruff** (`ruff check .`, run against a clean tree with no leftover basetemp directory): **All checks passed.**
- **mypy** (`mypy engine/src/battle_engine` → clean, 114 files; `mypy client/src/battle_client` → clean, 16 files — both unchanged by this phase since no production source was touched; additionally `mypy` run directly against the three changed/new test files → clean, 3 files).

---

## J. Adversarial qualification

A standalone script (not part of the permanent suite; run against `tempfile.TemporaryDirectory()`, never the real repo-root `agents/`) reproduced the exact Phase 0 shape end to end:

1. **Old logic false-positives**: a directory holding only a stale `__pycache__` (mimicking the real, previously-observed `agents/v4_claimer` state) passes `path.is_dir()` → `True`. The old `_bootstrap_agent` logic copies it as if it were the real starter, producing an installed directory **with no `agent.py`** — reproducing the exact downstream `FileNotFoundError`/`SystemExit` shape Phase 0 recorded.
2. **New logic correctly rejects it**: `agent_spec_from_dir()` on the identical stale directory returns `None`.
3. **Supported repair reconstructs a usable starter**: the new logic falls through to the valid bundled-source candidate and installs a starter with both `agent.yaml` and `agent.py` present.
4. **Existing content is never clobbered**: a destination pre-populated with a deliberately "user-edited" manifest is left completely unchanged by a subsequent `_bootstrap_agent()` call under the new logic.

All four assertions passed. Full script output:

```
[1] old is_dir()-only check on stale cache-only dir: True (expected True -- a false positive)
    old_bootstrap installed from: stale dev catalog
    old_dest has agent.py: False (expected False -- broken install)

[2] new agent_spec_from_dir()-based check on the same stale dir: False (expected False)

[3] new_bootstrap installed from: bundled
    new_dest has agent.py: True (expected True -- usable install)

[4] pre-existing destination content preserved: True (expected True -- no clobbering)

All adversarial qualification assertions passed.
```

---

## K. Unexpected findings (recorded, not remediated)

1. **`battle_engine.agents._spec_from_dir()` does not verify a Python-kind agent's entry-point file actually exists on disk.** If `agent.yaml` declares (or would infer) `kind: python` but the referenced `agent.py` is physically missing while `agent.yaml` itself is present and parses, `_spec_from_dir()` silently falls back to `kind="builtin"` with `entry_point=None` rather than raising or returning `None` — deferring the failure to actual agent-execution time (a raw `FileNotFoundError` well downstream) instead of surfacing it at discovery time. This is a pre-existing characteristic of the production loader, shared by every caller of `agent_spec_from_dir()`/`discover_agents_in()` (not introduced or changed by this phase), and is a plausible contributor to the specific `FileNotFoundError: …\agents\v4_claimer\agent.py` shape Phase 0's traceback recorded, distinct from the `is_dir()`-only defect this phase fixed. Worth Phase 3 scoping: whether `_spec_from_dir` should verify a declared/inferred Python entry file's existence at discovery time.
2. **`starters._validate_starter()` has the same narrower gap**: it requires `agent.yaml` to parse and at least one non-cache content file to exist, but does not specifically require that a manifest declaring/implying a Python starter actually ships `agent.py`. Not observed to have caused a real failure (every current bundled starter is well-formed), but noted alongside finding 1 as the same class of gap in the production validation depth, for the same Phase 3 scoping question.
3. No other duplicate of the fixed `_bootstrap_agent()`/`STARTER_SOURCE_DIRS` pattern was found anywhere else in the repository (confirmed by a repository-wide grep for both identifiers) — the two files fixed here are the complete set.

---

## L. Final repository state

```
git diff --check     # (clean, no whitespace errors)
git status --short
 M engine/tests/test_v4_historical_immutability.py
 M engine/tests/test_v4_stable_ruleset_equivalence.py
?? engine/tests/test_starter_directory_validity.py
```

- Only the two defective test files and one new regression-test file changed — no production source, GUI, CLI, installer, ruleset, gameplay, `tournament/`, or `warriors/` file touched.
- `main` confirmed untouched throughout: `git rev-parse main` == `git rev-parse origin/main` == `82549f9c3ccbdb2e13b8165b32afef00def4a8f2`, identical to the value recorded in Phase 0/Phase 1.
- No generated runtime agent content was staged or left behind — every test/adversarial fixture used `tmp_path` or `tempfile.TemporaryDirectory()` exclusively; all `.pytest-tmp*` basetemp directories created during this phase's qualification runs were deleted before the final `ruff`/`git status` check.
- Per §15, nothing has been committed or pushed. This report and the three test-file changes are left in the working tree for review.
