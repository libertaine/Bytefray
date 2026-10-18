# Bytefray V6 — M2-5 Technical and Platform Qualification Closure Record 01

2026-10-18, America/Indianapolis.

**Authority: Bytefray Project Lead — "Component Identity Acceptance and M2-5
Reconciliation" decision**

| Decision axis | Recorded disposition |
| --- | --- |
| M2-5 TECHNICAL AND PLATFORM QUALIFICATION | **ACCEPTED — PASS WITH CONDITIONS** (§4) |
| Accepted source | `bb6c4b88713a4a0552db3bf4a561b803b306b52b` on the published `v6-alpha1-m2-5-qualified` branch (§2) |
| Native Ubuntu confirmation | **Confirmed in an Ubuntu Wayland session through XWayland**, as stated by the lead (§3) |
| Native Ubuntu on Xorg | **NOT QUALIFIED — recorded limitation** (§3) |
| Acceptance criteria | AC01–AC10 and AC12 technically supported under the §4 conditions; AC11 requires human evaluation |
| M2-6 human comprehension evaluation | **DEFERRED to Bytefray 5.2**; not executed |
| Component Identity Reset (`10da315`) | **ACCEPTED** by the same decision ([versioning policy](../COMPONENT_VERSIONING.md)) |
| Reconciliation with the component identity line | Local integration merge `22f092cd8e54d3cd74b9cedf3ef1379f2ec64c29` (§5); unpushed |
| Bytefray 5.1 | Feature freeze continues. No release branch, tag, version change or publication authorized; the application version stays `5.0.0` |
| Original E9 / Requirement C | **OPERATIONALLY BLOCKED** (execution LOCKED) / **NOT ESTABLISHED** — unchanged |

## 1. Authority and provenance

The Project Lead stated this decision in the development session of
2026-10-18. It accepts the M2-5H recommendation of PASS WITH CONDITIONS, takes
account of the native Ubuntu confirmation that followed publication of
`bb6c4b8`, accepts the Component Identity Reset milestone, defers M2-6 to
Bytefray 5.2 and authorizes a local reconciliation of the two lines. This
record transcribes that conversational decision. It carries no signature,
cryptographic approval or new research authority, and it is not a release
authorization.

Earlier records keep their historical wording and bytes:

- [M2-5 Entry Decision 01](V6_ALPHA_M2_5_ENTRY_DECISION_01.md) still reads
  "not authorized".
- The [public summary](V6_ALPHA_M2_5_PUBLIC_SUMMARY_01.md) still reads
  "Native Ubuntu is not yet qualified", which was true when it was published.
- The [native Ubuntu confirmation handoff](V6_ALPHA_M2_5_UBUNTU_CONFIRMATION_01.md)
  still names Ubuntu on Xorg as its required session.

This record establishes the final M2-5 disposition. No fresh M2-5 qualification
campaign was run for it.

## 2. Accepted identities

| Identity | Value |
| --- | --- |
| Accepted commit / tree | `bb6c4b88713a4a0552db3bf4a561b803b306b52b` / `b909d012c51c98451b4d9b04f285a4e3ecaaeffa` |
| Parent (published M2-4) / tree | `10c3530f035335b89716d5bda7ce138440767a71` / `893ee89db154474924e5c1f92a5a70041345eb4d` |
| PD-1 source | `app/views/replay_history.py`, raw SHA-256 `6994479d4256dd49dc74750d705ddc3a12917c469a839eb6b557ed1391c7df10` |
| Timezone fixture correction | `tests/test_v5_replay_history_qualification.py`, raw SHA-256 `b786ebcce71915f267cf1fa9df518b79319d46a1c89370b113dd358e1741f340` |
| Source manifest | [`V6_ALPHA_M2_5_SOURCE_MANIFEST_01.json`](V6_ALPHA_M2_5_SOURCE_MANIFEST_01.json), SHA-256 `dd2b55792dff98d5b8097261bde26917133ae1aaf70b46073240f256e2e51451`; 1,249 source/test and 20 portable fixture identities |
| Ubuntu confirmation handoff | SHA-256 `a14ce2ba0fbdbfb28c2e4153a23b3e40bca3ed7d57438d38570453e4465c03d7` |
| Retained M2-5H Qualification Report 01 (local, not published) | SHA-256 `e65131403bad5b9de8e9616f106ab6f718d4f43ff51f8da176cc91475252e208`, re-verified unchanged on 2026-10-18 |

