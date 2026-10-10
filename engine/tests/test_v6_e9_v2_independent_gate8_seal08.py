"""Independent Seal-08 checks: S7-IQ-F1 combined ordering and S7-IQ-F2 entry classification.

Author context: a new independent test-author context of the Seal-08 cycle (2026-10-08), separate
from the implementer and from the authors of the earlier independent Gate-8 modules, working on the
uncommitted Seal-08 state over baseline e035def989dfc5e26ae3eb2c9ccfd16aed54b66c. It did not read
the implementer's Seal-08 module, the implementer's earlier Gate-8 modules or the Seal-08 plans,
did not consult the implementer, and ran no test while writing this module.

Derivation. Expected outcomes come only from: Disposition 05 (v2_finding_disposition_05.json and
its mirror: the S7-IQ-F1 repair ordering items 1-7, the required F1 qualification table and the
S7-IQ-F2 rule); the lead's Seal-08 scope rulings (v2_seal08_lead_scope_rulings_01.txt: D8-01 with
its required registered_producers behavior, complete ordering and additional required F1
coverage, and D8-03 DV8-1 to DV8-3); Gate-8 scope 04 (body.required_semantics, derived_readings,
rulings and new_qualification); Planning Revision 02 section 3 (V6_E9_SEAL07_PLAN_02.md, the
classification rules); and Gate-8 scope 02 body.repairs.F1, whose order item 3 counts a registry
that fails its unchanged consistency checks as positive evidence. The implementer-derived readings
DV8-4 and DV8-5 of scope 04 are not used as a source of any expectation. The implementation
sources authority.py, private_verification.py, records.py and inventory.py were read for names,
paths and call signatures only. "Reading:" marks this author's reading where the texts leave a
choice; "Case validity:" marks checks that the intended combined state was actually reached.

Limits. Every study is a synthetic qualification fixture of the independent Gate-8 producer module
(test_v6_e9_v2_independent_gate8_producer): study "synthetic-e9-v2-only", synthetic actors,
hash-derived synthetic uint64 values and a literal 32-byte constant standing in for the salt, built
inside pytest temporary roots. REAL appears only as the fixtures' entropy declaration label. No
fixture consumes entropy, calls os.urandom or secrets, creates salt, runs a native match or
publishes anything. Faults are injected only into files under pytest temporary roots and into
in-process calls; repository files are only read. Passing this module is author validation, not
qualification of Seal 08, and it grants no operational authorization.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import pytest

from engine.tests import test_v6_e9_v2_independent_gate8_producer as fixture
from engine.tests import test_v6_e9_v2_independent_gate8_seal06 as prior
from tools.research.v6.e9.v2 import authority as auth
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2 import records

PASS, UNAVAILABLE = "PASS", "UNAVAILABLE"
FAILED, REFUSED = "FAILED_VERIFICATION", "REFUSED_PRECONDITION"
FIRST, LAST = "0" * 64, "f" * 64  # registry entry names that sort before and after any G digest


@pytest.fixture
def bases(tmp_path_factory):
    return fixture.base_getter(tmp_path_factory)


def issued(bases, tmp_path: Path) -> fixture.Study:
    """A private copy of the issued study: ISSUE(+S) is the tip and W is not yet produced."""
    study = fixture.clone(bases("issued"), tmp_path)
    assert FIRST < study.log.bindings["G"]["digest"] < LAST
    return study


def attempt(study: fixture.Study, tip: str | None = None) -> records.IntegrityError:
    """One manually started W attempt that does not pass; returns the error its caller received."""
    with pytest.raises(records.IntegrityError) as raised:
        fixture.produce(study, expected_tip=tip)
    return raised.value


def assert_stays_refused(study: fixture.Study, calls: list, history: list[str],
                         *repairs: Callable[[], None]) -> None:
    """Scope 04 recovery item 2 and the D8-01 recovery distinction: a discovered positive mismatch
    stays terminal through the existing 'already failed' refusal, whatever is repaired afterwards
    (Scope 02 F1 classification: every later attempt for this S is refused)."""
    for repair in repairs:
        repair()
        error = attempt(study)
        assert not isinstance(error, records.DurableUnavailable)
        history = [*history, REFUSED]
        assert fixture.labels(study) == history
    assert calls == [] and fixture.written_W(study) == []


# ---- Registry fixtures --------------------------------------------------------------------------

def entry_path(study: fixture.Study, digest: str) -> Path:
    return study.log.root / "producer-roots" / (digest + ".json")


def retain_generation_record(study: fixture.Study) -> Path:
    """Retain this G's record, so the registry scan reads it from the authority root."""
    study.log.retain_record(study.records["G"])
    path = study.log.root / "evidence-records" / (study.log.bindings["G"]["digest"] + ".json")
    assert path.is_file()
    return path


