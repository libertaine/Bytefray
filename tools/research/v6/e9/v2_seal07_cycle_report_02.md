# Seal-07 continuation: Seal 07 created, independent qualification FAIL (S7-IQ-F1 BLOCKER)

Recorded 2026-10-07 under the lead disposition for S7-DEV-B1 and S7-DEV-F1. That disposition is held as the
implementer's transcription `v2_seal07_lead_disposition_b1_f1_01.txt`, raw `820b8895…`. The machine record
`v2_seal07_cycle_report_02.json` (raw `bdc0436a…`) binds every file below by hash and governs this mirror.

All ten authorized steps ran:

- Seal 07 exists.
- The fresh independent reproduction **passed every run**.
- The qualifier nonetheless rated the qualification **FAIL** because of one BLOCKER, S7-IQ-F1: a frozen F1 precedence invariant fails on the sealed bytes.
- The implementer confirmed the BLOCKER by reading the sealed code.
- Nothing was fixed after sealing.
- Lead disposition is required.

## Records and identities

| Item | Identity | Raw SHA-256 |
| --- | --- | --- |
| Preservation supersession 01 | `v6-e9-v2-preservation-supersession-a82d0caccf3b` | `319528a4d7e29266a680e198acea9769229cef41aaf86693607e5044852b4661` |
| Scope-03 amendment 01 (B1-Q1) | `v6-e9-v2-gate8-scope-amendment-4088826751d2` | `3e5c1a4945a7b2f534d58a106cba7c6ed25d710edeffa877f1b3136564261961` |
| Bindings edit provenance | `v6-e9-v2-seal07-edit-provenance-a5e539c1f07c` | `8b142b04028bb468805a4a62034de4c6e9d128ae8dcdcf23107eda602f822461` |
| F1 correction provenance | `v6-e9-v2-seal07-f1-provenance-8f49ad314cca` | `b237966c463c619c0b2776c103253b36918cb8295ccc81ceba8d5c1376998450` |
| Candidate 30 implementation manifest (293 files) | attempt_30 = final_07 | `fa644d180d2de792f384f0dbd47acd41d2366ee9000dc75a4843c07b1aab612e` |
| Candidate 30 qualification manifest (34 files) | attempt_30 = final_07 | `9c909545db1e0276c5253fbb9a30dad5261e22259fc79c47fe50c9679a1a6332` |
| **Seal 07** (`v2_final_manifest_seal_07.json`) | instrument `v6-e9-instrument-v2-3c2bda92b3c0` | `fe2e9a4bd27d88418f33c0afd18f103ffa9ffc1c566d2c8c0be5554a48a59c29` |
| Auditor reproduction output | same instrument, PASS | `8b957c54906749acec1e375d1f2d3285d2a90571537bb7fd951114b100049728` |
| Independent qualifier report 01 | FAIL | `a7336a755d52392e467372341c8789cfa8eb449811efddedbf91539197817148` |
| Qualification evidence 07 | `v6-e9-v2-qualification-evidence-cdb88a31bfbc` | `51604190677ea9595d9c4b217a0164342efd6cf6d99e6362ab27f1b8cdc6d242` |
| Tooling attempt history 02 | `v6-e9-v2-attempt-history-a494ee4c9735` | `6bebcdd8cc3c80e66a9242dbb0e42106e16f1ae3f1b2c81a9d80533214bd936d` |

The instrument digest is `3c2bda92b3c078456c6fd08f6bc52882e96d8251714b22d3379b7c5c3a3783d4`. It was
re-derived independently by the qualifier and by the auditor script. The readable mirrors are
`docs/research/v6/V6_E9_V2_INHERITED_PRESERVATION_SUPERSESSION_01.md` and
`docs/research/v6/V6_E9_GATE8_SCOPE_03_AMENDMENT_01.md`.

## Exact bindings-test diff (B1-Q1)

The function was rewritten by a fresh independent author, agent-a1fefe5ca2b160867, whose transcript hashes to `f718a165…`.

- The module hash went from `6b91043e…` to `3cc2d65f…`.
- The function block, which now spans lines 48–114, went from `cd7287cf…` to `8bb529db…`.
- The prefix and suffix are byte-identical, as is every other block.
- The `git diff HEAD` SHA-256 is `528d3b18…`.

