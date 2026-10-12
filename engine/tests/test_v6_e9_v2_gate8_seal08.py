"""Seal 08: S7-IQ-F1 (complete F1 precedence, option C) and S7-IQ-F2 under scope 04 (implementer tests).

Scope: v2_gate8_scope_04.json (v6-e9-v2-gate8-scope-0f65753151e2), the lead's Seal-08 rulings
D8-01..D8-03 and Disposition 05. SYNTHETIC QUALIFICATION FIXTURES ONLY: every REAL-labelled study
is the hand-built fixture of test_v6_e9_v2_gate8_producer.py in a pytest temporary root. REAL is
only an input declaration. No REAL entropy, salt creation, generation, native match, registration
or operational publication occurs, and nothing here is operational evidence.
"""

from __future__ import annotations

import json

import pytest

from engine.tests.test_v6_e9_v2_gate8_producer import OP, RECORDER, VERIFIER, built, encode
from engine.tests.test_v6_e9_v2_gate8_seal06 import (
    labels,
    marker_path,
    no_generation,
    registry_path,
    substitute,
    verifier_calls,
)
from tools.research.v6.e9.v2 import authority as au
from tools.research.v6.e9.v2 import inventory
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2 import records as rec

ZERO, LAST = "0" * 64 + ".json", "f" * 64 + ".json"
SCAN_TRIGGERS = ["other-G first", "other-G last", "G record", "event file"]
SOURCES = [*SCAN_TRIGGERS, "this-G entry"]
SCHEMAS = rec.BASE / "amended_record_schemas_v2_proposed_02.json"


def roots(study):
    return study.log.root / "producer-roots"


def unavailable(study, monkeypatch, source):
    """Make one producer-registry read typed-unavailable; returns the exact restorer."""
    if source == "this-G entry":
        path = registry_path(study)
        raw = path.read_bytes()
        path.unlink()
        path.mkdir()  # a native non-regular object: refused before any open

        def restore():
            path.rmdir()
            path.write_bytes(raw)
        return restore
    if source in ("other-G first", "other-G last"):
        other = roots(study) / (ZERO if source == "other-G first" else LAST)
        other.mkdir()
        return other.rmdir
    active, inside = [True], []
    real_scan = au.AuthorityLog.registered_producers

    def scan(self):
        inside.append(True)
        try:
            return real_scan(self)
        finally:
            inside.pop()
    monkeypatch.setattr(au.AuthorityLog, "registered_producers", scan)
    if source == "G record":
        G, real_resolve = study.log.bindings["G"], au.AuthorityLog.resolve

        def resolve(self, ref):
            if active and inside and ref == G:
                raise rec.DurableUnavailable("simulated unavailable G record")
            return real_resolve(self, ref)
        monkeypatch.setattr(au.AuthorityLog, "resolve", resolve)
    else:
        real_read = au.regular_bytes

        def read(path):
            if active and inside and path.name.startswith("event-"):
                raise rec.DurableUnavailable("simulated unavailable event file")
            return real_read(path)
        monkeypatch.setattr(au, "regular_bytes", read)
    return active.clear


def inconsistent(study, form, name=LAST):
    """Another registry entry that fails the unchanged scan consistency checks (Scope 02 F1 item 3)."""
    raw = registry_path(study).read_bytes()
    if form == "foreign stem":
        value = raw  # this G's exact entry under another G's name: path.stem check
    elif form == "corrupt":
        value = b'{"corrupt"'
    else:
        item = json.loads(raw)
        item["unexpected"] = True
        value = encode(item)
    path = roots(study) / name
    path.write_bytes(value)
    return path


def wrong_bytes(study, form):
    raw = registry_path(study).read_bytes()
    if form == "substituted":
        value = substitute(study, "registry")
    elif form == "corrupt":
        value = b'{"corrupt"'
    else:
        value = json.dumps(json.loads(raw), indent=1).encode() + b"\n"  # same content, other bytes
    assert value != raw
    return value


def failed(study):
    with pytest.raises(rec.IntegrityError) as raised:
        study.produce()
    assert not isinstance(raised.value, pv.Unavailable)
    assert labels(study)[-1] == "FAILED_VERIFICATION" and not (study.folder / "W.json").exists()
    return raised.value


def refused_after_failure(study):
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()
    assert "PASS" not in labels(study)


# ---- S7-IQ-F1: positive mismatch evidence is never masked by registry unavailability -------------