## 3. Native Ubuntu confirmation

After `bb6c4b8` was published, a Windows-side preflight on 2026-10-17 stopped
with HOLD because no native Ubuntu desktop was reachable from that session. It
ran no Ubuntu test. The lead reports that the bounded confirmation was then
carried out on an Ubuntu desktop in a **Wayland session, using XWayland**, and
accepts it as confirming the M2-5 workflows within that scope.

That scope is narrower than the handoff's. The handoff required a native Xorg
or X11 login and states that "a Wayland session running XWayland is a
different scope". Therefore:

- **Native Ubuntu on Xorg is not qualified.** It remains a recorded
  limitation of M2-5 and of any release claim built on it.
- No claim is made for Wayland-native Qt or SDL backends.
- No claim is made for other Linux distributions, the full runtime-version
  matrix, or packaging and installers.

The Ubuntu confirmation's own report and raw evidence are not in this
repository and were not on the integrating workstation. This record therefore
relies on the lead's decision. It does not restate test counts, dependency
versions, timings or observations from that confirmation. The confirmation
applies to `bb6c4b8` and was not repeated on the reconciled tree (§5).

## 4. Conditions

The conditions of the [public summary](V6_ALPHA_M2_5_PUBLIC_SUMMARY_01.md)
remain in force unchanged:

- Windows replay loading takes about 12.2 seconds for the selected workloads.
- Selected perspective switches take about 6 seconds on Windows and 4 seconds
  on WSL Linux, and Windows showed "Not Responding" during measured C2
  switching. No performance optimization is included.
- History scroll, Help scroll and arbitrary timeline seek have no keyboard
  alternatives. Return does not activate the ordinary non-default guide button.
- WSLg focus needed a Windows-host caption click.
- Historical Linux crash and shutdown observations remain unresolved.
- There is no general display-scale or accessibility certification.
- The earlier M2-3 L1–L5, M2-4 D1 and COM/tooling conditions remain as recorded
  in their closure documents.

This decision adds two conditions:

- **C-X1:** native Ubuntu desktop coverage is Wayland through XWayland only;
  native Xorg is unqualified (§3).
- **C-X2:** AC11 is unmet until M2-6 human comprehension evaluation runs, which
  is deferred to Bytefray 5.2.

## 5. Reconciliation with the component identity line

The lead authorized merging this line with the accepted component identity
line. The merge is local and unpushed:

| Identity | Value |
| --- | --- |
| Integration branch | `v6-m2-5-identity-integration` (local) |
| Merge commit / tree | `22f092cd8e54d3cd74b9cedf3ef1379f2ec64c29` / `9041d70d49bba5055f4b2f87798ccf8622b7fd3e` |
| First parent | `10da3150b49f1f3fd91c8928d94f8dfb4884c91e` (component identity, accepted) |
| Second parent | `bb6c4b88713a4a0552db3bf4a561b803b306b52b` (this record's accepted source) |
| Merge base | `10c3530f035335b89716d5bda7ce138440767a71` |

The two lines share no changed path, and the merge was conflict-free. Against
the source manifest, the merged tree has:

- 1,233 of 1,249 source/test identities byte-identical to the M2-5 qualified
  bytes;
- 16 identities superseded by changes on the accepted line: the
  `bytefray spectator` export command, Designer's Spectator launch path, and
  presentation-only Ruleset labels and help text;
- all 20 portable fixtures and both PD-1 files byte-identical.

M2-5's qualification evidence binds to `bb6c4b8`. It is not a qualification of
the merged tree. The combined tree's regression evidence and its review are in
the reconciliation report, `docs/M2_5_RECONCILIATION_REPORT.md`, which the
commit after this record's adds.

## 6. Not authorized by this record

- creating the Bytefray 5.1 Alpha release branch or tag;
- changing the application version from `5.0.0`;
- pushing or publishing the integration branch;
- executing M2-6 or any E9 research;
- new features or gameplay mechanics.
