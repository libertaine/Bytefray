# E9 capability qualification

These modules implement the approved allocation capability class. They do
not implement an experiment runner, matrix, seed protocol, payoff selector,
or statistical decision rule.

- `tactics.py` is a byte-identical copy of the frozen E8 shared executor.
  Do not edit it. Its original module description is retained for byte identity;
  `policy.py` supplies the E9 wrapper and factory.
- `policy.py` handles verification feedback, opportunity epochs, fixed
  variants, disabled twins, and schedule variants. Reset accepts only arena
  512 and active window 27. Use the unchanged E8 T8 ruleset for qualification.
- `selectors.py` implements the approved deterministic controller and
  canonical schedule enumeration. Neither selector receives tactical state.
- `oracle.py` independently transcribes the approved transition contract;
  it imports neither policy code nor implementation constants.
- `packages.py` creates explicit scratch packages for qualification tests.
  These import repository modules and are not standalone distribution agents.

The engine tests use synthetic callbacks and scripted legal opponents. The
real-match harness saves diagnostic observations/actions/controller states
in ignored scratch storage; it does not summarize or compare outcomes.
The existing engine trace/replay recorder still produces its normal artifacts.

See [qualification record](../../../../docs/research/v6/V6_E9_CAPABILITY_QUALIFICATION.md)
and [approved contract](../../../../docs/research/v6/V6_E9_ADAPTIVE_POLICY_CLASS_AND_CAPABILITY_SPEC.md).
Requirement C remains NOT ESTABLISHED. Experimental seeds, performance
selection and preregistration require a later research decision.