@pytest.mark.parametrize("form", ["substituted", "corrupt", "re-encoded"])
@pytest.mark.parametrize("trigger", SCAN_TRIGGERS)
def test_s8_f1_this_g_wrong_registry_bytes_fail_despite_scan_unavailability(tmp_path, monkeypatch,
                                                                          trigger, form):
    """D8-01 / Disposition 05: current-G mismatch + other-G, G-record or event-file unavailable."""
    study = built(tmp_path)
    raw = registry_path(study).read_bytes()
    registry_path(study).write_bytes(wrong_bytes(study, form))
    clear = unavailable(study, monkeypatch, trigger)
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    error = failed(study)
    assert "registered producer root" in str(error) and calls == []
    clear()
    registry_path(study).write_bytes(raw)  # exact restoration of every condition
    refused_after_failure(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


@pytest.mark.parametrize("source", SOURCES)
def test_s8_f1_marker_mismatch_fails_despite_registry_unavailability(tmp_path, monkeypatch, source):
    """D8-01: marker mismatch + scan unavailability, and + this G's entry itself unavailable."""
    study = built(tmp_path)
    marker = marker_path(study).read_bytes()
    marker_path(study).write_bytes(substitute(study, "marker"))
    clear = unavailable(study, monkeypatch, source)
    no_generation(monkeypatch)
    assert "first-raw marker" in str(failed(study))
    clear()
    marker_path(study).write_bytes(marker)
    refused_after_failure(study)


@pytest.mark.parametrize("source", SOURCES)
def test_s8_f1_unavailability_without_mismatch_is_unavailable_until_exact_recovery(tmp_path, monkeypatch,
                                                                                  source):
    """D8-01: no positive mismatch anywhere -> UNAVAILABLE; the exact evidence returning -> PASS."""
    study = built(tmp_path)
    clear = unavailable(study, monkeypatch, source)
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Unavailable, match="producer registry unavailable"):
        study.produce()
    assert labels(study) == ["UNAVAILABLE"] and calls == [] and not (study.folder / "W.json").exists()
    clear()
    W = study.log.resolve(study.produce())
    assert labels(study) == ["UNAVAILABLE", "PASS"] and W["body"]["decision"] == "PASS" and calls == [True]


