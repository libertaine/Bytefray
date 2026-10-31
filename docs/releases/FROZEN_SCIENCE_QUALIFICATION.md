# Frozen E9 science and product CI: two qualification boundaries

Date: 2026-10-31. Decision: project owner, Option 1 of
[the PR #6 CI remediation](CLASSIC_RULESET_RETIREMENT_CI_REMEDIATION.md)
Section D: separate frozen-science qualification from current product CI.

**E9 remains LOCKED. Requirement C remains NOT ESTABLISHED.** Nothing here
runs, resumes or authorizes E9 research. Every check is read-only.

## The problem

E9's committed contracts govern a whole-repository snapshot: product
documents (`ARCHITECTURE.md`, `docs/AGENT_API_V2.md`, `docs/REPLAY_SCHEMA.md`,
`docs/RESULT_SCHEMA.md`), an LF manifest of every `engine/src` file, frozen E8
sources, packages and sealed results. Its tests assert those identities
against the live tree. Since V6 alpha M1-1 (`b6c9a57`, 2026-10-10)
legitimately changed `engine/src`, no development commit could satisfy them,
and `test-linux-core` had not passed on the V6 line since. A red product
job that can never turn green proves nothing about either the product or
the science.

## Boundary design

| | Product qualification | Frozen-science qualification |
| --- | --- | --- |
| Question | Does the current product meet its current contracts? | Does the frozen science still reproduce exactly as recorded? |
| Source | The commit under test | The pinned historical snapshot, checked out by commit |
| Where | `ci.yml` (`python -m pytest`, locally too) | `frozen-science.yml` |
| Environment | Supported matrix, current dependencies | Recorded research environment |
| Evidence guard | `test_frozen_science_boundary.py` in the product suite | `protected-evidence-guard` job |

One record governs both: [`tools/qualification/frozen_science_e9.json`](../../tools/qualification/frozen_science_e9.json),
with [`tools/qualification/frozen_science.py`](../../tools/qualification/frozen_science.py)
(standard library only) as its verifier.

### 1. Product selection

The root [`conftest.py`](../../conftest.py) deselects exactly the
`product_ci_transfer` inventory: whole modules by exact path and individual
tests by exact node ID. No name pattern, skip marker, `xfail` or exception
handling is involved. Transferred cases are reported as *deselected* with a
summary line naming the workflow that verifies them, and
`--include-frozen-science` restores them. `test_frozen_science_boundary.py`
fails if an entry is not an E-series research test, names a missing test,
lacks a reason, or is absent from the historical inventory.

`test-linux-core` now checks out full history (`fetch-depth: 0`). Of the 24
E2–E8 test functions failing in the PR's earlier runs, 16 failed only because
a shallow clone could not `git show` or `rev-parse` the historical commits
their records name. With history they pass and **stay in product CI**: they
compare committed evidence with immutable historical commits, which is valid
in any tree.

### 2. Transferred inventory (1,507 cases)

Product collection on the PR, non-GUI: 9,095 cases with
`--include-frozen-science`; 7,588 without. The difference is exactly:

**All 40 E9 test modules** (1,499 cases):
`engine/tests/test_v6_e9*.py`. These are the E9 qualification inventory; the
E9 qualifier records themselves define qualification by module list. Their
subject, `tools/research/v6/e9`, and the modules themselves are
byte-identical to the snapshot (enforced below), so running them there
verifies the same code against the engine, packages and documents their
contracts actually govern. Running them on a developing tree can only fail
the inherited boundary (`load_protocol(verify=True)`) or, in the passing
remainder, test E9 tooling against an engine E9 is defined to refuse.

**Eight E8 tests**, each loading the E8 family freeze, whose qualification
record pins the bytes of `test_v6_e8_family.py`,
`test_v6_e8_sensing_context.py` and `test_ruleset_v6_research_sensing_active.py`.
V6 alpha M1-1 (`b6c9a57`) changed all three before Classic retirement, so the
eight already failed at `f127be7`; the retirement (`bb2c7a4`) changed the
third again:

- `test_v6_e8_analysis_freeze.py`:
  `test_a_re_signed_tampered_record_still_fails_to_load`,
  `test_a_tampered_record_fails_to_load`,
  `test_it_carries_every_earlier_identity`,
  `test_the_freeze_loads_and_its_identity_is_pinned`
- `test_v6_e8_family_freeze.py`: `test_the_freeze_loads_and_its_identity_is_pinned`
- `test_v6_e8_runner.py`:
  `test_a_failing_engine_source_check_stops_before_the_pre_match_gate`,
  `test_copied_packages_must_equal_the_family_freeze`,
  `test_the_preconditions_run_in_order_and_gate_every_match`

All eight pass unmodified at the snapshot. No product test, no other
E2–E8 test and no Designer, client or legacy test is transferred.

### 3. Historical snapshot and provenance

**Snapshot:** `b948540aa9ef34134ff7e3c633c3acfc9f97da96` (tree
`b75337919c51f1f5d68bc89823d3d1a048b0fd21`), "research(v6): preserve E9
blocked operational attempt", 2026-10-09: the last V6 research commit and the
direct parent of `b6c9a57`.

E9's contracts do not all belong to one commit. Each was checked against
the history (blob bytes):

| Contract | Committed | Reproduces |
| --- | --- | --- |
| E9 protocol freeze `v6-e9-prereg-v1-563980801bf0` (`protocol_freeze.json`): snapshots, 10 governing files, qualified E9 sources, frozen E8, packages, sealed E8 result, 116-file engine manifest | `6294efc` (record); verifier `514f4e2` | `load_protocol(verify=True)` passes at every E9 commit `514f4e2`, `d145db6`, `352277f`, `8994804`, `e035def`, `569cb9a`, `b948540`; first fails at `b6c9a57` ("the frozen engine manifest changed") |
| E9 v2 inherited scientific sources (`v2/scientific.py`) | `e035def` | Passes at `e035def` through `b948540` |
| Seal 06 implementation manifest (`v2_implementation_manifest_final_06.json`, 293 pins; seal record 17 pins) | `e035def` | Exactly at `e035def`; Seals 07–08 later changed 4 of its files |
| Seal 08 implementation manifest (`final_08`, 293 pins; seal record 28 pins) | `569cb9a` | Exactly at `569cb9a` and `b948540` |
| Seals 01–05 and 07 implementation manifests | `e035def` (checkpoint) | **Not reproducible as exact trees.** They were developed uncommitted and checkpointed together; `final_07` matches 289–291 of 293 pins at any commit. Their records remain intact and are read by the original tests |
| Inherited preservation manifest (1,203 working-tree pins at adoption) | `e035def` | **Partly not reproducible.** 1,174 pins match the snapshot checkout; 28 record the original research machine's working tree, not committed content: 17 are CRLF renderings of adoption-commit (`2dd8f69`) blobs, 11 are mixed-line-ending bytes never committed in that form (found, read-only, only in the original research worktree). The manifest file itself is intact and guarded |

`b948540` is the only commit at which every committed E9 contract that can
hold simultaneously does, so it is the snapshot. Its additions over `569cb9a`
are research evidence and documents only.

### 4. Historical verification (`historical-e9` job)

On `ubuntu-latest` and `windows-latest`:

1. Check out the current commit (for the policy and verifier only) and,
   separately, the snapshot **by commit** with full history.
2. Install the snapshot's own `.[dev]` on CPython 3.13 with
   [`e9_historical_constraints.txt`](../../tools/qualification/e9_historical_constraints.txt):
   pytest 9.1.1, PyYAML 6.0.3, ruff 0.16.3, mypy 2.3.1 (the recorded research
   `.venv`, `docs/research/v6/V6_PHASE0_BASELINE.md` section 3; qualified on
   3.13.14).
3. `verify-snapshot`: HEAD and tree equal the pinned identities, no tracked
   modification, every inventory entry exists, and the snapshot's **own**
   `load_protocol(verify=True)` and `verify_inherited_sources()` pass.
4. `run-historical` runs the inventory with the invocations it was qualified
   with, with temporary directories outside the snapshot:
   - the 29 E9 v2 modules (1,338 cases) with the command the snapshot's
     `tools/research/v6/e9/v2/qualification_run.py` builds for every E9 v2
     attempt: `-X utf8`, `addopts=-q`, no cache provider, plugin autoload
     disabled, `PYTHONUTF8=1`, and its `qualification_guard` plugin, which
     forbids entropy and match execution. The harness itself is not called,
     because it writes attempt evidence;
   - the 11 other E9 modules and the eight E8 cases (169) under the
     snapshot's own `pytest.ini`, as the V6 line's CI ran them.
5. Each run must report exactly its pinned case count with zero failures and
   errors. A short collection, a failure or an error fails the job.

**One case is not reproducible from any commit** and is excluded by exact
node ID, recorded under `not_reproducible_from_commits`, never counted as a
pass:
`test_v6_e9_v2_independent_bindings.py::test_separate_adoption_attestation_exact_review_and_unchanged_body`.
It asserts that the raw working-tree bytes of all 1,203 inherited
preservation pins equal their pins; 28 of them are the original machine's
working tree (provenance table). It passed there, and the evidence it reads
is guarded below, but it cannot be re-run anywhere else. To keep the
limitation exact, `run-historical` checks at the snapshot, read-only, that
the working tree mismatches the manifest in exactly the 28 recorded
path/pin pairs (`working_tree_pins` in the policy) plus `.gitattributes`,
whose bytes must equal the recorded superseding SHA-256; the other 1,174 pins
are verified. The test's remaining assertions (adoption attestation, review
archive, supersession record) are not re-run.