```diff
@@ -65,9 +65,53 @@ def test_separate_adoption_attestation_exact_review_and_unchanged_body():
         assert len(z.namelist()) == len(set(z.namelist())) == 20
         for path in z.namelist():
             assert z.read(path) == (ROOT / path).read_bytes()
-    preserved = json.loads((E9 / "v2_inherited_preservation_manifest_01.json").read_bytes())
-    for path, expected in preserved["tracked_files"].items():
-        assert independent_sha((ROOT / path).read_bytes()) == expected
+    adoption_commit = "2dd8f69c5c6feb5f3a7d8fc0eb81b0c06802dee2"
+    adoption_blob = "7064b0bb9d533b312b45f0c368610a64777ec8b6"
+    adoption_pin = "d26332b37bbcac74a5e369317df33cbbecd4042f4ca6867770e38a54307bfd86"
+    checkpoint_commit = "e035def989dfc5e26ae3eb2c9ccfd16aed54b66c"
+    checkpoint_blob = "89bba2ee71b70188107be24fd918c078b0b6ae76"
+    superseding_sha = "97128feeef25cbe98af6770173d09a809b1c0f626ec2a5ac558236aaf4b99555"
+    manifest_raw = (E9 / "v2_inherited_preservation_manifest_01.json").read_bytes()
+    assert independent_sha(manifest_raw) == "b1f86c1d9b59be0f8841bf1b587b7a88d3ffb7bed34cffa476ef582606660147"
+    preserved = json.loads(manifest_raw)
+    pins = preserved["tracked_files"]
+    assert pins[".gitattributes"] == adoption_pin
+    record_raw = (E9 / "v2_inherited_preservation_supersession_01.json").read_bytes()
+    assert independent_sha(record_raw) == "319528a4d7e29266a680e198acea9769229cef41aaf86693607e5044852b4661"
+    record = json.loads(record_raw)
+    assert record_raw == independent_json(record) + b"\n"
+    assert independent_sha(independent_json(record["body"])) == record["digest"]
+    assert record["digest"] == "a82d0caccf3b131d4ee853bac1174868db338b6b71d032be33c2677178dd4e9f"
+    assert record["identity"] == "v6-e9-v2-preservation-supersession-a82d0caccf3b"
+    original = record["body"]["original_manifest"]
+    assert original["path"] == "tools/research/v6/e9/v2_inherited_preservation_manifest_01.json"
+    assert original["sha256_raw"] == independent_sha(manifest_raw)
+    assert original["tracked_file_pins"] == len(pins) == 1203
+    assert record["body"]["semantics"]["superseded_paths"] == [".gitattributes"]
+    entry = record["body"]["superseded_entry"]
+    assert entry["path"] == ".gitattributes"
+    assert entry["adoption_pin_sha256_raw"] == adoption_pin
+    assert entry["superseding_bytes"]["commit_parent"] == adoption_commit
+    assert independent_sha(entry["change"]["diff_utf8"].encode("utf-8")) == entry["change"]["diff_sha256_raw"]
+    parents = subprocess.check_output(["git", "rev-list", "--parents", "-n", "1", checkpoint_commit],
+                                      cwd=ROOT, text=True)
+    assert parents == f"{checkpoint_commit} {adoption_commit}\n"
+    for side, commit, blob, sha in (("adoption_bytes", adoption_commit, adoption_blob, adoption_pin),
+                                    ("superseding_bytes", checkpoint_commit, checkpoint_blob, superseding_sha)):
+        assert (entry[side]["commit"], entry[side]["git_blob"], entry[side]["sha256_raw"]) == (commit, blob, sha)
+        tree_entry = subprocess.check_output(["git", "rev-parse", "--verify", f"{commit}:.gitattributes"],
+                                             cwd=ROOT, text=True)
+        assert tree_entry == f"{blob}\n"
+        blob_raw = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=ROOT)
+        assert hashlib.sha1(b"blob " + str(len(blob_raw)).encode() + b"\x00" + blob_raw).hexdigest() == blob
+        assert independent_sha(blob_raw) == sha
+        assert blob_raw == entry[side]["utf8"].encode("utf-8")
+    current = (ROOT / ".gitattributes").read_bytes()
+    assert independent_sha(current) == superseding_sha
+    assert current == subprocess.check_output(["git", "cat-file", "blob", checkpoint_blob], cwd=ROOT)
+    actual = {path: independent_sha((ROOT / path).read_bytes()) for path in pins}
+    mismatched = {path: digest for path, digest in actual.items() if digest != pins[path]}
+    assert mismatched == {".gitattributes": superseding_sha}
```

