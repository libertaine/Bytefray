# M1-1 context inventory disposition proposal 02

2026-10-10, America/Indianapolis. **ADOPTED — IMPLEMENTATION AUTHORIZED.**
The user explicitly answered: “Authorize these two assertion updates and
finish validation.” The two updates below are applied; final verification is
recorded in the [M1-1 implementation report](V6_ALPHA_M1_1_POLICY_CAPABILITIES_01.md).

The [first supplemental disposition](V6_ALPHA_M1_1_SUPPLEMENTAL_INVENTORY_DISPOSITION_01.md)
is adopted and its eight assertion updates are applied. Full-suite execution
and an independent census audit identified two further context-delivery
assertions outside that list. Both parametrize the entire current registry
but expect the approved alpha identity to receive historical absent values.
Changing the implementation to meet those expectations would violate literal
T8 inheritance. The user-authorized eight changes do not include these two
functions; this second supplemental scope was subsequently explicitly adopted.

Independent reviewer: Codex subagent `/root/m1_1_independent_review`. The reviewer
also audited registry references in engine, client and historical tests and
found no further inventory conflicts; the full suite remains authoritative
for implementation defects.

| File under `engine/tests/` | Exact function | Proposed change |
| --- | --- | --- |
| `test_e6_context_detection_radius.py` | `test_every_registered_ruleset_delivers_its_own_radius` | Use local expected membership `{*RADIUS_32_IDS, "bytefray-rules-6-alpha1"}` for both `r32` delivery and literal radius 32 expectations. Preserve `RADIUS_32_IDS` and all other policies' absent/None checks. |
| `test_v6_e8_sensing_context.py` | `test_every_registered_ruleset_delivers_its_own_window` | Use local expected membership `{*E8_IDS, "bytefray-rules-6-alpha1"}` for both `w27` delivery and literal reset window 27 expectations. Preserve `E8_IDS` and all other policies' absent/None checks. |

Each function still runs both direct and worker cases: four newly affected
alpha cases, with the complete historical per-registry matrix still exercised.
No other functions, fixture definitions, schemas, historical
compatibility gates, scientific manifests, artifacts, goldens or source pins
may change. Original qualified bytes remain available at the baseline commit.

Separately, full-suite inspection exposed a worker guard regression for
injected characterization policies such as `test-only`. That implementation
defect is corrected in product code: callback loading with absent/empty
capability requirements needs no executable-registry query. Declared sensing
requirements still query the selected registered policy before import, and
NativeMatchService still rejects unknown/retired executable identities.
Existing characterization tests remain unchanged.
