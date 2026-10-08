# E9 v2 Seal-08 plan, revision 02 (lead rulings incorporated)

Recorded 2026-10-08. This revision folds the research lead's Seal-08 scope rulings
D8-01, D8-02 and D8-03 into the Seal-08 plan. The rulings are transcribed verbatim in
`tools/research/v6/e9/v2_seal08_lead_scope_rulings_01.txt`, raw SHA-256
`d3a1b02840b32a1f618fb7711342aca72144aa6bd6d898a3c5dcc954b6273bb8`.

[Plan 01](V6_E9_SEAL08_PLAN_01.md) (raw `6dfd2ae2…`) is unchanged and remains bound by
the scope-drafting record. This revision adds to it and edits nothing in it. Where the
two differ, this revision and the lead's rulings govern. The write-once Seal-08 scope
`tools/research/v6/e9/v2_gate8_scope_04.json` freezes this plan. Its readable mirror is
[V6_E9_GATE8_SCOPE_04.md](V6_E9_GATE8_SCOPE_04.md).

## 1. Rulings incorporated

| ID | Ruling | Effect on the plan |
| --- | --- | --- |
| D8-01 | **Option C approved; option N rejected** | `authority.py` joins the boundary, limited to the `registered_producers` scan ordering. The qualifier is not told to exclude the other-entry masking case. |
| D8-02 | **E8-1 and E8-2 authorized exactly** | The implementer changes C1–C3 (`[event]`, `[active]`, `[retained]`) in the Seal-07 implementer module. A new independent test-author context changes C4 (`R01[entry]`) in the Seal-07 independent module. No other existing test changes. |
| D8-03 | **DV8-1 and DV8-2 confirmed; DV8-3 confirmed as a scope constraint** | Unavailability before protected verification is entered (protected entry and `_preconditions`) is `REFUSED_PRECONDITION`. S7-IQ-F3 is neither repaired nor broadened. Option C adds no registry read. |

The status is unchanged: Seal 07 is INDEPENDENT REPRODUCTION FAIL, S7-IQ-F1 is the
Seal-08 blocker, S7-IQ-F2 is the Seal-08 repair, and S7-IQ-F3–F10 are record only.

## 2. Implementation

The implementation boundary is exactly two files:

- `tools/research/v6/e9/v2/authority.py`, only `AuthorityLog.registered_producers`
  (sealed lines 274–304);
- `tools/research/v6/e9/v2/private_verification.py`, only `_operational_boundary`
  (sealed lines 254–302) and the outcome mapping in `produce_private_verification`
  (sealed lines 518–529).

No signature, message text, check, read site or other caller changes. The
`_producer_registry_read` mapping stays the same three reads.

### 2.1 `registered_producers`: deferred unavailability, complete scan (D8-01)

The traversal, its order, its reads and its checks are unchanged. Only the control flow
around the three mapped reads changes:

1. A mapped read that raises `ProducerRegistryUnavailable` is remembered (the first one
   only) instead of ending the scan.
2. The scan continues with every check whose inputs are readable:
   - an unavailable entry is skipped, because nothing about its contents can be known;
   - an unavailable G record skips only that entry's G-operation check;
   - an unavailable event file skips only that event's CONSUME check.
3. Any positive consistency or identity mismatch raises its existing `IntegrityError` at
   once, as before.
4. After a complete scan with a remembered unavailability, the first remembered
   `ProducerRegistryUnavailable` is raised. That is the same exception object, with the
   same message, that Seal 07 raised at that read.

**DV8-4 (implementer-derived; the lead may strike it).** After an unavailability has
been remembered, an exception that is *not* positive mismatch evidence ends the scan
with the remembered `ProducerRegistryUnavailable`. Positive mismatch evidence means an
`IntegrityError` that is not a `DurableUnavailable`. Examples of exceptions that are not
positive evidence:

- an unmapped `Unavailable`, such as the frozen catalogue read inside `validate_refs`;
- a parse error from a malformed event file.

The scan stops exactly where Seal 07 stopped and reports what Seal 07 reported. The
unmapped error is neither deferred nor converted; it only cannot replace the condition
that was already deferred.

