# E9 historical scope and coverage decision — 2026-10-03

**Coverage incomplete; generation LOCKED.** The available evidence supports
an evidence-bound **partial Route A manifest**, with finite containment checks
for identified executions. It supports neither an authoritative exhaustive
qualification manifest nor a usable whole-scope Route B superset. Requirement C
remains **NOT ESTABLISHED**. Seed generation, commitment publication and payoff
execution remain **UNAUTHORIZED**.

The governing scope is authoritative because it comes from frozen Draft 3.
The records here are a verified assessment of available coverage; the coding
agent is their recorder, not an authority attesting to historical completeness.
No responsible custodian's exhaustive-history declaration was supplied or
found in the inspected records. No one was contacted.

## Governing requirement and temporal scope

[Draft 3 §7](V6_E9_OBSERVATION_DRIVEN_ALLOCATION_PREREGISTRATION_DRAFT.md)
requires E6 and E8 experimental match seeds and **all prior qualification match
seeds**, including harness defaults and derived match-seed selections. Policy
RNG substreams are excluded from the match-seed obligation. The inventory must
be built and verified before generation, identify source records and
qualification coverage, and keep generation locked when completeness cannot
be established.

There is no authorized V6-only, freeze-date, instrument-date or retained-log
cutoff. Relevant project qualification includes regression, development,
capability, manual/release/CI smoke and compatibility activity that executes
matches, including failed, interrupted, partial and repeated executions.
Qualification matches in older studies remain relevant regardless of study
label. Pure readers, synthetic metadata creation and analysis RNG have no
match-seed obligation at their proved bound sites; containing executions must
be assessed separately.

The upper boundary is immediately before a later separately authorized
generation, after the exclusion inventory is frozen. Any intervening
qualification matches must be covered too. The earliest retained Git root
records migration of pre-existing files on 2025-09-29; it does not establish
when qualification began. Earlier activity remains unknown.

**Conservative extra exclusions are permitted by inference from the frozen
rules:** the inventory must cover specified prior use, and generation rejects
inventory members; the rules do not impose an exact-only inventory. This
interpretation does not change the OS CSPRNG, unsigned 64-bit domain,
big-endian draws, duplicate rejection, accepted-draw ordering or N=1,412.
Extra values still require provenance and cannot establish completeness.
The qualified consumer accepts an explicit `match_seeds_hex` list. It does
not support interval, predicate or generator representations. A whole-domain
exclusion is prohibited and would prevent acceptance.

## Boundaries and available evidence

The local read-back verifies:

| Boundary | Binding |
|---|---|
| Protocol commit | `6294efc7afea9d576742aaae0572d73ba904ac6b` |
| Draft 3 raw SHA-256 | `fbb9cd39e723362f85e9bc38e67bb348e8e497f8fc8770a2c901dbf173d6855a` |
| Qualified instrument commit | `514f4e22e9300d92ce23afaa418e39b06dac277e` |
| Packet 03 raw SHA-256 | `f31973fca452e0be34c1dc957cd7d64e303c0db421ce58ac1b706f7f5cf27a66` |

The [scope record](../../../tools/research/v6/e9/historical_scope_record.json)
identifies every inspected or potential source's custodian, availability, byte
binding, covered scope and limitations. It distinguishes unavailable records
from records the original producer demonstrably never serialized.

Targeted Git queries retained 827 reachable commit records, 28 workflow-history
entries, 63 test/tool deletion entries with parent-source bindings, and five
registered worktree identities, all currently present. Source versions and
workspace registration do not prove historical executions or parameter bounds.
Other execution-tool, pre-migration, clone and remote histories are not bound
by the available local session inventory; they are not presumed absent.

Read-only provider queries retained all pages of the API-reported available
GitHub history: **653 unique run identities** and **377 artifact identities**.
The run records span 2025-10-01 through 2026-10-02; four show latest attempt 2.
Failed and cancelled runs remain represented. The artifact names identify
executable/release bundles, not a qualification-seed manifest; their contents
were not downloaded. The available listing cannot prove that no history was
deleted or that no other CI provider existed.

Four targeted CI runs have byte-bound job responses and log receipts. Two log
archives were retrieved. The older log endpoints for **CI-18168897717** and
**CI-23956564416** returned **HTTP 410**; their retained jobs lack step details.
One successful Linux reference-match step supplies an explicit historical
match input already present in the candidate. No coverage claim is made for
other matches merely because that step or workflow succeeded.

## Supported coverage and route decision

The [shareable manifest index](../../../tools/research/v6/e9/historical_scope_manifest.json)
binds a private partial manifest with thirteen stable groups: the two revealed
experiment lists, ten retained B08/B12 executions, and one CI reference-match
step. Each private group retains actual recorded values, scope association,
source/evidence references and duplicate/failed-run relationships. Saved
metadata observations remain separate from execution groups.

E6/E8 commitments and all 32 entries of each list verify. The five B08
result/replay associations and five B12 replay/schedule associations verify
from retained bytes, using the two already-included seed references. B08's
helper obligation remains on DEFAULT-008/DERIVED-034. B12 rederivation agrees
with its recorded output using the historical caller default and thirteen
bound generator versions. The base input was not separately serialized at
invocation; this limits input attribution, not the directly recorded seed.