def consume_event(study: fixture.Study) -> Path:
    """The event file recording this G's CONSUME, which the scan checks registry bytes against."""
    (path,) = [path for path in fixture.event_files(study)
               if json.loads(path.read_bytes())["body"]["event_kind"] == "CONSUME"]
    return path


def other_generation(study: fixture.Study, *, before: bool, label: str) -> dict:
    """Another synthetic G of this study (only its operation differs) whose digest sorts before or
    after this G's digest. Found by a deterministic label search, never a draw."""
    own, template = study.log.bindings["G"]["digest"], study.records["G"]["body"]
    for index in range(1 << 16):
        body = {**template, "operation_id": f"synthetic-{label}-{index}"}
        if (records.sha256(records.canonical_bytes(body)) < own) == before:
            return records.make_record("G", body)
    raise AssertionError("no synthetic G digest sorts on the requested side")


def other_entry(study: fixture.Study, *, before: bool,
                operation: str | None = None) -> tuple[Path, bytes]:
    """A registry entry for another synthetic G of this study, with that G's record retained so
    every unchanged check on the entry can run. It is consistent unless ``operation`` names an
    operation its G record does not carry: an available entry failing a consistency check."""
    side = "before" if before else "after"
    record = other_generation(study, before=before, label="other-generation-" + side)
    study.log.retain_record(record)
    ref = records.record_ref(record)
    item = {"study_id": study.log.study_id, "G": ref,
            "operation_id": record["body"]["operation_id"] if operation is None else operation,
            "producer_root": os.path.normcase(str((study.root / ("other-" + side)).resolve())),
            "recorder": fixture.RECORDER,
            "binding_tuple": {**{role: study.log.bindings[role] for role in auth.THROUGH_G},
                              "G": ref}}
    raw = records.canonical_bytes(item) + b"\n"
    path = entry_path(study, ref["digest"])
    path.write_bytes(raw)
    return path, raw


def misfiled_entry(study: fixture.Study, digest: str = LAST) -> Path:
    """This G's exact registry bytes filed under another G's name: an available entry failing the
    unchanged identity check that an entry is filed under the G it records."""
    path = entry_path(study, digest)
    path.write_bytes(study.log.read_artifact(prior.bound(study, "registry")))
    return path


def later_mismatch(study: fixture.Study, form: str) -> Path:
    """An available inconsistent registry entry that sorts after this G's own entry."""
    if form == "misfiled":
        return misfiled_entry(study)
    assert form == "G-operation"
    return other_entry(study, before=False, operation="synthetic-mismatched-operation")[0]


