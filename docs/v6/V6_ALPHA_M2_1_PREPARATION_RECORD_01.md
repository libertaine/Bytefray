# Bytefray V6 — M2-1 Preparation and Validation Record 01

2026-10-15, America/Indianapolis. **Documentation preparation only.**
This record accompanies [Scope Revision03](V6_ALPHA_M2_SCOPE_CONTRACT_03.md) and
[Checkpoint B01](V6_ALPHA_M2_CHECKPOINT_B_01.md). It records local observations
and documentation checks; it creates no implementation, qualification, human
evaluation, historical-preservation audit or approval result.

## 1. Entry observations and preservation

Branch `v6-m2-clean`, HEAD `f79a74be1d486f042d260bea672305b9abb27aa5`,
tree `d4f2c73cbd3965762e61316567537e173503ff8a`. Upstream `origin/v6-research` locally
records the same full commit (0 ahead / 0 behind). Local divergent
`v6-research` is `2fc3c82e115650b515a4efab39afb172b62535ed` (4 ahead / 3 behind
the recorded upstream). Remote URL is
`https://github.com/libertaine/Bytefray.git`. A read-only live-remote query
failed to connect to github.com:443; no fetch/ref mutation or live parity claim.

Entry index has no staged changes. Raw index SHA-256:
`b77a600d7e0c4e5679798a787e0b392b9994a5ae95a5b8841c4f0192bf6ee00b`.
The four-file inherited state below is the complete entry porcelain state:
README/ROADMAP modified; Review02 and direction record untracked. Their raw
bytes were captured before edits and SHALL remain unchanged by this task.

| Inherited file | Entry bytes | Entry raw SHA-256 |
| --- | ---: | --- |
| `README.md` | 52994 | `a272442333219cd881396804059ff0a7860561930f3d4ec870838e481d5c8153` |
| `docs/ROADMAP.md` | 119407 | `de163cf07f3dd71acbe8b6575e0c7c0aa973b5671974940a22e5dea16498fa4e` |
| `docs/v6/V6_ALPHA_M2_DESIGN_REVIEW_02.md` | 24973 | `7588d127a66e024b55ba28c867f35aa88e6aeb96655dcd7b7de75a99d8c4897b` |
| `docs/v6/V6_PROJECT_DIRECTION_DECISION_20261015.md` | 4384 | `27312ede9a8b41aad9692bc1bce429dd0f96ae8fd51957c58d85748331686c2c` |

The original-worktree proposal was read in place and its reviewed hash matched.
No original-worktree file was written, and no branch was switched, merged,
rebased, reset or overwritten. No recursive original/private workspace inventory
was attempted. The record makes no new per-file private backup or custody claim.

## 2. Exact input identities

These are raw working-file hashes at preparation entry, not normalized Git blob
hashes. The named HEAD independently identifies the tracked source baseline.
The local proposal path is a provenance locator, not a published document link.
M1 final acceptance supersedes earlier proposal/pending language without changing
those records. Capability and policy input hashes pin the existing contract
implementation; no ruleset/API change is proposed.