## S7-DEV-F1 implementation diff (against candidate 29)

`authority.py` changed from `d9ede34e…` to `f9c88157…`, and `private_verification.py` from `8bce3300…` to
`5bb4cc37…`. The implementer made both changes.

```diff
--- a/tools/research/v6/e9/v2/authority.py (candidate 29)
+++ b/tools/research/v6/e9/v2/authority.py
@@ -35 +35,15 @@
 T = TypeVar("T")
+
+
+class ProducerRegistryUnavailable(DurableUnavailable):
+    """S7-DEV-F1: a registered_producers read of an entry, its G record or an event file is unavailable."""
+
+
+@contextmanager
+def _producer_registry_read() -> Iterator[None]:
+    """Type only these mapped reads so F1 can defer them; any other Unavailable stays immediate."""
+    try:
+        yield
+    except DurableUnavailable as exc:
+        raise ProducerRegistryUnavailable(*exc.args) from exc
+
+
 GENESIS = "genesis"
@@ registered_producers
-            raw = regular_bytes(path)
+            with _producer_registry_read():
+                raw = regular_bytes(path)
@@
-            G = self.resolve(item["G"])["body"]
+            with _producer_registry_read():
+                G = self.resolve(item["G"])["body"]
@@
-                event = json.loads(regular_bytes(event_path))["body"]
+                with _producer_registry_read():
+                    event_raw = regular_bytes(event_path)
+                event = json.loads(event_raw)["body"]
--- a/tools/research/v6/e9/v2/private_verification.py (candidate 29)
+++ b/tools/research/v6/e9/v2/private_verification.py
-from .authority import THROUGH_G, AuthorityLog, Lease, durable_bytes
+from .authority import THROUGH_G, AuthorityLog, Lease, ProducerRegistryUnavailable, durable_bytes
@@ _operational_boundary
-        except OSError:
+        except (OSError, ProducerRegistryUnavailable):
+            # S7-DEV-F1: deferred so a present first-raw marker is still checked for a mismatch.
             unavailable.append("producer registry")
```

The complete unified diffs are stored inside `v2_seal07_f1_correction_provenance_01.json`.

## Regression provenance

- **Implementer cases.** These are in `test_v6_e9_v2_gate8_seal07.py`, whose hash went from `b15ba4b3…` to `09a7082a…`. There are seven cases:
  - three combined cases (marker mismatch while a registry read fails typed), which give FAILED_VERIFICATION;
  - three valid-marker cases, which give UNAVAILABLE and then PASS once the condition clears;
  - one case the implementer derived from the ruling: a frozen-catalogue Unavailable raised inside the scan is not deferred.
- **Independent cases.** These were written by a fresh author, agent-a5481bd69b3ff921f, transcript `d84cc517…`. The earlier Codex author context could not be resumed from Claude Code. The author appended 25 cases to `test_v6_e9_v2_independent_gate8_seal07.py`. The first 1112 lines of that module are unchanged and still hash to `5463ca6e…`; the appended block hashes to `18fff291…`.
- **Transcript audits.** Neither author read the other side's tests or ran pytest. The disclosures are recorded: the F1 author read the live implementation sources, and it wrote a staging copy outside the repository.

## Validation (candidate 30 = final_07)

