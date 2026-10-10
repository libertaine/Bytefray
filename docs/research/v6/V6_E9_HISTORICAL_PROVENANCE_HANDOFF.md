# E9 historical provenance handoff — 2026-10-02

Step 2 remains BLOCKED on completeness. This packet provides review evidence;
it does not establish complete historical exclusion coverage.

Protocol: FROZEN. Instrument commit:
`514f4e22e9300d92ce23afaa418e39b06dac277e` (qualified).
Evaluation artifacts remain bound. Seed generation and payoff execution remain
UNAUTHORIZED. Requirement C remains NOT ESTABLISHED.

## Packet and integrity

Archive: `e9_historical_provenance_01.zip` in this directory.
Size: 2,154,682 bytes. SHA-256:

```text
c229176d1c084ac9fc22a20355bdddae4e273d309ece73864555e56aa0564929
```

The 224 archive members include the preparation report and machine records,
JSON/CSV coverage ledgers, 173 source snapshots, 38 reports/manifests, seven
selected retained tool-call excerpts, source/revision manifests and transport
checksums. The capability report identifying preset 7 is included.

The original preparation audit was retained unchanged and bound by its raw
SHA-256. Archive checksums, source snapshots against the named Git revisions,
163 retained failure captures and exported path redactions were independently
checked. No qualification, test suite or match was executed in this pass.

## Coverage limitations

| Indexed category | Rows | Disposition |
|---|---:|---|
| Original directory failures | 10 | UNRESOLVED |
| Unreadable records | 163 | UNRESOLVED |
| Nonliteral seed references | 158 | UNRESOLVED |
| Harness default declarations | 25 | UNRESOLVED |
| Additional count-only limitation | 1 | UNRESOLVED |

All 357 rows remain unresolved. Each indexed row identifies its evidence and
missing closure requirements; the original directory rows are placeholders
because that audit recorded only a count, not directory identities. A fresh
read-only traversal observed ten current access failures, but has not linked
them to the original ten. Current observations are recorded separately.

All 163 currently readable failure files were captured privately without
modifying the originals. None decoded as a JSON record under the documented
UTF-8/UTF-16 attempts. Readable sibling hints do not establish authoritative
duplicates. Original failures remain recorded.

Source snapshots bind current census declarations and selected historical
qualification source files. They do not establish which revision, parameters,
inputs or defaults applied to every historical invocation. The seven retained
tool-call excerpts are additional leads, not proof of successful execution or
an exhaustive invocation ledger. Actual match seeds must still be distinguished
from policy RNG values through deterministic provenance.

The original audit also counted 1,491 records without a decoded match seed
without retaining their paths. The extra aggregate row records this limitation;
its count cannot prove those records are outside the frozen exclusion scope.

## Privacy and delivery

Sensitive corpus paths and experimental reveal values use opaque references in
the packet. The private reverse map and raw failure captures are retained in
the ignored evidence area. Original and redacted transport hashes are separate;
redacted copies cannot substitute for original-byte evidence.

The archive is prepared locally. This session has no attachment-upload tool, so
it has not been transferred to the user's other workspace. Delivery requires an
accessible destination supplied by the user. No commit, push or publication was
performed.