Five named bootstrap sites retain their resolved analysis RNG roles at bound
revisions. Synthetic malformed payloads do not clear containing-test history.
Missing invocation-time source hashes and REC-063/064's missing individual
JUnit nodes are provenance limitations, **not universal prerequisites** for
covering seeds established by equivalent recorded evidence.

Route B's missing premise is an evidenced exhaustive input domain for every
in-scope historical generator family. Current defaults, retained outputs and
removed source snapshots cannot bound unknown overrides or unrecorded
worktree variants. The finite sets checked here cover only explicitly
identified witnessed executions. They do not purport to cover whole helper,
test, CI or workspace histories. No whole-scope exclusion set was manufactured.

The original **157-entry candidate is unchanged**, remains `complete: false`,
and includes every supported recorded value examined here. No new consumed
value or justified additional exclusion was established, so no successor
candidate was created. The additive [crosswalk](../../../tools/research/v6/e9/historical_scope_crosswalk.json)
preserves every one of the **357 original IDs**, original dispositions and
reviewed distinctions. It attaches concrete missing facts, recovery evidence
and recoverability to every unresolved row. New scope dependencies and CI
records do not increase the original gap count.

## Local verification and limits

The separate [offline verifier](../../../tools/research/v6/e9/verify_historical_scope.py)
imports only the standard library; its only subprocess operation is a Git
object read. The [verification receipt](../../../tools/research/v6/e9/historical_scope_verification.json)
separates integrity/membership PASS from completeness NOT ESTABLISHED.

Its synthetic fixtures cover invalid encodings/domains, duplicates, false
completeness flags, missing scope/dependencies, incorrect derivations,
corrupted bindings, inconsistent result/replay seeds and identities, and CI
step evidence. The final synthetic test and lint results are recorded in the
receipt's companion validation record.

The first read-back refused an overly strict verifier requirement that B12's
post-corruption tournament state retain its match ID. All five bound states
deliberately clear that field on `resumed_result_mismatch`. The corrected
reader checks the saved seed, round/entrants, artifact-directory association
and retained replay identity, and rejects contradictory surviving IDs. The
refusal and private diagnostic are retained; original evidence was not repaired.

The saved 464,207-row inventory is independently read back against the
original audit: 462,553 metadata bindings, 1,491 no-seed rows and 163 malformed
rows reconcile. This is a verification of **saved identities and observations**.
The earlier full raw-corpus rehash remains reported evidence; it was not
repeated. Raw reads this pass are limited to the ten linked B08/B12 executions
and targeted CI evidence. No current-tree seed census, match, historical
qualification suite, bootstrap outcome analysis, fresh seed draw or payoff
execution was performed.

Original evidence and all 239 files in the inherited preservation snapshot
remain unchanged. Additions are uncommitted. Private values, resolved paths,
raw responses and reverse maps remain ignored; shareable records use opaque
references and digests. Automatic review rejected an initial broader
tool-directory/shell-history inspection; the subsequent narrower repository
and identified CI queries were approved and completed. No shell-history copy
or broad tool-directory scan was performed.

## Precise remaining dependencies

| ID | Missing fact or scope | Evidence that can resolve it | Recoverability |
|---|---|---|---|
| DEP-01 | Historical identities/scope of ten original directory-error rows | Original error/path records with coverage, **or** an exhaustive covering manifest/proved usable superset | Paths/errors were never serialized by the original count-only callback; external copies unknown |
| DEP-02 | Historical identities/upstream seed coverage of the original 1,491 no-seed records | Original selected-path/byte records with upstream coverage, **or** equivalent exhaustive covering evidence | Original producer omitted source rows for these records; current identities cannot recover the historical mapping; external copies unknown |
| DEP-03 | Exhaustive local qualification families, variants, actual seeds or bounded inputs | Responsible custodian inventory with evidence of completeness, **or** generator/version/input-domain containment proof | Partial local evidence available; additional records/archives unknown |
| DEP-04 | Other workspaces/tools, pre-migration lineage and additional remote qualification histories | Custodian-backed scope inventory or evidenced outside-scope disposition, plus seed coverage for in-scope matches | Registered workspaces present; their execution histories unbound here; no absence/loss declaration justified |
| DEP-05 | Complete CI qualification attempts and seed coverage, including removed tests, failures/partials and reruns | CI archive/seed manifest, **or** bound revision/workflow/platform/input reconstruction and containment | Available provider metadata bound; two selected old logs HTTP 410; alternate archives unknown; source reconstruction may remain possible |

Recovery alternatives are explicit: an exhaustive manifest or proved usable
superset can close coverage without recovering every lost artifact identity.
There is no requirement to recover every node or invocation-time source hash
when equivalent evidence establishes the relevant seeds and family coverage.

The irreversible limitation **within the original audit output** is loss of
information that was never recorded: counts cannot determine the omitted
identities. HTTP 410 establishes present provider unavailability for the two
specified archives. Neither finding proves whole-scope seed coverage is
irretrievably impossible; backups or equivalent containment evidence remain
unknown. No protocol amendment or relaxation is made here. Any such change
requires a separate research-lead decision.

**Coverage incomplete; generation LOCKED**, pending DEP-01 through DEP-05 or
equivalent exhaustive covering evidence. Seed generation, commitment
publication and payoff execution remain unauthorized. Requirement C remains
NOT ESTABLISHED.