@pytest.mark.parametrize("form", ["foreign stem", "corrupt", "unknown key"])
@pytest.mark.parametrize("source", ["other-G first", "G record", "event file", "this-G entry"])
def test_s8_f1_a_later_inconsistent_entry_is_not_masked_by_earlier_unavailability(tmp_path, monkeypatch,
                                                                                 source, form):
    """D8-01 option C: an earlier unavailable read + a later available consistency mismatch fails.

    Repairing the unrelated unavailable condition, or even the inconsistent entry, never yields PASS.
    """
    study = built(tmp_path)
    other = inconsistent(study, form)
    clear = unavailable(study, monkeypatch, source)
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    failed(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and calls == []
    clear()
    refused_after_failure(study)
    other.unlink()
    refused_after_failure(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION", "REFUSED_PRECONDITION"]


def test_s8_f1_the_seal07_probe_state_no_longer_reaches_pass(tmp_path, monkeypatch):
    """S7-IQ-F1 / scope-drafting probe: other-G inconsistent + earlier non-regular entry."""
    study = built(tmp_path)
    other = inconsistent(study, "foreign stem")
    (roots(study) / ZERO).mkdir()
    no_generation(monkeypatch)
    failed(study)
    (roots(study) / ZERO).rmdir()
    other.unlink()
    refused_after_failure(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


def test_s8_f1_a_later_unmapped_unavailable_cannot_mask_a_marker_mismatch(tmp_path, monkeypatch):
    """DV8-4: after a deferral the scan ends with the deferred error, so the marker is still checked."""
    study = built(tmp_path)
    marker_path(study).write_bytes(substitute(study, "marker"))
    (roots(study) / ZERO).mkdir()
    inside, real_scan, real_read = [], au.AuthorityLog.registered_producers, rec.regular_bytes

    def scan(self):
        inside.append(True)
        try:
            return real_scan(self)
        finally:
            inside.pop()

    def read(path):
        if inside and path == SCHEMAS:
            raise rec.DurableUnavailable("simulated unavailable frozen catalogue")
        return real_read(path)
    monkeypatch.setattr(au.AuthorityLog, "registered_producers", scan)
    monkeypatch.setattr(rec, "regular_bytes", read)
    no_generation(monkeypatch)
    assert "first-raw marker" in str(failed(study))


# ---- registered_producers contract (D8-01 / DV8-3 / DV8-4) --------------------------------------

def scan_reads(monkeypatch):
    """Every mapped read the scan makes: entry/event regular reads and G-record resolves."""
    reads, real_read, real_resolve = [], au.regular_bytes, au.AuthorityLog.resolve

    def read(path):
        reads.append(("read", path.name))
        return real_read(path)

    def resolve(self, ref):
        reads.append(("resolve", ref["digest"]))
        return real_resolve(self, ref)
    monkeypatch.setattr(au, "regular_bytes", read)
    monkeypatch.setattr(au.AuthorityLog, "resolve", resolve)
    return reads


def test_s8_scan_a_clean_registry_is_unchanged(tmp_path):
    study = built(tmp_path)
    G = study.log.bindings["G"]["digest"]
    assert study.log.registered_producers() == {G: json.loads(registry_path(study).read_bytes())}


def test_s8_scan_continues_past_a_deferred_read_with_no_new_read(tmp_path, monkeypatch):
    """DV8-3: the faulted scan makes exactly the healthy scan's reads plus the unavailable one."""
    study = built(tmp_path)
    reads = scan_reads(monkeypatch)
    study.log.registered_producers()
    healthy = set(reads)
    assert ("read", registry_path(study).name) in healthy and any(name.startswith("event-") for _, name in healthy)
    reads.clear()
    (roots(study) / ZERO).mkdir()
    with pytest.raises(au.ProducerRegistryUnavailable, match="not a regular file"):
        study.log.registered_producers()
    assert set(reads) == healthy | {("read", ZERO)}


def test_s8_scan_raises_the_first_deferred_unavailability(tmp_path, monkeypatch):
    study = built(tmp_path)
    clear_record = unavailable(study, monkeypatch, "G record")
    clear_event = unavailable(study, monkeypatch, "event file")
    with pytest.raises(au.ProducerRegistryUnavailable, match="simulated unavailable G record"):
        study.log.registered_producers()
    clear_record()
    with pytest.raises(au.ProducerRegistryUnavailable, match="simulated unavailable event file"):
        study.log.registered_producers()
    clear_event()
    assert registry_path(study).stem in study.log.registered_producers()


@pytest.mark.parametrize("order", ["mismatch first", "mismatch last"])
def test_s8_scan_a_positive_mismatch_raises_in_either_order(tmp_path, order):
    """Mismatch before the unavailable entry (as in Seal 07) or after it (option C)."""
    study = built(tmp_path)
    mismatch, missing = (ZERO, LAST) if order == "mismatch first" else (LAST, ZERO)
    inconsistent(study, "corrupt", name=mismatch)
    (roots(study) / missing).mkdir()
    with pytest.raises(rec.IntegrityError) as raised:
        study.log.registered_producers()
    assert not isinstance(raised.value, rec.DurableUnavailable)


def test_s8_scan_an_unmapped_unavailable_is_not_deferred_and_does_not_replace_a_deferral(tmp_path,
                                                                                         monkeypatch):
    """DV8-2 (S7-IQ-F3 unchanged) and DV8-4."""
    study = built(tmp_path)
    real_read = rec.regular_bytes

    def read(path):
        if path == SCHEMAS:
            raise rec.DurableUnavailable("simulated unavailable frozen catalogue")
        return real_read(path)
    monkeypatch.setattr(rec, "regular_bytes", read)
    with pytest.raises(rec.DurableUnavailable, match="frozen catalogue") as plain:
        study.log.registered_producers()
    assert not isinstance(plain.value, au.ProducerRegistryUnavailable)
    (roots(study) / ZERO).mkdir()
    with pytest.raises(au.ProducerRegistryUnavailable, match="not a regular file") as deferred:
        study.log.registered_producers()
    assert "frozen catalogue" in str(deferred.value.__context__)


def test_s8_other_registry_callers_keep_single_condition_refusals(tmp_path):
    """D8-01: unavailable alone stays the typed refusal; only a combined later mismatch now wins."""
    study = built(tmp_path)

    def assert_producer():
        return study.log.assert_producer(study.generator.root, RECORDER, operation_id=OP)
    assert_producer()
    (roots(study) / ZERO).mkdir()
    with pytest.raises(au.ProducerRegistryUnavailable):
        assert_producer()
    other = inconsistent(study, "corrupt")
    with pytest.raises(rec.IntegrityError) as raised:
        assert_producer()
    assert not isinstance(raised.value, rec.DurableUnavailable)
    other.unlink()
    (roots(study) / ZERO).rmdir()
    assert_producer()


# ---- S7-IQ-F2: classification follows the protected-verification boundary (DV8-1) ---------------

def fault_at_entry(study, monkeypatch, where):
    """Make one protected-entry input unavailable; returns the exact restorer."""
    if where in ("event", "active", "retained"):
        if where == "event":
            path = min(study.log.root.glob("event-*.json"))
        elif where == "active":
            path = study.log.root / "active.json"
        else:
            path = study.log.root / "evidence-records" / (study.S["digest"] + ".json")
        raw = path.read_bytes()
        path.unlink()
        path.mkdir()

        def restore():
            path.rmdir()
            path.write_bytes(raw)
        return restore
    if where == "source-checker":
        def unavailable_source():
            raise rec.DurableUnavailable("simulated unavailable audited source file")
        study.log.source_check = unavailable_source
        return lambda: setattr(study.log, "source_check", lambda: None)
    target = SCHEMAS if where == "catalogue" else inventory.CONTRACT
    real_read, active = rec.regular_bytes, [True]

    def read(path):
        if active and path == target:
            raise rec.DurableUnavailable("simulated unavailable frozen input")
        return real_read(path)
    monkeypatch.setattr(rec, "regular_bytes", read)
    return active.clear


@pytest.mark.parametrize("where", ["event", "active", "retained", "source-checker", "catalogue",
                                   "frozen-limitations"])
def test_s8_f2_unavailability_at_protected_entry_is_a_refused_precondition(tmp_path, monkeypatch, where):
    """Disposition 05 / DV8-1: before protected verification is entered -> REFUSED_PRECONDITION."""
    study = built(tmp_path)
    tip = study.log.tip
    if where == "retained":
        study.log.retain_record(study.S)
    restore = fault_at_entry(study, monkeypatch, where)
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Unavailable):
        study.produce(expected_tip=tip)
    assert labels(study) == ["REFUSED_PRECONDITION"] and calls == []
    restore()
    study.produce(expected_tip=tip)  # non-terminal: exact restoration lets W proceed
    assert labels(study) == ["REFUSED_PRECONDITION", "PASS"] and calls == [True]


def durable_log_fault(monkeypatch, phase):
    """The same producer read, unavailable either in _preconditions or once _derive has begun."""
    real_log, real_derive, deriving, active = pv._durable_log, pv._derive, [], [True]

    def derive(*args, **kwargs):
        deriving.append(True)
        return real_derive(*args, **kwargs)

    def log(authority):
        if active and bool(deriving) == (phase == "verification"):
            raise rec.DurableUnavailable("simulated unavailable authority log")
        return real_log(authority)
    monkeypatch.setattr(pv, "_derive", derive)
    monkeypatch.setattr(pv, "_durable_log", log)
    return active.clear


@pytest.mark.parametrize("phase,expected", [("precondition", "REFUSED_PRECONDITION"),
                                            ("verification", "UNAVAILABLE")])
def test_s8_f2_the_same_read_is_classified_by_phase(tmp_path, monkeypatch, phase, expected):
    """DV8-1: not every Unavailable becomes REFUSED_PRECONDITION; the typed error still propagates."""
    study = built(tmp_path)
    clear = durable_log_fault(monkeypatch, phase)
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Unavailable, match="simulated unavailable authority log"):
        study.produce()
    assert labels(study) == [expected] and calls == []
    clear()
    study.produce()
    assert labels(study) == [expected, "PASS"] and calls == [True]


def test_s8_f2_an_unreadable_outcome_record_is_a_refused_precondition(tmp_path, monkeypatch):
    """DV8-1: _preconditions reads prior outcomes before verification is entered."""
    study = built(tmp_path)
    study.folder.mkdir(parents=True, exist_ok=True)
    stray = study.folder / "attempt-9999.outcome.json"
    stray.mkdir()
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Unavailable):
        study.produce()
    outcome = json.loads((study.folder / "attempt-0001.outcome.json").read_bytes())
    assert outcome["outcome"] == "REFUSED_PRECONDITION" and calls == []


