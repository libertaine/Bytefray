# Bytefray research history (moved from the README)

> Moved unedited from the top of `README.md` for 6.0.0-alpha.1, so the README
> can open with the product. Only relative links were adjusted for this
> folder. Statements here describe the project as it stood before
> 6.0.0-alpha.1 (for example, "potential 5.1 release" and "5.1 Alpha
> installer candidate"); the dated records it links to govern.

## Development after Bytefray 5.1.0-alpha.1 (as written before 6.0.0-alpha.1)

[`v6-research`](https://github.com/libertaine/Bytefray/tree/v6-research) now contains
both sealed gameplay research and an implemented **V6 Alpha 1 sensing milestone**.
**Bytefray 5.1** brings this experimental gameplay to the application, with the
separate [Bytefray-Spectator](https://github.com/libertaine/Bytefray-Spectator)
companion. Its first preview, **5.1.0-alpha.1**, is published. It is the last
release that runs the Classic Ruleset: this development line has retired
Classic, and Active Sensing (Alpha) is its only Ruleset.

| Name | Current meaning |
| --- | --- |
| **Bytefray 5.0.0** | Latest stable application release; downloads below. See the [stable `main` branch](https://github.com/libertaine/Bytefray/tree/main). |
| **Bytefray 5.1.0-alpha.1** | Published preview (Python package `5.1.0a1`, tag `v5.1.0-alpha.1`); the last release with Classic. See the [release notes](../../docs/releases/BYTEFRAY_5_1_0_ALPHA_1_RELEASE_NOTES.md). |
| **Active Sensing (Alpha)** (`bytefray-rules-6-alpha1`) | The only supported Ruleset on this development line, and the omitted-ruleset default. Its gameplay identity is unchanged from 5.1.0-alpha.1; bounded M1 acceptance does not establish unrestricted release readiness. |
| **Classic** (`bytefray-rules-4`) | **Retired** after 5.1.0-alpha.1 ([decision record](../../docs/releases/CLASSIC_RULESET_RETIREMENT.md)). It cannot run new matches here; Bytefray 5.1.0-alpha.1 still runs it, and its recorded artifacts remain readable. |
| **V6**, **`v6-research`** | Research and development program and its branch; experiments, probes and instrumentation are not all prospective product features. "V6" is not an application version. |
| **Bytefray-Spectator** | Separate Godot application with its own release series. Version `0.1.0-alpha.1` is bundled with the 5.1 Alpha Windows installer candidate; it is not separately published. |

Application versions, ruleset identities, Agent API versions and artifact schemas
are independent. Active Sensing (Alpha) is a display name: artifacts,
`--ruleset` and diagnostics always use the exact ruleset ID. The V6 program name
does not announce an application 6.0. See the
[component versioning policy](../../docs/COMPONENT_VERSIONING.md) and the
[development compatibility record](../../docs/releases/BYTEFRAY_6_0_0_ALPHA_1_COMPATIBILITY.md)
(the [5.1.0-alpha.1 record](../../docs/releases/BYTEFRAY_5_1_0_ALPHA_1_COMPATIBILITY.md)
describes the published preview).

### What V6 research is trying to solve

The V6 program began with a cleanup and architecture effort — internally described as:

> **Bytefray goes on a diet and a makeover.**

The repository was simplified, obsolete execution paths were retired, historical compatibility was preserved, and major evaluation code was broken into smaller, more maintainable components.

With that foundation in place, the research shifted toward a harder gameplay question:

**How can Bytefray create meaningful opponent-dependent decisions rather than letting one broadly optimal strategy dominate most matchups?**

The research is deliberately empirical. Instead of adding several mechanics at once and deciding whether the result "feels better," V6 isolates individual variables, runs controlled match matrices, and records what actually changes.

### What has been learned so far

The early arena-size and movement studies are retained as historical background.
Their causal interpretations were superseded when the
[research integrity addendum](../../docs/research/v6/V6_PHASE4_GAMEPLAY_RESEARCH_METHODOLOGY.md#research-integrity-addendum-2026-09-22)
identified flawed premises and test/benchmark defects and closed that line.
The operative mechanic evidence starts at E2; the early rows below are not accepted
evidence for the Alpha 1 design.

| Research direction | What it told us |
|---|---|
| **Much larger arenas (historical)** | Explored whether extra space could deepen strategy; subsequent integrity review invalidated key causal interpretations, including apparent changes in competitive ordering. |
| **Movement scaling (historical)** | Explored reachability in large arenas; the normalization line closed with flawed premises and implementation/benchmark qualifications, rather than an adopted movement rule. |
| **Multi-tick capture** | Delaying capture removes one immediate forced line, but mostly converts it into delay, stalemate, or scheduler-dependent behavior. |
| **Slot-limited disruption** | Restricting disruption to the victim's next action significantly reduces whole-tick first-mover dominance, but does not eliminate order dependence. |
| **Mirrored pass ordering** | Balancing later action order removes much of the multi-pass ordering effect while exposing a separate opening-exchange effect. |
| **Anchor/core separation** | Separating process spawn position from the core proved that their original co-location was not the main cause of the remaining advantage. |
| **Priced sensing** | Limiting free information produced the first strong evidence that the best strategy can genuinely depend on the opponent and that obtaining information can compete with taking immediate action. |
| **Explicit active sensing (E8)** | Preserved opponent-dependent acquisition choices in the registered ecology. Reacquisition helped against the moving opponent under whole-tick disruption, but that benefit did not transfer to the one-offer companion. |

### From priced information to explicit sensing

The E6 **Priced Sensing** experiment asked what happens if an agent cannot automatically see opponents across its entire effective range.

Instead, agents have to decide how much effort to spend finding an opponent versus acting immediately.

Under the original control, one policy could remain a best response across the opponent field.

Under priced sensing, that disappeared: different opponents rewarded different allocations of search, information, movement, and attack effort.

The registered interpretation was:

**`R-CREATES` — priced sensing created an opponent-dependent choice of how to allocate actions.**

The experiment also showed that gathering **less** information could outperform gathering more information in some matchups.

That is important because it demonstrates the kind of strategic tradeoff V6 has been looking for.

It is **not**, however, a candidate for direct promotion.

The primary experiment also created a new seat artifact, so its registered disposition was to reject that exact mechanic as a gameplay candidate. A companion experiment using a different disruption model reproduced the strategic result without the same artifact.

The follow-up question—whether priced sensing interacts with disruption semantics to create the E6 seat artifact—was examined in a post-hoc factorial audit of the frozen E6 corpus. The audit found that the registered KC-5 event was a unit-level interaction involving priced sensing, whole-tick lockout, and ADAPT's absolute-tick behavior, but not a stable family-level sensing × disruption effect. That line closed with no E7 experiment; E8 subsequently completed the next registered study.

[E8's sealed result](../../docs/research/v6/V6_E8_RESULTS.md) returned **YES / R8-PRESERVES**:
switching from movement-acquired spatial information to an explicit sensing action
preserved opponent-dependent acquisition choices. Spending less on acquisition
could outperform spending more. Reacquiring EVADE8's relocated anchor paid under
the whole-tick parent, while repeated reacquisition was refuted in the one-offer
companion. The primary seat test was **NEITHER**, not proof of seat neutrality.
Its disposition was **CANDIDATE for further design**, with promotion false.

These findings supported a design channel, not universal competitive balance or
proof that revising strategy within a match improves payoff. **Requirement C**,
the bounded beneficial-adaptation claim, remains **NOT ESTABLISHED**. See the
[E2–E8 synthesis](../../docs/research/v6/V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md)
for the distinctions among registered results, descriptive observations and design
recommendations.

**E9 remains deferred and operationally blocked; scientific execution is LOCKED.**
Protocol and instrument qualification are preparation, not a completed payoff
experiment. The original generation authority was consumed once; retained execution
evidence records zero real entropy calls/attempts and no scientific execution. The
[original-G proof assessment](../../docs/research/v6/V6_E9_ORIGINAL_G_PROOF_RESOLUTION_01.md)
and [prospective handoff](../../docs/research/v6/V6_E9_PROSPECTIVE_STUDY_HANDOFF_01.md)
retain the restrictions. Alpha product work does not unlock E9 or establish C.

The [October 15 project decision](../../docs/v6/V6_PROJECT_DIRECTION_DECISION_20261015.md)
accepts the successor-feasibility assessment's **CONDITIONAL DESIGN-ONLY GO**
recommendation and defers further E9 work. No further successor design,
implementation or new study is authorized.

### Adoption and implementation progress

The [Phase 0 decision](../../docs/v6/V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md) adopted
the distinct Alpha 1 identity, T8's primary active-sensing mechanics, a bounded
teaching-fixture seed exception and upstream filtering of delivered knowledge.
This was a separate product decision after E8, not automatic promotion of its
research treatment. Slot-limited disruption, mirrored passes, delayed capture,
anchor/core separation and scaled movement remain research alternatives; Alpha 1
keeps whole-tick disruption, forward passes, one-tick capture checks, core-base
starting anchors and literal movement clamped to ±64.

[M1 — Verified Sensing Exchange](../../docs/v6/V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md)
is **technically accepted and CLOSED**, with Windows AMD64 and Linux X11/Xvfb
qualification. It delivers:

* Explicit experimental ruleset selection and capability preflight, retaining stable V4 defaults.
* Window Scout, its stationary teaching fixture and a reproducible full-match demo with bound replay/result/trace evidence.
* Independent sensing-exchange reconstruction, a phase cursor and receipt-only knowledge projection.
* Designer personal-copy/parameter workflows and diagnostic replay of request, receipt, movement and write phases.

Broader Alpha 1 development remains **incomplete**; M1 did not authorize an
unrestricted public release. Its native automated workflows do not establish a
human usability study. [M1-5's implementation record](../../docs/v6/V6_ALPHA_M1_5_IMPLEMENTATION_RECORD_01.md)
describes the authoring and viewer integration.

**M2 — Alpha 1 Expansion is the active development milestone.** After the
[design review](../../docs/v6/V6_ALPHA_M2_DESIGN_REVIEW_02.md), the lead accepted
[Scope Revision 03](../../docs/v6/V6_ALPHA_M2_SCOPE_CONTRACT_03.md) with conditions.
Its **M2-2 Watchful Keeper** slice is technically accepted and CLOSED — PASS WITH
CONDITIONS ([closure record](../../docs/v6/V6_ALPHA_M2_2_CLOSURE_01.md)). Its **M2-3
Roaming Reacquirer** implementation is accepted — PASS WITH CONDITIONS
([closure record](../../docs/v6/V6_ALPHA_M2_3_CLOSURE_01.md)). Its **M2-4 Replay and
Usability** implementation is accepted — PASS WITH CONDITIONS
([closure record](../../docs/v6/V6_ALPHA_M2_4_CLOSURE_01.md)): an `A | B | Omni`
replay selector with symmetric delivered views, a measured layout with readable
sample-marker labels, and one shared sensing guide with two scenario cards.
These acceptances cover Windows and Linux WSL2/WSLg X11 only and are not
release authorizations. Replay load time and accessibility remain open
conditions. Its **M2-5 technical and platform qualification** is accepted —
PASS WITH CONDITIONS ([closure record](../../docs/v6/V6_ALPHA_M2_5_CLOSURE_01.md)) —
on Windows, Linux WSL2/WSLg X11 and an Ubuntu Wayland session through XWayland;
native Ubuntu on Xorg is not qualified. Human evaluation (M2-6) is deferred to
Bytefray 5.2.

## V6 Alpha 1: decisions from delivered information

An agent cannot rely on the engine passively supplying opponent positions in
`bytefray-rules-6-alpha1`. It must spend actions to find contacts and decide what
to do with observations that may already be stale. The
[adopted M1 contract](../../docs/v6/V6_ALPHA_M1_CONTRACT_01.md), read with the later
Phase 0 and final-acceptance decisions, specifies the interaction:

| Mechanic | Implemented behavior |
| --- | --- |
| **SENSE** | `AgentAction(ActionKindV2.SENSE, operand=address)` scans an inclusive circular ±27-cell window. The normalized center must be within the acting process's reach; the window may extend beyond that reach. |
| **Action price** | A scan consumes one action opportunity, including an empty or out-of-reach scan. It does not move, write, claim territory or disrupt an opponent. |
| **Sample and delivery** | Anchors are sampled when the action executes. Sorted unique anonymous addresses arrive once as `previous_sense_anchors` in the same process's next eligible observation, possibly in a later tick; a sibling callback does not receive them. No eligible callback before termination means no receipt. |
| **Information asymmetry** | Passive enemy contacts are empty. SENSE exposes no opponent identity, core location or live tracking; different agents/processes can have different delivered knowledge. Applied-empty, refused and absent receipts remain distinct. |
| **Historical contacts** | A receipt describes the sample instant, even if an opponent moved before delivery. Agents may remember it; there is no engine expiry timer or automatic refresh. Diagnostic playback labels sample/receipt age and reconstructs only the permitted knowledge prefix when seeking. |
| **Movement and memory** | MOVE changes the anchor by a literal delta clamped to ±64. READ/WRITE target memory within process reach. READ delivers byte value and last-writer owner ID; that feedback is distinct from an anonymous spatial contact. WRITE can change bytes/ownership and disrupt processes at the target. |
| **Core defense** | Cores contain eight cells; owning zero at tick end eliminates an entrant. Whole-tick disruption and seeded placement are inherited from the primary design. |

The standard M1 demonstration uses two entrants, a 512-cell arena, eight actions
per entrant per tick and a 1,000-tick limit. These are its run profile, not a
new universal arena-size requirement. Alpha 1 retains Agent API v2 and
replay4/trace2/result2; capability metadata v1 (`required: [sense]`) and demo
sidecar v1 are additive. Sensing agents declare that capability so a run under a
Ruleset without SENSE fails preflight. Since Classic's retirement it is the only
Ruleset: the CLI uses it when `--ruleset` is omitted, and every Designer surface
(Simple, Advanced, Development and Evaluation) runs it without a Ruleset control.

### Teaching examples and limits

[Window Scout](../../docs/v6/V6_ALPHA_M1_2_IMPLEMENTATION_RECORD_01.md)
(`v6_window_scout`) is implemented and registered. Its teaching fixture shows
**incomplete knowledge → SENSE → delayed anonymous receipt → informed MOVE → WRITE**,
then resumed scouting. The stationary opponent is an internal fixture, not a
competitive starter. Watchful Keeper (`v6_watchful_keeper`) adds the defensive
lesson — delivered READ ownership supports a repair attempt and an anonymous
SENSE receipt supports one defensive WRITE — and is accepted as M2-2. Roaming
Reacquirer (`v6_roaming_reacquirer`) adds the reacquisition lesson — a paid
rescan records only that an old address was absent from a newer sample, and a
paid MOVE and new SENSE find a new anonymous contact without claiming it is the
same process — and is accepted as M2-3.

Reach has **no direct resource or quota cost** in Alpha 1. Window Scout deliberately
uses reach 128 to make movement and search legible; legal unrestricted circular
coverage can reduce the need to move while searching or attacking. The action
cost of SENSE remains, but limited teaching reach is not an enforced competitive
tradeoff. These demonstrations teach information flow, not optimized play or balance.

The initial core byte **`0xCE` is mutable**. Rewriting a core cell can erase that
beacon, including a write by its owner. A byte signature is not cell ownership:
core survival depends on ownership of assigned cells, not preservation of `0xCE`.

The teaching seed exception does not solve seed/placement inference by arbitrary
Python agents. API v2 still supplies deterministic seed/RNG context and agents
are trusted local code. Restricted replay faithfully presents **engine-delivered
knowledge**, not every fact hostile host code could derive. This remains a
release limitation rather than a secrecy guarantee.

## Bytefray-Spectator: making recorded matches readable

The simulation and information model grew more sophisticated during research;
human observers also need an engaging way to see the consequences. The separate
[Bytefray-Spectator repository](https://github.com/libertaine/Bytefray-Spectator)
explores that presentation layer in **Godot 4 / GDScript**, while Bytefray remains
the authority for match execution.

**See Spectator in action:** [Watch the short Bytefray Spectator showcase on YouTube](https://www.youtube.com/watch?v=bWVifa9iEmw).
The video demonstrates the current recorded-match presentation experience.

The existing Pygame viewer supplies general replay/analysis tooling, and the V6
sensing viewer is a diagnostic teaching tool for exact request/receipt/action
phases. Spectator adds a focused circular-arena presentation, recorded action
effects, readable core status and procedural audio. It does not execute agent
decisions or simulate new matches during playback; visual/audio effects are
presentation derived from recorded facts, not additional simulation events.

Its current source-only preview supports:

* Circular memory ownership, process anchors/movement, disruption and core status.
* Recorded WRITE targets and SENSE request/delivery activity, with timeline playback, frame/tick stepping, seeking and restart.
* **Broadcast** world information and **Agent A** delivered information; arbitrary entrant selection is not implemented.
* **Filled Arcs** and **Classic** memory styles with identical address coordinates.
* Procedural sound effects and original nonverbal electronic opening/winner cues; the public preview has no spoken announcer.

Broadcast shows the complete recorded state and outcome. Agent A shows only its
own exported actions, READ/SENSE receipts and remembered anonymous contacts;
hidden ownership, opponent actions and winner cues do not enter that perspective.
Separate models and upstream receipt-only projection enforce this boundary for
both graphics and sound. Navigation maps tick boundaries rather than hidden
opponent decision indices. Seeking to the end or exhausting Agent A's own record
does expose its record boundary: this is a recorded viewer with a disclosed
navigation limitation, not a live competitive-agent interface.

The read-only Python exporter checks exact pinned Bytefray package bytes, verifies
canonical replay/result/trace association and reconstructs the recorded outcome.
It uses Bytefray's `SensingCursor` for Broadcast and receipt-only `SensingView`
for Agent A, emitting `broadcast.json`, `agent_a.json` and a hash manifest.
The Godot loader rejects presentation files whose SHA-256 differs from that
manifest. This detects inconsistency; it is not authentication against malicious
replacement of both files and manifest.

The bundled **Harrier vs Bastion, seed 427** showcase uses a 512-cell arena and
ends in core capture at tick 477. It was selected for a readable contest under a
frozen protocol; its upset is not a balance benchmark. The development fixture
is Window Scout against the stationary opponent. See the
[showcase record](https://github.com/libertaine/Bytefray-Spectator/blob/main/docs/P0C_SHOWCASE_SELECTION_01.md)
and [existing screenshot comparisons](https://github.com/libertaine/Bytefray-Spectator/blob/main/docs/FILLED_ARCS_MEMORY_VISUALIZATION_01.md).

**Viewing requires Godot 4.7.2, a display and the OpenGL Compatibility renderer.**
The bundled showcase requires no separate Bytefray or Python installation.
Windows automated verification is documented; other Spectator platforms and
independent human usability/listening evaluation remain unqualified or pending.
There is no standalone executable release.

That pinned exporter and its frozen fixtures remain unchanged. They require
Python 3.13 and exact locally supplied Bytefray source at pin
`9c81718d057c8cd021f6d1cc7938ea19881b78e1`, which is not currently public.
See Spectator's [dependency and export instructions](https://github.com/libertaine/Bytefray-Spectator#generate-matches-or-exports--dependency-limitation).

**Integrated viewing (development branch, unreleased and unqualified).** The
`v6-spectator-integration` branch moves export into Bytefray itself:

* `bytefray spectator export --source <match dir> --out <dir>` verifies an
  ordinary completed two-entrant Active Sensing (Alpha) match
  (`bytefray-rules-6-alpha1`). It runs the same replay
  preflight Designer uses, then the authoritative sensing reconstruction, then
  re-derives the outcome. It writes the same Broadcast and Agent A documents
  under a version-2 manifest. No hand-written `match.json` is needed.
* Agent Designer's **View Last Match** opens such matches in Spectator when one
  is installed or configured (`BYTEFRAY_SPECTATOR`). Every other match, and
  every match when Spectator is absent, keeps the Pygame viewer.
* Spectator's own branch adds **File > Open Presentation** and Windows/Linux
  export presets for standalone builds.

See the [Spectator export and Designer dispatch spec](../../docs/specs/spectator_export.md).

Godot consumes verified exports, not arbitrary raw replay formats. Broader
replay compatibility, additional entrant perspectives, other-platform
qualification and a separately published Spectator executable remain future
work, not supported features. The 5.1 Alpha Windows installer bundles
Spectator `0.1.0-alpha.1`, and Designer finds that copy automatically.

### Current development direction

Bytefray 5.0.0 remains the stable application on V4. A potential 5.1 release could
bring explicitly experimental Alpha 1 gameplay to a wider audience once the
remaining product and release decisions are resolved. M2 development focuses
on contrasting teaching agents, parameter-first authoring and human comprehension
of delayed/stale knowledge. Continued research can investigate adaptation and
competitive interaction separately; Alpha 1 and Spectator do not settle those
questions. Spectator develops the viewing experience in its own repository.

For evidence, start with the [E2–E8 synthesis](../../docs/research/v6/V6_E2_E8_SYNTHESIS_AND_NEXT_DESIGN_REVIEW.md),
[Phase 0 adoption](../../docs/v6/V6_ALPHA_M1_PHASE0_DECISION_PACKET_01.md) and
[M1 acceptance](../../docs/v6/V6_ALPHA_M1_FINAL_ACCEPTANCE_01.md).
[ROADMAP](../../docs/ROADMAP.md) and [FUTURE_PLANS](../../docs/FUTURE_PLANS.md) retain older
planning language; the dated decisions and sealed results govern current status.

The downloads and V4 quick start below describe the stable 5.0.0 application.
For historical execution modes retired on this branch, use the matching released
version; historical artifact readers remain available here.