| Check | Implementer | Independent qualifier |
| --- | --- | --- |
| Full 27-module suite | 1237 collected, 1231 passed, 6 skipped, 0 failed, 0 errors (59:23) | 1237 collected, 1231 passed, 6 skipped, 0 failed, 0 errors (56 min) |
| Native WSL supplement (the 6 Windows skips) | 4/4 + 2/2 | 6/6 |
| Ruff; mypy engine; mypy client | pass; pass (97 files); pass (16 files) | pass; pass (97 files); pass (16 files) |
| Bindings / inherited preservation | 9/9 (candidate 29 had 8 passed, 1 failed) | included in the full run |
| Focused Seal-07 + Seal-06 | implementer 117 passed, 2 skipped; independent 350 passed, 4 skipped | included in the full run |
| Targeted F1 | all 7 implementer and 25 independent new cases pass; all prior F1 cases pass | included in the full run |

## Findings (qualifier report 01; for lead disposition)

- **S7-IQ-F1: BLOCKER.** The implementer confirmed it. At `private_verification.py:286-293`, the own-G registry byte comparison `registry != producers[0]` only runs in the `else` branch.
  - **Effect.** When the scan fails with a deferred, typed unavailability, a present registry entry with wrong bytes is recorded UNAVAILABLE instead of FAILED_VERIFICATION, and a later PASS can be reached.
  - **Rules contradicted.** Scope 02 F1 order item 3, and the ruling's last precedence bullet: "any other existing positive mismatch evidence retains its frozen failure classification".
  - **Inheritance.** For other-G and event-file scan failures, Seal 06 already masked the mismatch through its OSError branch. For the G-record read, Seal 06 gave FAILED_VERIFICATION, so on that path this is a Seal-07 regression.
  - **Implementer error.** The F1 correction kept the old branch structure. The F1 provenance record's statement that positive mismatch evidence keeps its frozen classification is incorrect for this case, and neither author's tests covered it.
  - **Alternative reading.** The qualifier notes that ruling §3 bullet 2, read alone, could permit the observed result.
- **S7-IQ-F2: NON-BLOCKING.** Typed unavailability at protected entry or in the preconditions is recorded UNAVAILABLE, whereas Planning Revision 02 §3 says REFUSED_PRECONDITION. Both outcomes are non-terminal, and both authors' tests encode UNAVAILABLE. This behavior was inherited from candidate 29.
- **S7-IQ-F3 to F10: NOTE.**
  - F3: the implementer's derived catalogue-not-deferred case.
  - F4: after any authority event, recovery provenance blocks interruptions that occurred before any output was published.
  - F5: some OSError handlers can no longer fire, and the reason text for unavailable private evidence changed.
  - F6: an ordinary race during a read is classified as an integrity failure.
  - F7: the recorded durability limits (no Windows directory flush; the retained candidate is a hard link).
  - F8: no repository record binds the original Seal-07 implementation authorization.
  - F9: the independent authors' disclosures.
  - F10: the bindings test depends on the git object database.

No source or test byte changed after sealing. Seal 07 must not be used operationally. Any remedy for
S7-IQ-F1 needs the lead's disposition, then a new scope or exception, a new candidate and a new seal.

## Preservation, status and confirmation

- **Rehash.** The final rehash matches 327/327 manifested files. Seal 06, candidate 29 and all earlier records are unchanged.
- **Inherited pins.** 1202 of 1203 match; `.gitattributes` is the only exception, covered by the supersession.
- **Git.** HEAD is `e035def989dfc5e26ae3eb2c9ccfd16aed54b66c`, the index is empty, and nothing was committed or pushed. The final status is saved as `v2_seal07_git_status_final_02.txt`, raw `8654d52c…`, 78 lines.
- **Private backup** (outside the checkout, a new separate directory):
  - path: `D:\Projects\BATTLE2-private-evidence\v6-e9-seal07-transcript-provenance\`;
  - size: 7267 files, 173,564,065 bytes, 0 verification failures;
  - contents: the implementer, author and qualifier transcripts, the ten Codex rollouts, `cache/e9-seal07-*`, and the qualifier's work and probe outputs;
  - there is no off-machine copy.
- **No operational E9 work occurred:**
  - no REAL entropy, operational generation, operational W or salt creation;
  - no native matches or operational publication;
  - no Q, Gate 7 or operational O/V/A/R/B;
  - no real-study stale-lock clearance.

Execution remains LOCKED. Gate-8 operational acceptance and Requirement C remain NOT ESTABLISHED, and Q is absent.
