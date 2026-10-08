# E9 v2 Seal-08 scope drafting return (01)

PROPOSED, 2026-10-08. This document returns the Seal-08 scope draft under
[Disposition 05](V6_E9_V2_FINDING_DISPOSITION_05.md), raw SHA-256
`5bf0c83ba0371224a1d722f07017af7cbcb399d1e413ce365b26b814df52ae29`.
**The Seal-08 scope is not frozen.** No implementation has started, and no source or
test byte has changed.

Scope drafting hit both of Disposition 05's stop conditions:

1. The *complete* F1 repair needs `authority.py` as well as `private_verification.py`
   (section 3).
2. S7-IQ-F2 directly contradicts four sealed Seal-07 test cases. Each of the two sealed
   Seal-07 modules would need an edit (section 4).

Steps 1–4 of the authorized sequence are done: Disposition 05 is written, the scope is
drafted, sufficiency is checked and the conflict sweep is done. Step 5 (freeze) and
everything after it wait for the decisions in section 7. Machine-readable bindings,
rehashes and probe hashes are in the write-once
`tools/research/v6/e9/v2_seal08_scope_drafting_verification_01.json`.

## 1. Baseline

- HEAD is `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c`, the index is empty and nothing
  was committed.
- All 327 Seal-07 manifested files (293 implementation, 34 qualification) match
  `final_07`. They were rehashed before and after the probe and before and after these
  records were written.
- `git status --porcelain` differs from `v2_seal07_git_status_final_02.txt` only by the
  three files written after that snapshot, plus this cycle's new records.
- The next candidate number is 31. No attempt-31 manifest exists.

## 2. Draft Seal-08 implementation (inside `private_verification.py`)

### 2.1 S7-IQ-F1 core: the current-G entry is never left to the scan

The fix applies at `_operational_boundary`, sealed lines 281-293. The current G's own
durable entry is compared with the bytes the boundary binds before the registry scan
runs, and regardless of what the scan does. A wrong-bytes entry is positive evidence by
itself. It does not need the scan's reads, which may be deferred.

```diff
     mismatched, unavailable = [], []
     registry = _durable(authority.root / "producer-roots" / (G["digest"] + ".json"))
     if registry is None:
         unavailable.append("producer registry")
+    elif registry != producers[0]:
+        # S7-IQ-F1 (disposition 05): this G's own durable entry is positive evidence by itself and
+        # is never left to the registry scan, whose mapped reads may be deferred.
+        mismatched.append("generation boundary does not bind the registered producer root")
     else:
         try:
             registered = authority.registered_producers().get(G["digest"])
         except (OSError, ProducerRegistryUnavailable):
             # S7-DEV-F1: deferred so a present first-raw marker is still checked for a mismatch.
             unavailable.append("producer registry")
         else:
-            if registry != producers[0] or registered is None or _raw(registered) != producers[0]:
+            if registered is None or _raw(registered) != producers[0]:
                 mismatched.append("generation boundary does not bind the registered producer root")
```

The marker comparison is unchanged and stays after the scan. The four lead-required
mismatch cases then give `FAILED_VERIFICATION`, and the two no-mismatch cases give
`UNAVAILABLE`. Retry stays terminal through the existing `_preconditions` "already
failed" refusal.

The classification of the existing combinations does not change. One reason text does.
A wrong-bytes entry with no fault used to fail on the scan's own check (for example
"producer registry differs from immutable G consumption evidence"). It now reports
"generation boundary does not bind the registered producer root". Both reasons are
value-free, and no sealed test matches either string (section 5).

### 2.2 S7-IQ-F2: classification follows the protected-verification boundary

The fix applies at the `produce_private_verification` outcome mapping, sealed lines
518-529.

```diff
-        if isinstance(exc, Unavailable):
-            outcome = "UNAVAILABLE"
-        elif isinstance(exc, Refused) or phase != "verification":
+        if isinstance(exc, Refused) or phase != "verification":
+            # S7-IQ-F2 (disposition 05): before the protected verification state is entered,
+            # unavailability too is a refused precondition, never a verification-stage outcome.
             outcome = "REFUSED_PRECONDITION"
+        elif isinstance(exc, Unavailable):
+            outcome = "UNAVAILABLE"
         else:
             outcome = "FAILED_VERIFICATION"
```