class Scan:
    """Observe every AuthorityLog.registered_producers call (the registry scan) and the durable
    reads it attempts. With a target, that existing durable object is a directory, so non-regular
    and unavailable before any open (Planning Revision 02 section 3), for exactly the duration of
    each scan call while armed. Between scans the exact original bytes are back in place."""

    def __init__(self, monkeypatch, study: fixture.Study, target: Path | None = None):
        self.target, self.armed = target, target is not None
        self.held = study.root / ("scan-held-" + target.name) if target is not None else None
        self.calls: list[dict] = []
        self.current: dict | None = None
        original_scan, original_read = auth.AuthorityLog.registered_producers, auth.regular_bytes

        def observed_read(path):
            call = self.current
            if call is not None:
                call["reads"].append(Path(path))
            try:
                return original_read(path)
            except records.DurableUnavailable:
                if call is not None:
                    call["unavailable"].append(Path(path))
                raise

        def observed_scan(log):
            call: dict = {"reads": [], "unavailable": [], "raised": None}
            self.calls.append(call)
            previous, self.current = self.current, call
            installed = parked = False
            if self.armed and self.target is not None and self.held is not None:
                if self.target.exists():
                    os.replace(self.target, self.held)
                    parked = True
                self.target.mkdir()
                installed = True
            try:
                return original_scan(log)
            except BaseException as exc:
                call["raised"] = exc
                raise
            finally:
                self.current = previous
                if installed and self.target is not None and self.held is not None:
                    self.target.rmdir()
                    if parked:
                        os.replace(self.held, self.target)

        monkeypatch.setattr(auth, "regular_bytes", observed_read)
        monkeypatch.setattr(auth.AuthorityLog, "registered_producers", observed_scan)

    def disarm(self) -> None:
        """The exact restoration of a scan-time unavailability."""
        self.armed = False

    def take(self) -> list[dict]:
        calls, self.calls = self.calls, []
        return calls


def met(calls: list[dict], path: Path) -> bool:
    """Some registry scan call met ``path`` as unavailable."""
    return any(path in call["unavailable"] for call in calls)


def scanned_past(calls: list[dict], unavailable: Path, later: Path) -> bool:
    """Some registry scan call met ``unavailable`` and then went on to read ``later``."""
    return any(unavailable in call["unavailable"] and later in call["reads"]
               and call["reads"].index(unavailable) < call["reads"].index(later)
               for call in calls)


def arm(study: fixture.Study, trigger: str, monkeypatch,
        state: str = "directory") -> tuple[Scan, Callable[[], None], Path]:
    """Make one registry-scan input unavailable; return the scan observer, the exact restoration
    and the unavailable path.

    entry-before / entry-after: a consistent other-G entry, sorting before or after this G's
        entry, made non-regular ("directory") or unreadable ("read_error") on disk.
    own-entry: this G's own durable registry entry, made non-regular or unreadable on disk.
    event / G-record: the CONSUME event file, or this G's retained record, is non-regular only
        while the registry scan runs. The protected entry reads the same objects, and its own
        classification (DV8-1) would end the attempt before the producer's registry boundary.
    """
    if trigger in ("entry-before", "entry-after"):
        path, _ = other_entry(study, before=trigger == "entry-before")
        return Scan(monkeypatch, study), prior.make_unavailable(state, path, monkeypatch), path
    if trigger == "own-entry":
        path = prior.durable(study, "registry")
        return Scan(monkeypatch, study), prior.make_unavailable(state, path, monkeypatch), path
    assert trigger in ("event", "G-record")
    path = consume_event(study) if trigger == "event" else retain_generation_record(study)
    scan = Scan(monkeypatch, study, path)
    return scan, scan.disarm, path


# ==== S7-IQ-F1: the D8-01 minimum list and the Disposition 05 table ============================

@pytest.mark.parametrize("state, form", [("directory", "misfiled"), ("read_error", "misfiled"),
                                         ("directory", "G-operation")])
def test_d8_01_earlier_unavailable_entry_never_masks_a_later_entry_mismatch(
        state, form, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    scan, restore, unavailable = arm(study, "entry-before", monkeypatch, state)
    mismatch = later_mismatch(study, form)
    assert unavailable.name < prior.durable(study, "registry").name < mismatch.name
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # D8-01 required behavior items 1-5 and its first "Additional required F1 coverage" bullet;
    # Disposition 05 ordering items 1, 4 and 5; Scope 02 F1 order item 3: the later available
    # entry's consistency mismatch is positive evidence and wins over the deferred unavailability.
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)  # Scope 04 F2_mapping
    # Case validity: the scan met the earlier entry as unavailable and went on to the mismatch.
    assert scanned_past(scan.take(), unavailable, mismatch)
    assert calls == [] and fixture.written_W(study) == []
    prior.assert_attempts_private_free(study)
    # The unrelated unavailable entry returns byte-identical, then the mismatch is removed too:
    # neither repair yields PASS.
    assert_stays_refused(study, calls, [FAILED], restore, mismatch.unlink)