Plain `pytest` at the snapshot also fails two further E9 v2 cases
(`test_w12_producer_is_real_only_with_no_entropy_reference_or_mode_switch`
asserts the guard is active; `...[outside_repository]` needs a temporary
directory outside the checkout). Both are properties of how E9 v2 was
qualified, not defects, and the recorded invocation satisfies them.

Nothing from the current tree's product source is consulted, so product
changes cannot be read as changes to the snapshot. Triggers: manual,
weekly, and pushes or pull requests touching research, E-series tests, the
policy, the root `conftest.py` or `.gitattributes`.

### 5. Seal 07 and pytest 9.2

`test_v6_e9_v2_gate8_seal07.py::test_s7_regular_missing_unreadable_and_opened_identity`
replaces `os.fstat` with a stub lacking `st_size`. At the snapshot, unmodified:
pytest 9.1.1 passes; pytest 9.2.0 fails with `AttributeError`. It is a
protected test and was not edited. It now runs only at the snapshot, under
the pinned 9.1.1. Product CI keeps current pytest.

### 6. Current-tree protected-evidence guard

Separation must not make frozen evidence editable. `frozen_science.py guard`
(job `protected-evidence-guard`, and
`test_protected_evidence_is_identical_to_the_immutable_snapshot` in the
product suite) requires that every file under