@pytest.mark.parametrize("where", ["registry", "marker", "payload", "salt", "audit", "K"])
def test_s8_f2_unavailable_evidence_during_verification_stays_unavailable(tmp_path, monkeypatch, where):
    """DV8-1: once protected verification has begun, unavailable durable evidence keeps UNAVAILABLE."""
    study = built(tmp_path)
    if where in ("registry", "marker"):
        path = registry_path(study) if where == "registry" else marker_path(study)
    else:
        ref = study.S["body"][where] if where != "K" else study.records["O"]["body"]["K"]
        path = study.log.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")
    raw = path.read_bytes()
    path.unlink()
    path.mkdir()
    no_generation(monkeypatch)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Unavailable):
        study.produce()
    assert labels(study) == ["UNAVAILABLE"] and calls == []
    path.rmdir()
    path.write_bytes(raw)
    study.produce()
    assert labels(study) == ["UNAVAILABLE", "PASS"]


def test_s8_f2_other_classifications_are_unchanged(tmp_path, monkeypatch):
    """A Refused stays REFUSED_PRECONDITION and a verification integrity failure stays FAILED."""
    study = built(tmp_path)
    no_generation(monkeypatch)
    with pytest.raises(pv.Refused, match="registered independent W verifier"):
        study.produce(verifier={**VERIFIER, "role": "recorder"})
    marker_path(study).write_bytes(substitute(study, "marker"))
    failed(study)
    assert labels(study) == ["REFUSED_PRECONDITION", "FAILED_VERIFICATION"]