The propagated exception object is unchanged, so callers still receive the typed
`Unavailable`. Only the recorded outcome label moves. The resulting mapping:

| Where the typed `Unavailable` arises | Seal 07 | Seal 08 draft |
| --- | --- | --- |
| `_begin` (before the lock; intent or allocation reads) | no outcome (raised before `try`) | unchanged |
| `protected` entry: `_check` → `_state` (event files, `active.json`, retained tuple records), source checker, adopted P, catalogue, `frozen_limitations` | UNAVAILABLE | **REFUSED_PRECONDITION** |
| `_preconditions` under the lease: `_outcomes`, `_recovery` provenance, `_durable_log`, tuple resolves | UNAVAILABLE | **REFUSED_PRECONDITION** |
| `_derive` (phase `verification`): registry, marker, retained private evidence, retained records, events and catalogue read during verification | UNAVAILABLE | unchanged |
| write and post-PASS recheck phases | no outcome (re-raised) | unchanged |

**Frozen-text check.** No narrower meaning was found, so no contradiction is returned.
Planning Revision 02 §3 (raw `6c71f7cb…`, lines 133-142) says:

- "Unavailable authority/source state that prevents protected entry:
  REFUSED_PRECONDITION; the action and private verification do not run";
- "Non-regular W, PASS intent/outcome or other unprovable continuation state: existing
  non-terminal refusal";
- "Registry/marker/retained scientific evidence unavailable during verification:
  UNAVAILABLE".

Revision 01 R3 (raw `b0ae22ce…`) gives the same refusal for W.json and the PASS
intent. The Scope-03 `read_map` has no per-row classification. The draft therefore
applies the phase rule that already governs non-`Unavailable` errors at line 525.

## 3. Return 1: the complete F1 repair needs `authority.py`

Disposition 05 items 1 and 5 require that "any positive mismatch evidence that can still
be evaluated" is checked, and that "all available positive mismatch checks are
performed", before deferred unavailability may produce `UNAVAILABLE`. Scope 02 F1 order
item 3 counts registry consistency failures as such evidence: "or the registry fails
its unchanged consistency checks".

`authority.registered_producers` (sealed lines 274-304) **stops at the first typed
unavailable read**. Every entry sorted after that read goes unchecked. That includes
another G's entry that is present and inconsistent.

**Probe on the sealed bytes.** A plain-Python run, not pytest, with the
qualification-guard prohibitions and synthetic fixtures only. The script is in
`BATTLE2-test-temp/e9-v2-seal08-scope-probe-20261008-01/`, script raw `dbf23176…`,
output raw `4a6f8f2e…`. The inconsistent entry is this G's exact bytes stored under the
name `f…f.json`, which fails the unchanged `path.stem` check.

| Case | Result |
| --- | --- |
| Inconsistent other-G entry alone | `FAILED_VERIFICATION` ("producer registry source/study/actor mismatch") |
| Same entry, plus a non-regular entry `0…0.json` sorted first | `UNAVAILABLE`; after both are removed, the next attempt is **`PASS`** |

This is the S7-IQ-F1 pattern: positive registry evidence masked by a typed scan
unavailability, followed by a reachable PASS. The draft in §2.1 does not close it. Only
the scan can evaluate the other entries. Copying the scan's checks into
`private_verification.py` would duplicate authority logic, so it is not proposed.
Seal 06 already masked this case through the bare-`OSError` path, so it is inherited.
Disposition 05 rules that inheritance does not excuse the complete rule.

**Option C (complete).** Add `authority.py` to the boundary, changing only
`registered_producers`:

- Each of the three mapped typed reads is caught *per read*. The scan then carries on
  with every remaining check whose inputs are readable: remaining entries, the
  CONSUME-evidence check over the readable event files, and the G operation check
  once its G record is readable.
- A consistency failure still raises `IntegrityError` at once.
- The first deferred `ProducerRegistryUnavailable` is raised only after the whole scan.
- `_operational_boundary` also runs the scan when the current G's own entry is
  unavailable, ignoring only the deferred error.
- Nothing else changes: checks, messages, unmapped `Unavailable` (catalogue) and the
  other callers' code paths.