@pytest.mark.parametrize("state, restoration", [("directory", "exact"), ("read_error", "exact"),
                                                ("directory", "altered")])
def test_d8_01_earlier_unavailable_entry_alone_is_unavailable_until_its_exact_bytes_return(
        state, restoration, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    scan, restore, unavailable = arm(study, "entry-before", monkeypatch, state)
    own = prior.durable(study, "registry")
    assert unavailable.name < own.name
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # D8-01 item 5 and its second coverage bullet; Disposition 05 ordering item 6 and the table row
    # "no mismatch + other-G unavailable": with no positive mismatch anywhere, UNAVAILABLE.
    assert fixture.labels(study) == [UNAVAILABLE]
    assert isinstance(error, pv.Unavailable)
    # Case validity, and D8-01 item 3: the scan met the earlier entry and still read this G's entry.
    assert scanned_past(scan.take(), unavailable, own)
    assert calls == [] and fixture.written_W(study) == []
    restore()
    if restoration == "exact":
        # Scope 04 recovery item 1; Disposition 05 retry row: once exactly the unavailable evidence
        # returns, a new attempt against the same S passes.
        reference = fixture.produce(study)
        assert fixture.labels(study) == [UNAVAILABLE, PASS] and len(calls) == 1
        assert records.record_ref(fixture.read_W(study)) == reference
        return
    # Reading: an entry that returns with other bytes is not the exact evidence. It is an available
    # entry failing its G-record consistency check (Scope 02 F1: an inconsistent restoration is
    # FAILED_VERIFICATION; D8-01 complete ordering), and the failure is terminal.
    exact = unavailable.read_bytes()
    altered = {**json.loads(exact), "operation_id": "synthetic-altered-operation"}
    prior.replace_file(unavailable, records.canonical_bytes(altered) + b"\n")
    error = attempt(study)
    assert fixture.labels(study) == [UNAVAILABLE, FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    assert_stays_refused(study, calls, [UNAVAILABLE, FAILED],
                         lambda: prior.replace_file(unavailable, exact))


@pytest.mark.parametrize("trigger", ["event", "G-record"])
def test_d8_01_event_or_G_record_unavailable_to_the_scan_never_masks_another_entry_mismatch(
        trigger, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    scan, restore, unavailable = arm(study, trigger, monkeypatch)
    mismatch = misfiled_entry(study)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # D8-01 third coverage bullet (event-file unavailable plus another available registry
    # mismatch) and complete ordering; Scope 04 new_qualification (event-file or G-record
    # unavailability + another registry mismatch): FAILED_VERIFICATION.
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    assert scanned_past(scan.take(), unavailable, mismatch)  # Case validity
    assert calls == [] and fixture.written_W(study) == []
    assert_stays_refused(study, calls, [FAILED], restore, mismatch.unlink)


@pytest.mark.parametrize("trigger, form", [("entry-before", "substituted"), ("event", "corrupt"),
                                           ("G-record", "substituted")])
def test_s7_iq_f1_this_G_wrong_registry_bytes_with_scan_unavailability_fail_verification(
        trigger, form, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    own = prior.durable(study, "registry")
    expected = own.read_bytes()
    prior.replace_file(own, prior.wrong_bytes(study, "registry", form, tmp_path))
    scan, restore, _ = arm(study, trigger, monkeypatch)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # Disposition 05 S7-IQ-F1 required result, ordering items 2 and 4 and the table rows
    # "current-G mismatch + other-G unavailable" and "+ event-file unavailable"; D8-01 fourth
    # coverage bullet; Scope 04 F1_ordering item 1 (checked first, never dependent on the scan).
    # The G-record row is the state the Seal-07 reproduction recorded UNAVAILABLE, then PASS.
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    # Case validity: any scan the producer still runs meets the unavailability. Whether it scans
    # at all once this G's own entry mismatches is not prescribed.
    assert all(call["unavailable"] for call in scan.take())
    assert calls == [] and fixture.written_W(study) == []
    prior.assert_attempts_private_free(study)
    # The scan unavailability is repaired, then this G's exact entry returns: never PASS.
    assert_stays_refused(study, calls, [FAILED], restore,
                         lambda: prior.replace_file(own, expected))


@pytest.mark.parametrize("trigger, form", [("entry-before", "substituted"), ("event", "corrupt"),
                                           ("G-record", "substituted"), ("own-entry", "corrupt")])
def test_s7_iq_f1_marker_mismatch_with_scan_unavailability_fails_verification(
        trigger, form, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    marker = prior.durable(study, "marker")
    expected = marker.read_bytes()
    prior.replace_file(marker, prior.wrong_bytes(study, "marker", form, tmp_path))
    scan, restore, unavailable = arm(study, trigger, monkeypatch)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # Disposition 05 ordering items 3 and 4 and the table rows "marker mismatch + other-G
    # unavailable" and "+ event-file unavailable"; D8-01 fifth coverage bullet; Scope 02 F1 order
    # item 3 for this G's own entry unavailable beside the marker (Scope 04 new_qualification).
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    if trigger != "own-entry":  # Case validity: the combined state was reached in the scan
        assert met(scan.take(), unavailable)
    assert calls == [] and fixture.written_W(study) == []
    assert_stays_refused(study, calls, [FAILED], restore,
                         lambda: prior.replace_file(marker, expected))


@pytest.mark.parametrize("trigger", ["entry-after", "event", "G-record"])
def test_s7_iq_f1_scan_unavailability_without_mismatch_is_unavailable_until_exact_restoration(
        trigger, bases, tmp_path, monkeypatch, request):
    study = issued(bases, tmp_path)
    scan, restore, unavailable = arm(study, trigger, monkeypatch)
    spied = prior.scientific_spy(monkeypatch)
    entropy = fixture.entropy_spy(monkeypatch, request)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # Disposition 05 ordering item 6 and the table rows "no mismatch + other-G unavailable" and
    # "+ event-file unavailable"; D8-01 complete ordering; Planning Revision 02 section 3 first
    # rule: registry evidence unavailable during verification is UNAVAILABLE.
    assert fixture.labels(study) == [UNAVAILABLE]
    assert isinstance(error, pv.Unavailable)
    assert met(scan.take(), unavailable)  # Case validity
    assert calls == [] and fixture.written_W(study) == []
    prior.assert_attempts_private_free(study)
    restore()  # exactly the unavailable evidence returns; nothing else changes
    reference = fixture.produce(study)
    # Scope 04 recovery item 1; Disposition 05 retry row: a pure UNAVAILABLE condition recovers.
    assert fixture.labels(study) == [UNAVAILABLE, PASS] and len(calls) == 1
    assert records.record_ref(fixture.read_W(study)) == reference
    assert not any(call["unavailable"] for call in scan.take())
    # Scope 02 F1 recovery_constraint: no draw, generation, registration, marking or append.
    assert spied["calls"] == [] and set(spied["operations"]) == {"private_verification"}
    assert entropy == []


@pytest.mark.parametrize("state, companion", [("missing", "alone"),
                                              ("directory", "consistent-entry"),
                                              ("read_error", "consistent-entry")])
def test_s7_iq_f1_this_G_entry_unavailable_keeps_the_frozen_availability_behavior(
        state, companion, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    if companion == "consistent-entry":
        other_entry(study, before=True)
    own = prior.durable(study, "registry")
    restore = prior.make_unavailable(state, own, monkeypatch)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # Disposition 05 table row "current-G registry itself unavailable" with Scope 02 F1
    # classification (missing or unreadable: UNAVAILABLE). No mismatch evidence is manufactured,
    # neither from this G's unavailable entry nor from the consistent entry beside it that the
    # scan may still examine (D8-01 item 6).
    assert fixture.labels(study) == [UNAVAILABLE]
    assert isinstance(error, pv.Unavailable)
    assert calls == [] and fixture.written_W(study) == []
    # Scope 02 F1 recovery_constraint: the producer neither recreates nor replaces the entry.
    if state == "missing":
        assert not own.exists()
    elif state == "directory":
        assert own.is_dir()
    restore()
    reference = fixture.produce(study)
    assert fixture.labels(study) == [UNAVAILABLE, PASS] and len(calls) == 1
    assert records.record_ref(fixture.read_W(study)) == reference


@pytest.mark.parametrize("state, form", [("missing", "misfiled"), ("directory", "G-operation")])
def test_d8_01_this_G_entry_unavailable_does_not_mask_another_entry_mismatch(
        state, form, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    mismatch = later_mismatch(study, form)
    own = prior.durable(study, "registry")
    restore = prior.make_unavailable(state, own, monkeypatch)
    scan = Scan(monkeypatch, study)
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study)
    # Reading (Disposition 05 table row "current-G registry itself unavailable" beside another
    # entry): the row fixes the single condition only. D8-01 item 3 ("continue examining every
    # registry item whose evidence remains available") and item 4, with the complete ordering
    # ("other available registry-entry consistency mismatch -> FAILED_VERIFICATION" ranks above
    # "event/registry unavailability with no available positive mismatch"), make an available
    # inconsistent entry positive evidence that is actually observed, not manufactured. So this
    # G's unavailable entry plus another available inconsistent entry is FAILED_VERIFICATION, as
    # Scope 04 new_qualification also lists. The implementer-derived DV8-5 is not the source.
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    assert any(mismatch in call["reads"] for call in scan.take())  # Case validity
    assert calls == [] and fixture.written_W(study) == []
    assert_stays_refused(study, calls, [FAILED], restore, mismatch.unlink)


@pytest.mark.parametrize("state", ["consistent-entries", "entry-mismatch-alone"])
def test_d8_01_single_conditions_keep_their_classification(state, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    scan = Scan(monkeypatch, study)
    calls = fixture.verifier_spy(monkeypatch)
    if state == "consistent-entries":
        other_entry(study, before=True)
        other_entry(study, before=False)
        reference = fixture.produce(study)
        # D8-01 "fully valid registry -> same result as before": the attempt passes.
        assert fixture.labels(study) == [PASS] and len(calls) == 1
        assert records.record_ref(fixture.read_W(study)) == reference
        assert all(not call["unavailable"] and call["raised"] is None for call in scan.take())
        return
    mismatch = misfiled_entry(study)
    error = attempt(study)
    # D8-01 "mismatch alone -> same FAILED_VERIFICATION as before"; Scope 02 F1 order item 3.
    assert fixture.labels(study) == [FAILED]
    assert not isinstance(error, records.DurableUnavailable)
    assert any(mismatch in call["reads"] for call in scan.take())
    assert_stays_refused(study, calls, [FAILED], mismatch.unlink)


# ==== registered_producers contract (direct) and DV8-3 ==========================================

@pytest.mark.parametrize("state", ["consistent", "mismatch", "unavailable",
                                   "unavailable-then-mismatch", "mismatch-then-unavailable"])
def test_registered_producers_contract_positive_mismatch_wins_wherever_it_sorts(
        state, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    G = study.log.bindings["G"]["digest"]
    if state == "consistent":
        path, raw = other_entry(study, before=True)
        result = study.log.registered_producers()
        # Scope 04 registered_producers_contract: with no mapped read unavailable the scan reads as
        # before; D8-01 "fully valid registry -> same result as before".
        assert set(result) == {G, path.stem}
        own = prior.durable(study, "registry").read_bytes()
        assert records.canonical_bytes(result[G]) + b"\n" == own
        assert records.canonical_bytes(result[path.stem]) + b"\n" == raw
        return
    if state == "mismatch":
        misfiled_entry(study)
    elif state == "unavailable":
        prior.make_unavailable("directory", other_entry(study, before=True)[0], monkeypatch)
    elif state == "unavailable-then-mismatch":
        prior.make_unavailable("directory", other_entry(study, before=True)[0], monkeypatch)
        misfiled_entry(study, LAST)
    else:
        assert state == "mismatch-then-unavailable"
        misfiled_entry(study, FIRST)
        prior.make_unavailable("directory", other_entry(study, before=False)[0], monkeypatch)
    with pytest.raises(records.IntegrityError) as raised:
        study.log.registered_producers()
    if state == "unavailable":
        # Scope 04 contract item 2: with no positive mismatch, the deferred typed unavailability.
        assert isinstance(raised.value, auth.ProducerRegistryUnavailable)
        assert isinstance(raised.value, records.DurableUnavailable)
    else:
        # D8-01 items 4 and 5; Scope 04 contract items 2 and 3: positive mismatch evidence raises
        # as itself, whether it sorts before or after the unavailable entry, and alone as before.
        assert not isinstance(raised.value, records.DurableUnavailable)


def durable_reads(monkeypatch, study: fixture.Study) -> dict[str, list[Path]]:
    """Reads under the authority root: every durable read the authority module attempts through
    its regular-file reader, and every file actually opened for reading."""
    root, seen = study.log.root, {"attempted": [], "opened": []}
    reader, opener = auth.regular_bytes, Path.open

    def attempted(path):
        if Path(path).is_relative_to(root):
            seen["attempted"].append(Path(path))
        return reader(path)

    def opened(path, mode="r", *args, **kwargs):
        if "r" in mode and path.is_relative_to(root):
            seen["opened"].append(path)
        return opener(path, mode, *args, **kwargs)

    monkeypatch.setattr(auth, "regular_bytes", attempted)
    monkeypatch.setattr(Path, "open", opened)
    return seen


def drained(seen: dict[str, list[Path]]) -> tuple[Counter, Counter]:
    result = Counter(seen["attempted"]), Counter(seen["opened"])
    seen["attempted"].clear()
    seen["opened"].clear()
    return result


@pytest.mark.parametrize("trigger", ["entry-before", "event", "G-record"])
def test_dv8_3_deferral_consults_no_registry_object_beyond_the_unchanged_traversal(
        trigger, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    other, _ = other_entry(study, before=True)  # consistent, so the baseline traverses it fully
    own_G = retain_generation_record(study)
    other_G = study.log.root / "evidence-records" / (other.stem + ".json")
    events = fixture.event_files(study)
    target = {"entry-before": other, "event": consume_event(study), "G-record": own_G}[trigger]
    seen = durable_reads(monkeypatch, study)
    baseline = study.log.registered_producers()
    attempted_before, opened_before = drained(seen)
    restore = prior.make_unavailable("directory", target, monkeypatch)
    drained(seen)  # the fixture's own read of the target is not a scan read
    with pytest.raises(records.DurableUnavailable):
        study.log.registered_producers()
    attempted, opened = drained(seen)
    restore()
    # DV8-3 (confirmed as a scope constraint): option C adds no registry read; nothing is consulted
    # beyond the unchanged traversal of the same registry, and the non-regular object is never
    # opened (Planning Revision 02 section 3).
    assert not attempted - attempted_before and not opened - opened_before
    assert attempted[target] and not opened[target]
    # D8-01 item 3: every item whose evidence remains available is still examined. Only the reads
    # that need an unavailable entry's own content (its G record and event checks) may drop out.
    skipped = attempted_before - attempted
    assert set(skipped) <= ({other_G, *events} if trigger == "entry-before" else set())
    assert attempted[prior.durable(study, "registry")] == 1
    # Exact restoration reads exactly as before.
    assert study.log.registered_producers() == baseline
    assert drained(seen) == (attempted_before, opened_before)


# ==== S7-IQ-F2 (DV8-1): the protected verification boundary decides ===========================

@pytest.mark.parametrize("source", ["active", "retained-S", "source-checker", "prior-outcome"])
def test_s7_iq_f2_unavailability_before_protected_verification_is_refused_precondition(
        source, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    log, earlier = study.log, []
    tip = log.tip
    if source == "active":
        target = log.root / "active.json"
    elif source == "retained-S":
        target = log.root / "evidence-records" / (study.S["digest"] + ".json")
    elif source == "source-checker":  # the audited checker over a synthetic pinned source
        target = tmp_path / "synthetic-pinned-source.txt"
        target.write_bytes(b"synthetic pinned source\n")
        manifest = {target.name: fixture.sha(target.read_bytes())}
        log.source_check = auth.pinned_source_checker(
            tmp_path, {"body": {"implementation_sources": manifest}},
            {"body": {"qualification_sources": manifest}}, log.bindings["P"])
    else:
        # An earlier attempt left an UNAVAILABLE outcome record (this G's registry entry was
        # missing, then returned byte-identical); the producer's own preconditions read it.
        assert source == "prior-outcome"
        restore = prior.make_unavailable("missing", prior.durable(study, "registry"), monkeypatch)
        attempt(study, tip)
        restore()
        earlier = [UNAVAILABLE]
        target = fixture.w_folder(study) / "attempt-0001.outcome.json"
    restore = prior.make_unavailable("directory", target, monkeypatch)
    calls = fixture.verifier_spy(monkeypatch)
    reads = fixture.private_read_spy(monkeypatch, study)
    error = attempt(study, tip)
    # Scope 04 new_qualification: the typed Unavailable still reaches the caller.
    assert isinstance(error, pv.Unavailable) and pv.Unavailable is records.DurableUnavailable
    # Planning Revision 02 section 3 second rule: the action and private verification do not run.
    assert calls == [] and reads == [] and fixture.written_W(study) == []
    restore()  # the outcome records are read only once the exact bytes are back
    # Disposition 05 S7-IQ-F2 "before protected verification state has been successfully entered";
    # DV8-1; Scope 04 F2_mapping (protected entry and _preconditions): REFUSED_PRECONDITION.
    assert fixture.labels(study) == [*earlier, REFUSED]
    # Scope 04 recovery item 3: a REFUSED_PRECONDITION from unavailability is not terminal.
    reference = fixture.produce(study, expected_tip=tip)
    assert fixture.labels(study) == [*earlier, REFUSED, PASS] and len(calls) == 1
    assert records.record_ref(fixture.read_W(study)) == reference


@pytest.mark.parametrize("target, phase, expected", [
    ("event", "entry", REFUSED), ("event", "verification", UNAVAILABLE),
    ("G-record", "entry", REFUSED), ("G-record", "verification", UNAVAILABLE),
    ("salt", "verification", UNAVAILABLE)])
def test_dv8_1_the_protected_verification_boundary_not_the_unavailability_decides(
        target, phase, expected, bases, tmp_path, monkeypatch):
    study = issued(bases, tmp_path)
    if target == "event":
        path = consume_event(study)
    elif target == "G-record":
        path = retain_generation_record(study)
    else:
        path = study.log.root / "evidence-raw" / (study.S["body"]["salt"]["sha256_raw"] + ".bin")
    tip = study.log.tip
    if phase == "entry" or target == "salt":
        restore = prior.make_unavailable("directory", path, monkeypatch)
        scan = Scan(monkeypatch, study)
    else:  # only the verification-phase registry scan sees the object unavailable
        scan = Scan(monkeypatch, study, path)
        restore = scan.disarm
    calls = fixture.verifier_spy(monkeypatch)
    error = attempt(study, tip)
    # Both sides receive the same typed Unavailable (records.DurableUnavailable).
    assert isinstance(error, pv.Unavailable)
    assert calls == [] and fixture.written_W(study) == []
    if phase == "entry":  # verification never began, so no registry evidence was evaluated
        assert scan.take() == []
    elif target != "salt":
        assert met(scan.take(), path)  # Case validity
    restore()
    # DV8-1 and Disposition 05 S7-IQ-F2: unavailability while establishing protected verification
    # is REFUSED_PRECONDITION; once verification has begun (Planning Revision 02 section 3 first
    # rule: registry and retained scientific evidence) it stays UNAVAILABLE. Not every
    # Unavailable becomes REFUSED_PRECONDITION.
    assert fixture.labels(study) == [expected]
    reference = fixture.produce(study, expected_tip=tip)
    assert fixture.labels(study) == [expected, PASS] and len(calls) == 1
    assert records.record_ref(fixture.read_W(study)) == reference
