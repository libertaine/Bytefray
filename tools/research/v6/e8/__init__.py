"""The V6 E8 active spatial sensing experiment (docs/research/v6/V6_E8_ACTIVE_SPATIAL_SENSING_PREREGISTRATION.md).

This package holds, so far, the machine-readable pre-registration, the
registered decision logic and the parent goldens, all made before any engine,
agent, family, experiment seed or matrix work exists:

* ``preregistration.json``: the transcription of revision 5 of the
  markdown pre-registration, which remains the authoritative wording;
* ``preregistration.py``: its loader, which fails closed unless the JSON is
  the frozen one, the markdown is the registered revision, and the two agree;
* ``decision.py``: the registered decision logic (statuses, stability, rows,
  readings, the core answer, kills, disposition, the census and the seat
  layers), reading every registered value from the frozen transcription;
* ``preregistration_freeze.py`` and ``preregistration_freeze_v4.json``: the
  pre-registration freeze identity, v4. ``preregistration_freeze_v3.json``,
  ``preregistration_freeze_v2.json`` and ``preregistration_freeze.json`` are
  freezes v3, v2 and v1, kept byte for byte as superseded before any
  exposure;
* ``parent_goldens.py`` and ``parent_goldens.json``: the C8 and C8L parent
  byte-identity goldens (phase I8-1, D8-6), run at fixed infrastructure seeds.

Research-only. Only the golden tool runs matches, at those infrastructure
seeds; nothing here runs an E8 matrix cell.
"""