The other callers are `register_producer`, `assert_producer`, `consume_generation` and
`renew_before_generation`. They now see a positive `IntegrityError` instead of
`ProducerRegistryUnavailable` only when both conditions coexist. Both are
`IntegrityError` refusals there, and those callers have no outcome mapping.

```diff
     def registered_producers(self) -> dict:
         from .inventory import strict_private_json
         result = {}
+        deferred: ProducerRegistryUnavailable | None = None
         for path in sorted((self.root / "producer-roots").glob("*.json")):
-            with _producer_registry_read():
-                raw = regular_bytes(path)
+            try:
+                with _producer_registry_read():
+                    raw = regular_bytes(path)
+            except ProducerRegistryUnavailable as exc:
+                deferred = deferred or exc  # Disposition 05: readable entries are still checked
+                continue
             ... unchanged entry checks ...
-            with _producer_registry_read():
-                G = self.resolve(item["G"])["body"]
-            if (G["study_id"] != ... ):
-                raise IntegrityError("producer registry original G operation/source mismatch")
+            try:
+                with _producer_registry_read():
+                    G = self.resolve(item["G"])["body"]
+            except ProducerRegistryUnavailable as exc:
+                deferred = deferred or exc
+            else:
+                if (G["study_id"] != ... ):
+                    raise IntegrityError("producer registry original G operation/source mismatch")
             ... ref = artifact(raw, ...) unchanged ...
             for event_path in self.root.glob("event-*.json"):
-                with _producer_registry_read():
-                    event_raw = regular_bytes(event_path)
+                try:
+                    with _producer_registry_read():
+                        event_raw = regular_bytes(event_path)
+                except ProducerRegistryUnavailable as exc:
+                    deferred = deferred or exc
+                    continue
                 ... unchanged CONSUME check ...
             result[path.stem] = item
+        if deferred is not None:
+            raise deferred
         return result
```

**Option N (narrow).** Keep `private_verification.py` alone, as in §2.1. This closes
the demonstrated S7-IQ-F1 and every lead-enumerated case. The other-entry masking in
the table above would stay as a recorded residual. Any instruction to the Seal-08
qualifier to probe "combined positive-mismatch + unavailability states" would have to
exclude it explicitly. Otherwise the qualifier would likely rate it a blocker again.

**Recommendation: option C.** Its semantics are the literal Disposition 05 items 1 and
5 plus Scope 02 item 3. The change is confined to the error ordering of one scan. A
narrow reading is exactly how Seal 07 failed.

## 4. Return 2: S7-IQ-F2 contradicts four sealed Seal-07 cases

Every fault in these cases occurs inside `authority.protected` → `_check` before the
lease and action. Each case asserts the superseded `UNAVAILABLE` label. Under the §2.2
draft they would record `REFUSED_PRECONDITION`. The propagated `Unavailable` and every
other assertion in them still hold.

| # | Repository-root node ID | Fault location | Assertion |
| --- | --- | --- | --- |
| C1 | `engine/tests/test_v6_e9_v2_gate8_seal07.py::test_s7_operational_durable_objects_are_unavailable_without_read[event]` | `_state` reads the first `event-*.json` (non-regular) | line 126 `assert labels(study) == ["UNAVAILABLE"]` |
| C2 | `…::test_s7_operational_durable_objects_are_unavailable_without_read[active]` | `_state` reads `active.json` | line 126 |
| C3 | `…::test_s7_operational_durable_objects_are_unavailable_without_read[retained]` | `_state` → `resolve(S)` reads `evidence-records/<S>.json` | line 126 |
| C4 | `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py::test_R01_audited_source_checker_rejects_at_both_protected_checks[entry]` | `_check` → `source_check` (first pass) | line 456 `assert fixture.labels(study) == (["UNAVAILABLE"] if pass_number == 1 else ["PASS"])` |

The identities and ownership of the two affected functions:

- **Implementer module.** Module raw `09a7082a…`. The function spans lines 87-129,
  block SHA-256 `e0988ff2…`. Its other seven parameter cases (`registry`, `marker`,
  `payload`, `salt`, `audit`, `K`, `outcome`) are unaffected. C1–C3 share line 126.
  This module is the implementer's own.