Without DV8-4 the combined state "earlier mapped unavailability + later catalogue
`Unavailable` + marker mismatch" would change from Seal 07's `FAILED_VERIFICATION` to
`UNAVAILABLE`. That would be a new masking, in a state where no later positive mismatch
was discovered. D8-01 allows a behavior change only where "an earlier unavailable read
previously prevented discovery of later positive mismatch evidence". DV8-2 forbids
broadening S7-IQ-F3.

The resulting contract: if no mapped read is unavailable, the scan is byte-for-byte the
Seal-07 scan. If one is, the result is the Seal-07 result unless a positive mismatch is
found later, in which case that mismatch raises.

Intended change (unchanged lines elided):

```diff
     def registered_producers(self) -> dict:
+        """... D8-01 (Seal 08) ordering, see the docstring ..."""
         from .inventory import strict_private_json
         result = {}
-        for path in sorted((self.root / "producer-roots").glob("*.json")):
-            with _producer_registry_read():
-                raw = regular_bytes(path)
+        deferred: ProducerRegistryUnavailable | None = None
+        try:
+            for path in sorted((self.root / "producer-roots").glob("*.json")):
+                try:
+                    with _producer_registry_read():
+                        raw = regular_bytes(path)
+                except ProducerRegistryUnavailable as exc:
+                    deferred = deferred or exc
+                    continue
                 ... unchanged entry checks (re-indented) ...
-            with _producer_registry_read():
-                G = self.resolve(item["G"])["body"]
-            if (G["study_id"] != ...):
-                raise IntegrityError("producer registry original G operation/source mismatch")
+                try:
+                    with _producer_registry_read():
+                        G = self.resolve(item["G"])["body"]
+                except ProducerRegistryUnavailable as exc:
+                    deferred = deferred or exc
+                else:
+                    if (G["study_id"] != ...):
+                        raise IntegrityError("producer registry original G operation/source mismatch")
                 ... ref = artifact(raw, ...) unchanged ...
-            for event_path in self.root.glob("event-*.json"):
-                with _producer_registry_read():
-                    event_raw = regular_bytes(event_path)
+                for event_path in self.root.glob("event-*.json"):
+                    try:
+                        with _producer_registry_read():
+                            event_raw = regular_bytes(event_path)
+                    except ProducerRegistryUnavailable as exc:
+                        deferred = deferred or exc
+                        continue
                     ... unchanged CONSUME check ...
-            result[path.stem] = item
+                result[path.stem] = item
+        except Exception as exc:
+            if deferred is None or (isinstance(exc, IntegrityError)
+                                    and not isinstance(exc, DurableUnavailable)):
+                raise
+            raise deferred  # DV8-4: the scan ends where it previously stopped
+        if deferred is not None:
+            raise deferred
         return result
```

**Other callers.** These are `register_producer`, `assert_producer`,
`renew_before_generation`, `consume_generation` and `commitment.study_private_values`.
Their single-condition behavior is unchanged. In the combined state "unavailable +
later positive mismatch" they now receive the positive `IntegrityError` instead of
`ProducerRegistryUnavailable`. Both are `IntegrityError` refusals, and none of these
callers distinguishes the two.

### 2.2 `_operational_boundary`: the complete F1 ordering

```diff
     mismatched, unavailable = [], []
     registry = _durable(authority.root / "producer-roots" / (G["digest"] + ".json"))
     if registry is None:
         unavailable.append("producer registry")
+    elif registry != producers[0]:
+        # S7-IQ-F1: this G's own durable entry is positive evidence by itself, never left to the scan.
+        mismatched.append("generation boundary does not bind the registered producer root")
     else:
         try:
             registered = authority.registered_producers().get(G["digest"])
         except (OSError, ProducerRegistryUnavailable):
             unavailable.append("producer registry")
         else:
-            if registry != producers[0] or registered is None or _raw(registered) != producers[0]:
+            if registered is None or _raw(registered) != producers[0]:
                 mismatched.append("generation boundary does not bind the registered producer root")
     marker = ... unchanged ...
     if mismatched:
         raise IntegrityError(mismatched[0])
+    if registry is None:
+        # D8-01: this G's entry is unavailable, but every other readable registry entry is still
+        # checked; a positive mismatch there raises, and only the scan's unavailability is ignored.
+        try:
+            authority.registered_producers()
+        except (OSError, ProducerRegistryUnavailable):
+            pass
     if unavailable:
         raise Unavailable("durable " + " and ".join(unavailable) + " unavailable")
```