- `tools/research/v6/`
- `docs/research/v6/`
- `engine/tests/test_v6_e9*.py` and `engine/tests/_e9_*.py`

be byte-identical (raw SHA-256) to the same path in the snapshot commit, with
none added, removed or left untracked. Expected bytes come from the
immutable snapshot objects, not from the checkout under test; the snapshot's
tree ID and the 795-file manifest digest
`1c59ecd294d4b3e0fe24b855e6a89fd80d41fe455d7a276701906c110d8ad8c0` are
pinned as a second identity. Without the snapshot commit the guard fails
closed. All 795 files currently match, as they have since the snapshot.

Product documents and `engine/src`, which E9's contracts also named, are
deliberately outside the guard: they are the product. Changing a protected
path now requires changing the pinned anchor, which is visible in review.

## Limitations

- One E9 v2 case asserts never-committed working-tree bytes and cannot be
  reproduced from any commit (section 4).
- Seals 01–05 and 07 cannot be reproduced as exact historical trees (above).
- Qualification ran on CPython 3.13.14; CI uses the runner's 3.13 patch
  release. Locally 3.13.7 reproduced every check.
- The research `.venv` was not frozen with `pip freeze`; the constraints
  reproduce every version the record names, plus their resolved
  dependencies.
- E9 tests fail on CPython 3.10 in ten Seal 06–08 `read_error` cases (seen
  only in the old 3.10 product job). They were never qualified on 3.10 and
  now run only on 3.13.