- **Independent module.** Module raw `7861a563…`. The function spans lines 431-456,
  block SHA-256 `d4c857c7…`. Its `post-PASS-recheck` case stays `["PASS"]`. Only a
  new independent test-author context may edit this module.

**Proposed exceptions** (they need lead authorization; nothing has been edited):

- **E8-1.** The implementer replaces only the assertion at line 126. C1–C3 assert
  `["REFUSED_PRECONDITION"]`. All other parameter cases keep `["UNAVAILABLE"]`. The
  rest of the function stays byte-identical, including the no-open observer,
  `pytest.raises(pv.Unavailable)` and the restoration.
- **E8-2.** A new independent test-author context replaces only the `pass_number == 1`
  label in line 456 with `["REFUSED_PRECONDITION"]`. The rest of the function stays
  byte-identical, including the no-open observer and `len(calls) == 0`.

Both edits follow the Scope-03 exception procedure:

- retain the Seal-07 bytes in the Seal-07 manifests and evidence;
- record exact before/after line diffs and whole-module and block hashes, plus editor
  provenance;
- keep each module's prefix and suffix byte-identical.

The new Seal-08 modules carry the expanded F2 matrix.

The alternative is to leave both modules byte-identical and deselect C1–C4 from Seal-08
runs. That changes the qualification surface: the harness invocation, or a conftest.
It would also hide superseded assertions rather than restate them, so it is not
recommended.

## 5. Conflict sweep

Method: a read-only `rg` and AST/assertion review of all 27 Seal-07 manifested v2 test
modules. It covered:

- every `UNAVAILABLE` label assertion (45 occurrences across six modules);
- every outcome or reason assertion;
- every test that patches or populates `producer-roots` or calls
  `registered_producers`;
- every `match=` on registry, producer or consumption text.

Each `UNAVAILABLE` assertion was traced to the phase where its fault first raises.

| Group | Fault phase | Result under §2.1/§2.2 (and option C) |
| --- | --- | --- |
| Seal-07 implementer `…unavailable_without_read[event/active/retained]`; independent `test_R01…[entry]` | protected entry | **conflict C1–C4** |
| Seal-07 implementer `…[registry/marker/payload/salt/audit/K]`; F1 typed-scan cases (valid marker → `UNAVAILABLE`, `PASS`; marker mismatch → `FAILED_VERIFICATION`); catalogue-not-deferred case (F3) | verification | unchanged |
| Seal-07 independent `test_S7_DEV_F1_*` (5 triggers × marker forms/states); `E2`/`C15`/process-death `salt_missing`; `R09[entry]` (asserts only no PASS); `R03` and `R13` (direct calls, no labels) | verification or no label | unchanged |
| Seal-06 implementer and independent F1 registry/marker missing, unreadable, directory or read-error; wrong bytes; inconsistent restoration; unreadable listing (`PermissionError`); `marker_file_removed`, `marker_not_durable`, non-PASS `[UNAVAILABLE]`/`salt_missing` | verification | unchanged (classification); one reason text changes, which nothing matches |
| Gate-8 producer `w03` (deleted retained supplement or lead continuation), `w08` (payload, salt, original K) | verification (`_derive` / `derive_chain`) | unchanged |
| A2 consumer refusals (`verify_operational_w`, pre-U, U) | consumer | unchanged; only refusal is asserted |
| Renewal and producer registration (`registered_producers` on healthy registries) | n/a | unchanged under option C |

No sealed test asserts behavior for a wrong-bytes current-G entry under a deferred scan,
or for an inconsistent other-G entry.

## 6. Derived interpretations (the lead may strike these)

- **DV8-1.** "Protected verification state successfully entered" means the producer's
  existing `phase == "verification"`. That is, `_check` and the lease succeeded *and*
  `_preconditions` passed. Under this reading, unavailability inside `_preconditions`
  (outcomes, recovery provenance) is also `REFUSED_PRECONDITION`. This matches Revision
  02's "other unprovable continuation state: existing non-terminal refusal", and the
  lead's basis that verification "has not entered the state in which durable scientific
  evidence is being evaluated".
