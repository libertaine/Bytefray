"""The V6 E8 active spatial sensing experiment (docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md).

This package holds, so far, only the machine-readable pre-registration and
the registered decision logic, frozen before any engine, agent, family, seed
or matrix work exists:

* ``preregistration.json``: the transcription of revision 2 of the
  markdown pre-registration, which remains the authoritative wording;
* ``preregistration.py``: its loader, which fails closed unless the JSON is
  the frozen one, the markdown is the registered revision, and the two agree;
* ``decision.py``: the registered decision logic (statuses, stability, rows,
  readings, the core answer, kills, disposition, the census and the seat
  layers), reading every registered value from the frozen transcription;
* ``preregistration_freeze.py`` and ``preregistration_freeze.json``: the
  pre-registration freeze identity.

Research-only. Nothing here runs a match.
"""