| Input | Bytes | Raw SHA-256 |
| --- | ---: | --- |
| `docs/v6/V6_ALPHA_M1_CONTRACT_01.md` | 38774 | `504ed85c8ef2445bbab1e385dfe63d27fb35cf7a23199f1b9c50724a2f75a399` |
| `docs/v6/V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md` | 25626 | `69fc87be60e6be62b259826377fd38b583d8b6b1b796b434654c786cfe3576e8` |
| `docs/v6/V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md` | 17108 | `c78a260b358c46d3ff580d0f23e5d4f9d6906b2e33a711a08a684289135035de` |
| `docs/v6/V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md` | 17737 | `069f1d139668aae46403b7713703357cf6e6222344b96c1b0ad57d143f71f6a1` |
| `docs/v6/V6_ALPHA_M1_3_IMPLEMENTATION_RECORD_01.md` | 30117 | `609b73d0ae162748989fe6e4667b95716f7727b2862ffcc9d182b7e29280b6a3` |
| `docs/v6/V6_ALPHA_M1_4_IMPLEMENTATION_RECORD_01.md` | 20240 | `b1b8bfe1af5a98ecc54f862a83d7659ea4546269d5d0bc9108e0d8a72500a039` |
| `docs/v6/V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md` | 34972 | `f7c9c5c19eab569b62a01ededaff92753967416533780b24d00f617d508bdcfc` |
| `docs/v6/V6_ALPHA_M1_1_FROZEN_BASELINE_VALIDATION_DISPOSITION_03.md` | 13399 | `7ad568433543530a12c43d352c8f043124e6922d4460d0a667b9b9db7144d476` |
| `engine/src/battle_engine/rules.py` | 21869 | `4967df739d64d7a4a4cdb23bfbd9a42d1567d882900498d630706a1fad46b75d` |
| `engine/src/battle_engine/ruleset_policy.py` | 79918 | `22fb88283929cf0927aaa24d2db44fda2d8b7aaf5708fc365019ab0ce1d4194a` |
| `engine/src/battle_engine/agent_capabilities.py` | 2506 | `b06bec1e2b9ab599ef618998273d4e5d5c4951719334a0f5115ad6dbd651eb64` |
| `engine/src/battle_engine/starters.py` | 27476 | `4f427744e82145bcdb68c869be056861bb5424dcab8f9f967dfd5358cd3c38fe` |
| `engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.py` | 6417 | `8e6c97c7f0c3ead4f656ca2c0f1b265f3a03c500716591db2311f7abf9a3bdf0` |
| `engine/src/battle_engine/data/starter_agents/v6_window_scout/agent.yaml` | 1037 | `017864bdf34657a993419328a169766f07be1d2b99f6e28782f37ee51fa53890` |
| `engine/tests/test_v6_alpha_sensing_playback_core_capture.py` | 19267 | `742e5d3f645c0dc2e1884891cf9bc1a3b27d685485b6ce52786710fddf775c56` |
| `client/tests/test_v6_alpha_sensing_core_capture.py` | 4326 | `25ec816a597ab7df1a879ed4a65d83a65c5068c30de8d256713180e8ecacc444` |
| `D:/Projects/BATTLE2/docs/V6_ALPHA1_M2_SCOPE_PROPOSAL.md` | 20822 | `e97dca6c48f8e1b4e787b44d0870e44836f0ebc716f3ef9f1d1b3955aaddf7f1` |

The final Scope/Checkpoint hashes are recorded after their documentation checks
below. This record's own digest is intentionally not embedded in itself.

## 3. Task-created file manifest and relevant diff

The complete inherited four-file state remains in place. This task adds only:

| Added file | Relevant additions |
| --- | --- |
| `docs/v6/V6_ALPHA_M2_SCOPE_CONTRACT_03.md` | Explicit baseline/authority; retained M1 mechanics; capability object; two scaffold choices; K1/R1 parameter/state contracts; both-seat schedules; separate provenance/scenario verdicts; symmetric A/B navigation/layout; human criteria; compatibility/platform/isolation gates; six milestone entry/deliverable/acceptance/dependency/stop definitions. |
| `docs/v6/V6_ALPHA_M2_CHECKPOINT_B_01.md` | All ten review IDs/severities with exact normative references, ACs, methods and proposed-design dispositions; precise Keeper-only production/test/doc boundary; nine closure gates; open risks/limits; conditional recommendation and unset lead decisions. |
| `docs/v6/V6_ALPHA_M2_1_PREPARATION_RECORD_01.md` | Entry/index/input hashes, preservation comparison, change manifest, documentation consistency/reference/whitespace checks and explicit validation limits. |

Diff semantics relative to local Revision02: numbered workstreams become the
six sequential milestones; invalid capability lists become versioned objects;
absolute-core defense becomes delivered READ/own-relative repair; fixture scan
notification becomes own-callback F4 movement; reconstruction success becomes
separate explicit scenario completion; the CLI-template exclusion is replaced
by two existing-machinery choices; A/B selection acquires symmetric filtering
and navigation gates; vague human/platform acceptance becomes observable tasks
and bounded native evidence. Revision02 itself is untouched.

## 4. Checks and results

Checks completed with native PowerShell/.NET and read-only Git commands:

| Check | Observed result |
| --- | --- |
| Local Markdown references | **PASS:** 220 links across all seven working documents resolve, including directory links, heading anchors and source-line anchors. Remote URLs were not fetched by this check. |
| New document whitespace/encoding | **PASS:** all three files read as UTF-8, no trailing whitespace, final newline present. |
| Tracked/index whitespace | **PASS:** `git diff --check` and `git diff --cached --check` produced no diagnostics. |
| Input preservation | **PASS:** all 21 recorded inputs retain exact length/raw SHA-256, including the four inherited files, original proposal, governing M1 records and sampled source/capture-test baseline. |
| Git identity/index | **PASS:** branch, HEAD/tree, locally recorded upstream and divergent local branch unchanged; raw index digest unchanged and no staged diff. |
| Exact changed path set | **PASS:** seven porcelain entries = four inherited entries plus exactly the three new documents; no production/test/research changes. |
| Finding/criterion/gate coverage | **PASS:** F01–F08 HIGH and F09–F10 MEDIUM each appear once in the matrix; twelve M2-AC rows, six milestone rows and nine M2-2 closure gates present. |
| Contract consistency | Static cross-check in §5: no proposed M1 mechanic, wire-schema, V4-default, historical-evidence or E8/E9 authority change; exact decisions/proofs still pending as recorded. |
| Schedule review | Static action/chunk/reach/core-survival reasoning only; both-seat tables reviewed against scheduler rotation, ±64 movement, initial ownership, READ/SENSE delivery and D=1 suppression. **No engine-run witness.** |

An attempted stdlib-only Python documentation checker could not start because
the existing repo virtual-environment executable was inaccessible to the system.
The completed PowerShell checks above replace that tooling attempt; no runtime
environment repair or source/configuration change was made. An initial link-check
pass treated directory links as files and left heading anchors for inspection;
the final checker validates both and reports zero errors. Neither attempt was a
product test campaign.

Final reviewed contract/package identities (raw bytes, without normalization):

| Document | Lines | Bytes | Raw SHA-256 |
| --- | ---: | ---: | --- |
| `docs/v6/V6_ALPHA_M2_SCOPE_CONTRACT_03.md` | 509 | 37938 | `1b3e507a2593919ed64d43cad0d5ce673e734333529db1e936d5880b4a916eba` |
| `docs/v6/V6_ALPHA_M2_CHECKPOINT_B_01.md` | 173 | 22023 | `29e3883ab6a28995f1f105e9fb15f4e8091f0847930d38f2b1381a36d019f786` |

The preparation record is checked after this results section is inserted; its
self-digest is not embedded. The complete three-file additions and relevant
diff semantics are listed in §3.


No engine/client/app/test implementation, match, scenario validator, pytest,
Ruff, mypy, GUI interaction, human evaluation or research operation ran during
this documentation task. Runtime/technical gates in the scope and B package
are future obligations. No staged content, commit, merge, push or release.

## 5. Consistency review and remaining decision

The normative cross-check uses the accepted M1 final record and Phase0/contract,
implementation records M1-2 through M1-5, Disposition03, existing architecture and
scaffold/trace/schema contracts. No adopted M2 spec was found under docs/specs/.
The existing scaffold and accepted M1 personal-copy workflow support the bounded
copy choice; existing v1 parsing/common artifact fields support the proposed
envelope-only design. That design still requires implementation compatibility
checks; no Scout field or schema is reinterpreted here.

| Governing boundary | Preparation conclusion |
| --- | --- |
| M1 technical acceptance | PASS/CLOSED retained at accepted 053e3eb...; no existing technical gate reopened or new M1 evidence claimed. |
| Stable V4/defaults | Default/omitted selector behavior, Simple/Evaluation scope, stable SENSE rejection and retired-execution boundaries expressly preserved. |
| Alpha1 information delivery | Next same-process callback, one paid opportunity, anonymous historical samples, absent/null/empty/terminal distinctions, no alerts/TTL/live refresh; READ owner information remains distinct. |
| Projection/replay | Filter upstream of renderer; A/B symmetric permitted prefixes/local pacing; result binding/fallback and optional-sidecar independence retained. |
| Historical qualification | 329 historical pins remain tied to b948540...; accepted 72-node context and separate current product/compatibility partitions retained without resealing or a new unpartitioned PASS. |
| E8/E9 isolation | No controllers/private inputs/entropy/authority operations; E9 remains blocked/LOCKED, successor work deferred, Requirement C NOT ESTABLISHED. |
| Platform/human limits | Existing COM/focus/raw-artifact/layout limits retained truthfully; M2 adds explicit future native and actual-human gates, with no release/full-matrix claim. |

Recommendation is **PASS WITH CONDITIONS** for proposed design adoption, as
qualified by Checkpoint B01. Revised scope adoption, Checkpoint B acceptance and
M2-2 implementation authorization remain **AWAITING EXPLICIT LEAD DECISION**.
Stop at this prepared package.