- **DV8-2.** A wrong-bytes current-G entry is reported before the scan runs (§2.1). One
  side effect: an *unmapped* `Unavailable` inside the scan, such as the frozen
  catalogue, can no longer mask it. The marker keeps its sealed position after the scan,
  so S7-IQ-F3's recorded behavior (marker mismatch + catalogue unavailable inside the
  scan → `UNAVAILABLE`) is unchanged, as is the sealed implementer test that asserts
  it. Disposition 05 item 7 and F3 remain record only.
- **DV8-3.** Option C does not wrap any further read. Unmapped `Unavailable` keeps
  propagating immediately, per item 7.

## 7. Decisions requested

| ID | Decision | Recommendation |
| --- | --- | --- |
| D8-01 | F1 boundary: option C (`private_verification.py` + `authority.registered_producers`) or option N (`private_verification.py` alone, other-entry masking recorded as a residual excluded from the qualifier's probe brief) | **C** |
| D8-02 | Authorize E8-1 (implementer, line 126 only, C1–C3) and E8-2 (new independent author, line 456 `pass_number == 1` label only, C4) | **Authorize both** |
| D8-03 | Confirm or strike DV8-1, DV8-2 and DV8-3 | Confirm |

Once these are ruled, the write-once Seal-08 scope can be frozen with:

- the implementation boundary: `private_verification.py`, plus `authority.py` under C;
- the qualification boundary:
  - the new `test_v6_e9_v2_gate8_seal08.py` and
    `test_v6_e9_v2_independent_gate8_seal08.py`;
  - E8-1 in `test_v6_e9_v2_gate8_seal07.py`;
  - E8-2 in `test_v6_e9_v2_independent_gate8_seal07.py`.

Every other manifested file stays byte-identical, including Scope 03, its amendment and
all Seal-06 modules. Candidate 31 then binds the repaired source and the new and edited
qualification bytes.

## 8. Proposed Seal-08 qualification outline

These are the implementer cases. The independent author derives its own cases from
Disposition 05 and the frozen scope, not from this list.

- **F1, lead-required.** For each typed scan trigger (other-G entry sorted first and
  last, G record, event file):
  - current-G wrong bytes (substituted, corrupt, re-encoded) → `FAILED_VERIFICATION`,
    then a retry after exact restoration is refused;
  - marker mismatch → `FAILED_VERIFICATION`;
  - no mismatch → `UNAVAILABLE`, then `PASS` after the exact condition clears;
  - current-G entry itself missing or non-regular, with a valid marker → `UNAVAILABLE`,
    then `PASS` after exact restoration;
  - the same with a mismatched marker → `FAILED_VERIFICATION`.
- **F1, option C only.**
  - An inconsistent other-G entry with an earlier typed-unavailable entry →
    `FAILED_VERIFICATION`; a retry is never `PASS`.
  - The same while the current-G entry is unavailable → `FAILED_VERIFICATION`.
  - The typed unavailability is still raised after a complete clean scan.
  - Other callers' refusal is unchanged.
- **F2.**
  - Every protected-entry fault (event, active, retained tuple record, source checker,
    adopted P, catalogue, `frozen_limitations`) → `REFUSED_PRECONDITION`. The action
    and verifier are not entered, and the caller still receives the typed
    `Unavailable`.
  - Each `_preconditions` fault (outcome, recovery provenance) →
    `REFUSED_PRECONDITION`.
  - Each verification-phase fault (registry, marker, payload, salt, audit, K, retained
    record) still → `UNAVAILABLE`.
  - A non-`Unavailable` error during verification still → `FAILED_VERIFICATION`.
  - A post-PASS recheck failure still produces no second outcome.
- **Prohibitions on every path:** no generation, entropy, salt, native execution or
  registration.

## 9. Not done and not authorized

- No scope freeze, implementation, test edit, candidate manifest, pytest run, seal,
  commit or push happened. Ruff and mypy were not run.
- Seal 07, candidate 30, Scope 03 and its amendment, and all prior records are
  unchanged.
- REAL entropy, operational generation, operational W, salt, native matches,
  operational publication, Q, Gate 7, operational O/V/A/R/B and real-study stale-lock
  clearance remain unauthorized.
- Status: execution is LOCKED; Gate-8 operational acceptance and Requirement C are NOT
  ESTABLISHED; Q is absent.