The resulting ordering is the one D8-01 sets:

1. A current-G registry mismatch is `FAILED_VERIFICATION`. It is checked first and never
   depends on the scan.
2. A marker mismatch is `FAILED_VERIFICATION`. The marker keeps its sealed position after
   the scan when the current-G entry is readable (DV8-2).
3. Any other available registry-entry consistency mismatch is `FAILED_VERIFICATION`.
   This covers the scan in both branches, under §2.1.
4. Event or registry unavailability with no available positive mismatch gives the
   availability classification.
5. With no mismatch and no unavailability, processing continues normally.

**DV8-5 (implementer-derived; the lead may strike it).** Running the scan when this G's
own entry is unavailable is the fourth bullet of the approved option C (Plan 01 §3:
"`_operational_boundary` also runs the scan when the current G's own entry is
unavailable, ignoring only the deferred error"). It runs after the marker comparison,
and only when no positive mismatch is already known.

That placement keeps "current-G entry unavailable + marker mismatch" at
`FAILED_VERIFICATION` even when the scan would meet an unmapped `Unavailable` (DV8-2: no
S7-IQ-F3 broadening). In that branch an unmapped `Unavailable` from the scan propagates
as `Unavailable`, which is the same `UNAVAILABLE` classification as before.

The scan adds no read site. It consults exactly the objects of the unchanged traversal,
which are the objects the boundary already consults in every state where this G's entry
is readable (DV8-3). Seal 07 skipped the scan in this one state. That skipped scan is
the masking that D8-01 closes.

**Combined-state outcomes at the boundary** (classification; reasons are value-free):

| State | Seal 07 | Seal 08 |
| --- | --- | --- |
| Current-G wrong bytes + any typed scan unavailability | `UNAVAILABLE`, then `PASS` reachable (S7-IQ-F1) | `FAILED_VERIFICATION` |
| Earlier typed-unavailable entry + later inconsistent entry | `UNAVAILABLE`, then `PASS` reachable | `FAILED_VERIFICATION` |
| Typed G-record or event-file unavailability + another inconsistent entry | `UNAVAILABLE` | `FAILED_VERIFICATION` |
| Current-G entry unavailable + another inconsistent entry | `UNAVAILABLE` (scan skipped) | `FAILED_VERIFICATION` |
| Marker mismatch + any scan or current-G unavailability | `FAILED_VERIFICATION` | unchanged |
| Typed scan unavailability, no mismatch anywhere | `UNAVAILABLE`; `PASS` after exact restoration | unchanged |
| Current-G entry unavailable alone | `UNAVAILABLE`; `PASS` after exact restoration | unchanged |
| Typed unavailability + later unmapped `Unavailable` + marker mismatch | `FAILED_VERIFICATION` | unchanged (DV8-4) |
| Unmapped `Unavailable` in the scan with no earlier deferral (S7-IQ-F3) | `UNAVAILABLE` | unchanged (record only) |
| Any single mismatch alone | `FAILED_VERIFICATION` | unchanged; a current-G wrong-bytes reason now reads "generation boundary does not bind the registered producer root" |
| Clean registry and marker | normal | unchanged |

A discovered positive mismatch stays terminal through the existing `_preconditions`
"already failed" refusal. A pure availability condition recovers only when the exact
evidence returns.

### 2.3 S7-IQ-F2: outcome mapping (DV8-1 confirmed)

```diff
-        if isinstance(exc, Unavailable):
-            outcome = "UNAVAILABLE"
-        elif isinstance(exc, Refused) or phase != "verification":
+        if isinstance(exc, Refused) or phase != "verification":
+            # S7-IQ-F2: until protected verification has been entered, unavailability too is a
+            # refused precondition, never a verification-stage outcome.
             outcome = "REFUSED_PRECONDITION"
+        elif isinstance(exc, Unavailable):
+            outcome = "UNAVAILABLE"
         else:
             outcome = "FAILED_VERIFICATION"
```

`phase` becomes `"verification"` only after `authority.protected` has crossed the entry
boundary (`_check`, lease) and `_preconditions` has passed. That is the confirmed DV8-1
meaning of "protected verification entered". The propagated exception is unchanged, so
the caller still receives the typed `Unavailable`.

| Where the typed `Unavailable` arises | Seal 07 | Seal 08 |
| --- | --- | --- |
| `_begin` (before the `try`) | no outcome | unchanged |
| Protected entry: `_check` / `_state` (event files, `active.json`, retained tuple records), source checker, adopted P, catalogue, `frozen_limitations` | `UNAVAILABLE` | **`REFUSED_PRECONDITION`** |
| `_preconditions`: retained O/S/G records, `_outcomes`, `_recovery` provenance, `_durable_log` | `UNAVAILABLE` | **`REFUSED_PRECONDITION`** |
| `_derive` (verification): registry, marker, retained private evidence, records, events and catalogue read during verification | `UNAVAILABLE` | unchanged |
| Write phase and post-PASS recheck | no outcome (re-raised) | unchanged |

Not every `Unavailable` becomes `REFUSED_PRECONDITION`. A `Refused` or a non-`Unavailable`
error keeps its existing classification in every phase.

## 3. Legacy qualification exceptions (D8-02)

Both modules keep their Seal-07 bytes in the Seal-07 manifests, seal and evidence. Each
edit records the exact before/after module and block hashes, the diff and the editor's
provenance. Every byte outside the stated lines stays identical.

| ID | Module (Seal-07 raw) | Function (lines, block raw) | Permitted change | Editor |
| --- | --- | --- | --- | --- |
| E8-1 (C1–C3) | `engine/tests/test_v6_e9_v2_gate8_seal07.py` (`09a7082a…`) | `test_s7_operational_durable_objects_are_unavailable_without_read` (87–129, `e0988ff2…`) | Replace only line 126, `assert labels(study) == ["UNAVAILABLE"]`, with an assertion (at most two physical lines) expecting `["REFUSED_PRECONDITION"]` for `where` in `event`, `active` and `retained`, and `["UNAVAILABLE"]` for every other parameter it covered. The `if where != "outcome":` guard and every other line stay byte-identical. | implementer |
| E8-2 (C4) | `engine/tests/test_v6_e9_v2_independent_gate8_seal07.py` (`7861a563…`) | `test_R01_audited_source_checker_rejects_at_both_protected_checks` (431–456, `d4c857c7…`) | In line 456 replace only the `pass_number == 1` label `["UNAVAILABLE"]` with `["REFUSED_PRECONDITION"]`. The `["PASS"]` branch, the call-count and no-open assertions, and every other line stay byte-identical. | a new independent test-author context |

## 4. New qualification

### 4.1 Implementer module `engine/tests/test_v6_e9_v2_gate8_seal08.py`

- **F1 combined ordering.** The typed scan triggers are:
  - a non-regular other-G entry sorted first (`0…0.json`);
  - a non-regular other-G entry sorted last (`f…f.json`);
  - the G record;
  - every event file.

  The cases:
  - Current-G wrong bytes (substituted, corrupt, re-encoded) with each trigger give
    `FAILED_VERIFICATION`. Retry after exact restoration and fault removal is refused as
    "already failed".
  - A marker mismatch with each trigger, and with the current-G entry unavailable, gives
    `FAILED_VERIFICATION`.
  - Each trigger with no mismatch gives `UNAVAILABLE`, then `PASS` after the exact
    condition clears.
  - Earlier `0…0.json` unavailable + a later inconsistent entry gives
    `FAILED_VERIFICATION`. The inconsistent entry takes three forms: a foreign stem,
    corrupt bytes, or an unknown key. Repairing the unavailable entry never yields
    `PASS`.
  - G-record or event-file unavailability + an inconsistent entry gives
    `FAILED_VERIFICATION`.
  - Current-G entry unavailable + an inconsistent entry gives `FAILED_VERIFICATION`.
  - Current-G entry unavailable alone gives `UNAVAILABLE`, then `PASS`.
- **Scan contract, tested directly.**
  - A clean registry gives the same mapping.
  - A single typed unavailability raises the first `ProducerRegistryUnavailable` after
    every later entry was examined.
  - A mismatch before or after an unavailability raises the mismatch.
  - DV8-4: a later unmapped `Unavailable` raises the deferred error.
  - A faulted scan reads only paths that the healthy scan reads (DV8-3).
  - Other callers (`assert_producer`) keep their single-condition refusal.
- **F2.**
  - Protected-entry faults give `REFUSED_PRECONDITION`. The faults are an event file,
    `active.json`, a retained tuple record, the source checker, and the catalogue at
    entry.
  - `_preconditions` faults (an outcome file, retained O/S/G records) give
    `REFUSED_PRECONDITION`.
  - Verification-phase faults (registry, marker, payload, salt, audit, K) give
    `UNAVAILABLE`.
  - A non-`Unavailable` verification error gives `FAILED_VERIFICATION`. A `Refused`
    tail gives `REFUSED_PRECONDITION`.
  - In every case the caller still receives the typed `Unavailable`, and neither the
    verifier nor the generator is entered. The refusal is non-terminal: `PASS` follows
    exact restoration.
- **Prohibitions on every path:** no generation, entropy, salt, native match or
  registration.

### 4.2 Independent module `engine/tests/test_v6_e9_v2_independent_gate8_seal08.py`

A new independent test-author context writes this module. It works from Disposition 05,
the lead's rulings, Planning Revision 02 §3 and this frozen scope. It does not read the
implementer's Seal-08 module. It must cover at least the D8-01 minimum list:

- an earlier-sorting unavailable entry + a later consistency mismatch;
- an earlier-sorting unavailable entry with no mismatch;
- an event file unavailable + another registry mismatch;
- current-G wrong bytes + scan unavailability;
- a marker mismatch + scan unavailability;
- both recovery distinctions;
- the S7-IQ-F2 protected-entry / `_preconditions` / verification-phase distinction.

Its transcript provenance is retained privately, and only its hash is made public.

## 5. Candidates and validation

- Candidate 30 = final_07 is immutable historical evidence.
- Candidate 31 binds the repaired source, the two new modules and the E8-1/E8-2 edits.
  It has 293 implementation files and 36 qualification files under the unchanged
  manifest rule.
- Any later source or test change needs candidate 32, and so on. No manifest is ever
  overwritten, and every failed or interrupted attempt is retained.

Validation runs fresh through `qualification_run` only, and sequentially:

1. Seal-08 implementer focus.
2. Seal-08 independent focus.
3. All prior Gate-8 modules, including the Seal-06 and Seal-07 modules.
4. The full applicable V2 suite (29 modules), with complete counts.
5. A WSL native POSIX supplement for every Windows skip.
6. Ruff, mypy engine and mypy client.
7. The bindings / inherited-preservation module.

The cycle seals only if every check passes on one exact candidate pair.

## 6. Sealing and independent reproduction

1. Write `final_08` manifests as byte-identical copies of the passing candidate pair.
2. Rehash immediately before sealing.
3. Write `v2_final_manifest_seal_08.json` once and compute the instrument identity.
4. Change no source or test byte after sealing.
5. Back up the implementer, author and qualifier transcripts privately in a new
   directory.
6. A fresh independent qualifier context reproduces from the sealed manifests. It
   explicitly probes combined unavailability + later positive-mismatch ordering beyond
   the named regression tests, including the other-entry masking case.

A post-seal blocker preserves Seal 08 and goes back to the lead.

## 7. Stop conditions

Work stops and returns to the lead, without a workaround, if any of these occurs:

- another implementation file becomes necessary;
- another existing sealed test must change;
- a frozen requirement conflicts with the rulings;
- option C turns out to need a new evidence read or a change to which registry objects
  the traversal consults.

## 8. Not authorized

None of the following is authorized:

- REAL entropy, operational generation, operational W, salt, native matches or
  operational publication;
- Q, Gate 7 or operational O/V/A/R/B;
- real-study stale-lock clearance;
- commit or push.

Execution is LOCKED. Gate-8 operational acceptance and Requirement C are NOT
ESTABLISHED. Q is absent.
