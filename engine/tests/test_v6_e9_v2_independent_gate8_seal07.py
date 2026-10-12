"""Independent Seal-07 checks derived from frozen Scope03 and planning rulings.

Author context: /root/seal07_independent_author, starting e035def989dfc5e26ae3eb2c9ccfd16aed54b66c.
No implementer Seal-07 test or scenario/control-flow briefing was consumed. Expected
behavior comes from Scope03 read_map, crash_matrix, exact_recovery, disposition04,
planning rulings01 and plan03. Mechanical seams are names only, not expectations.
Fixtures are the independently authored frozen Seal05/06 synthetic studies: literal
salt and deterministic hash-derived values; REAL is only the declaration field.
No entropy, salt creation, generation, native match or operational publication occurs.
Process-death tests use bounded children; injected modes are not native POSIX proof,
and neither kill nor exceptions prove physical power-loss durability. Results here
are author validation, never independent qualification or operational authorization.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from engine.tests import test_v6_e9_v2_independent_gate8_producer as fixture
from engine.tests import test_v6_e9_v2_independent_gate8_seal06 as prior
from engine.tests._e9_v2_synthetic_records import inventory_status
from tools.research.v6.e9.v2 import authority as auth
from tools.research.v6.e9.v2 import inventory, records
from tools.research.v6.e9.v2 import private_verification as pv

SCOPE_PATH = fixture.FROZEN / "v2_gate8_scope_03.json"
SCOPE_RAW = "75343cf20cde42796a8ad10405cd475360e6c4e90ef8915add59243114143f98"
SCOPE = json.loads(SCOPE_PATH.read_bytes())["body"]
CONTRACT = fixture.FROZEN / "amended_rule_contract_v2_proposed_02.json"
CATALOGUE = fixture.FROZEN / "amended_record_schemas_v2_proposed_02.json"
NONREGULAR = (stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFDIR)


@pytest.fixture
def bases(tmp_path_factory):
    return fixture.base_getter(tmp_path_factory)


def clone(bases, tmp_path, name="issued"):
    return fixture.clone(bases(name), tmp_path)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def scientific_bytes(study) -> dict[str, bytes]:
    refs = [study.S["body"][role] for role in ("payload", "salt", "audit")]
    refs += list(study.refs.values())
    return {ref["sha256_raw"]: (study.log.root / "evidence-raw" /
            (ref["sha256_raw"] + ".bin")).read_bytes() for ref in refs}


def ref_path(study, ref):
    return study.log.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")


def mode_at(monkeypatch, target: Path, mode: int):
    """Model a pre-existing unsupported object, refusing every potentially blocking open."""
    original_stat, original_open = Path.stat, Path.open
    seen = {"stat": 0, "open": 0}

    def changed(path, *args, **kwargs):
        result = original_stat(path, *args, **kwargs)
        if path == target:
            seen["stat"] += 1
            fields = list(result)
            fields[0] = mode | 0o600
            return os.stat_result(fields)
        return result

    def refused_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path == target and "r" in mode:
            seen["open"] += 1
            raise AssertionError("unsupported durable object was opened")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", changed)
    monkeypatch.setattr(Path, "open", refused_open)
    return seen


def mapped_read(study, row, tmp_path):
    """Each row is independently taken from Scope03.read_map, not producer branches."""
    log = study.log
    if row == "S7-R01":
        target = tmp_path / "instrument.txt"
        target.write_bytes(b"synthetic instrument\n")
        manifest = {target.name: digest(target.read_bytes())}
        instrument = {"body": {"implementation_sources": manifest}}
        qualification = {"body": {"qualification_sources": manifest}}
        return target, auth.pinned_source_checker(tmp_path, instrument, qualification,
                                                   log.bindings["P"])
    if row == "S7-R02":
        target = tmp_path / "readback.bin"
        return target, lambda: auth.durable_bytes(target, b"exact readback")
    if row == "S7-R03-event":
        target = fixture.event_files(study)[0]
        return target, lambda: log._state()
    if row == "S7-R03-active":
        return log.root / "active.json", lambda: log._state()
    if row in ("S7-R04", "S7-R05"):
        record = study.records["S"]
        target = log.root / "evidence-records" / (record["digest"] + ".json")
        return target, lambda: (log.resolve(records.record_ref(record)) if row == "S7-R04"
                                else log.retain_record(record))
    if row in ("S7-R06", "S7-R07"):
        ref = study.S["body"]["salt"]
        target = ref_path(study, ref)
        raw = target.read_bytes()
        return target, lambda: (log.retain_artifact(raw, ref["evidence_id"])
                                if row == "S7-R06" else log.read_artifact(ref))
    if row == "S7-R08-other-G":
        target = log.root / "producer-roots" / ("f" * 64 + ".json")
        target.write_bytes(b"{}\n")
        return target, log.registered_producers
    if row == "S7-R08-event":
        return fixture.event_files(study)[0], log.registered_producers
    if row == "S7-R09":
        return CATALOGUE, records.catalogue
    if row in ("S7-R10-inventory", "S7-R10-limitation"):
        if row.endswith("inventory"):
            value = inventory_status()
            return CONTRACT, lambda: records._field("inventory_status", value, "InventoryStatus")
        value = json.loads(CONTRACT.read_bytes())["exact_interpretation"]["permanent_limitation_text"]
        return CONTRACT, lambda: records._field("permanent_limitation", value, "text")
    if row == "S7-R11":
        return records.ADOPTED, lambda: records.read_record(records.ADOPTED, "P")
    if row == "S7-R12":
        return CONTRACT, inventory.frozen_limitations
    if row == "S7-R13":
        target = fixture.w_folder(study) / "attempt-0001.outcome.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(fixture.encode({"outcome": "PASS"}))
        return target, lambda: pv._outcomes(target.parent)
    if row.startswith("S7-R14-"):
        role = row.removeprefix("S7-R14-")
        if role in ("payload", "salt", "generation_audit"):
            ref = study.S["body"]["audit" if role == "generation_audit" else role]
        elif role == "K":
            ref = study.refs["K"]
        elif role == "boundary":
            ref = study.boundary["body"]["evidence"][0]
        else:
            ref = log.retain_artifact(fixture.encode({"kind": "SYNTHETIC-" + role}),
                                       "SYNTHETIC-" + role)
        return ref_path(study, ref), lambda: pv._reader(log)(ref)
    if row == "S7-R15":
        return fixture.event_files(study)[0], lambda: pv._durable_log(log)
    if row.startswith("S7-R16-"):
        role = row.removeprefix("S7-R16-")
        if role in ("registry", "marker"):
            target = prior.durable(study, role)
        else:
            target = fixture.w_folder(study) / ("W.json" if role == "W" else prior.INTENT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"{}\n")
        return target, lambda: pv._durable(target)
    if row == "S7-R17":
        return CONTRACT, pv._frozen_limitation
    raise AssertionError(row)


READ_ROWS = ["S7-R01", "S7-R02", "S7-R03-event", "S7-R03-active", "S7-R04", "S7-R05",
             "S7-R06", "S7-R07", "S7-R08-other-G", "S7-R08-event", "S7-R09",
             "S7-R10-inventory", "S7-R10-limitation", "S7-R11", "S7-R12", "S7-R13",
             *["S7-R14-" + role for role in ("payload", "salt", "generation_audit", "K",
                                             "boundary", "history", "execution", "result")],
             "S7-R15", *["S7-R16-" + role for role in ("registry", "marker", "W", "intent")],
             "S7-R17"]


@pytest.mark.parametrize("row", READ_ROWS)
@pytest.mark.parametrize("mode", NONREGULAR, ids=("fifo", "socket", "character", "block", "directory"))
def test_mapped_durable_reads_reject_nonregular_without_open(row, mode, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    target, call = mapped_read(study, row, tmp_path)
    seen = mode_at(monkeypatch, target, mode)
    try:
        call()
    except (records.IntegrityError, OSError):
        pass
    else:
        assert row.startswith("S7-R16"), "only optional durable-unavailable reads may return None"
    assert seen["stat"] > 0 and seen["open"] == 0


def test_scope_identity_and_complete_requirement_inventory():
    assert digest(SCOPE_PATH.read_bytes()) == SCOPE_RAW
    assert len(SCOPE["read_map"]["rows"]) == 18
    assert len(SCOPE["crash_matrix"]["rows"]) == 15


class Stop(BaseException):
    """Exception-unwind injection; explicitly distinct from process death."""


def output_kind(path: Path, raw: bytes) -> str:
    if path.name.endswith(".intent.json"):
        return "intent"
    if path.name.endswith(".outcome.json"):
        return "outcome"
    if path.name == "W.json":
        return "W"
    value = json.loads(raw)
    if value.get("kind") == prior.RESULT_KIND:
        return "result"
    if value.get("body", {}).get("record_role") == "W":
        return "retained-W"
    return "other"


class Publications:
    """OS-visible no-overwrite install observer independent of producer decision structure."""

    def __init__(self, monkeypatch, study, hook=None):
        self.study, self.hook, self.events = study, hook, []
        original = os.link

        def link(source, destination, *args, **kwargs):
            path = Path(destination)
            if not path.is_relative_to(study.log.root):
                return original(source, destination, *args, **kwargs)
            raw = Path(source).read_bytes()
            kind = output_kind(path, raw)
            self.events.append((kind, path, raw, (study.log.root / "exclusive.lock").exists()))
            if hook:
                hook("before", kind, path, Path(source))
            result = original(source, destination, *args, **kwargs)
            assert path.read_bytes() == raw
            if hook:
                hook("after", kind, path, Path(source))
            return result

        monkeypatch.setattr(os, "link", link)


@pytest.mark.parametrize("boundary,when,kind", [
    ("S7-C03/B2", "before", "intent"), ("S7-C03/B2-after", "after", "intent"),
    ("S7-C06/B5", "before", "result"), ("S7-C06/B5-after", "after", "result"),
    ("S7-C08/B7", "before", "retained-W"), ("S7-C08/B7-after", "after", "retained-W"),
    ("S7-C10/B9", "before", "W"), ("S7-C10/B9-after", "after", "W"),
    ("S7-C12/B11", "before", "outcome"), ("S7-C12/B11-after", "after", "outcome")])
def test_exact_recovery_at_each_atomic_install(boundary, when, kind, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    scientific = scientific_bytes(study)
    fired, durable = [], {}

    def interrupt(moment, label, destination, source):
        if moment == when and label == kind and not fired:
            fired.append(boundary)
            durable.update(prior.tree(study.log.root))
            raise Stop()

    Publications(monkeypatch, study, interrupt)
    with pytest.raises(Stop):
        fixture.produce(study)
    assert fired == [boundary] and scientific_bytes(study) == scientific
    assert prior.lock_free(study)  # exception unwind, not crash recovery
    old = prior.tree(study.log.root)
    verifier = fixture.verifier_spy(monkeypatch)
    if kind == "outcome" and when == "after":
        with pytest.raises(records.IntegrityError):
            fixture.produce(study)
        assert verifier == []
    else:
        reference = fixture.produce(study)
        assert len(verifier) == 1
        assert fixture.labels(study) == ["PASS"]
        assert records.record_ref(fixture.read_W(study)) == reference
        assert fixture.outcomes(study)[0]["interrupted_prior_attempts"] == [1]
    after = prior.tree(study.log.root)
    assert all(after[name] == raw for name, raw in old.items())
    assert scientific_bytes(study) == scientific


def interrupt_complete_W(monkeypatch, study):
    fired = []

    def stop(moment, kind, destination, source):
        if moment == "before" and kind == "outcome" and not fired:
            fired.append(True)
            raise Stop()

    Publications(monkeypatch, study, stop)
    with pytest.raises(Stop):
        fixture.produce(study)
    assert fired and fixture.w_folder(study).joinpath("W.json").exists()


@pytest.mark.parametrize("event", ("HOLD", "ISSUE", "extended-ISSUE"))
def test_F2_any_intervening_authority_event_refuses_without_scientific_failure(
        event, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    W = (fixture.w_folder(study) / "W.json").read_bytes()
    if event == "HOLD":
        fixture.hold(study, "seal07-intervened")
    else:
        if event == "extended-ISSUE":
            study.log.bindings = {**study.log.bindings, "W": records.record_ref(json.loads(W))}
        study.log.append("ISSUE", fixture.LEAD, expected_tip=study.log.tip, operation_id=fixture.OP)
    seen = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert seen == []
    assert set(fixture.labels(study)) <= {"REFUSED_PRECONDITION"}
    assert (fixture.w_folder(study) / "W.json").read_bytes() == W


@pytest.mark.parametrize("target", ("W", "result", "retained-W"))
@pytest.mark.parametrize("damage", ("partial", "reencoded", "substituted"))
def test_F2_published_output_mismatch_is_preserved_and_never_PASS(
        target, damage, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    W = fixture.read_W(study)
    path = fixture.w_folder(study) / "W.json"
    if target == "result":
        ref = next(ref for ref in W["body"]["evidence"] if ref["evidence_id"] == prior.RESULT_ID)
        path = ref_path(study, ref)
    elif target == "retained-W":
        path = study.log.root / "evidence-records" / (W["digest"] + ".json")
    raw = path.read_bytes()
    changed = (raw[:len(raw) // 2] if damage == "partial" else
               json.dumps(json.loads(raw), indent=2).encode() + b"\n" if damage == "reencoded" else
               raw.replace(b"PASS", b"FAIL", 1))
    assert changed != raw
    path.write_bytes(changed)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert path.read_bytes() == changed and "PASS" not in fixture.labels(study)


def test_legacy_torn_canonical_W_has_no_recovery_provenance(bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    path = fixture.w_folder(study) / "W.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(prior.PARTIAL_W)
    seen = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert seen == [] and path.read_bytes() == prior.PARTIAL_W
    assert set(fixture.labels(study)) <= {"REFUSED_PRECONDITION"}


def test_B12_post_PASS_recheck_error_keeps_exact_single_PASS(bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)

    def drift(moment, kind, destination, source):
        if moment == "after" and kind == "outcome":
            study.flags["source_drift"] = True

    Publications(monkeypatch, study, drift)
    with pytest.raises(records.IntegrityError, match="source pin drift"):
        fixture.produce(study)
    assert fixture.labels(study) == ["PASS"] and prior.lock_free(study)


def test_B13_lost_response_does_not_allow_second_verification_or_PASS(bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    fixture.produce(study)
    original = prior.tree(study.log.root)
    calls = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert calls == [] and fixture.labels(study).count("PASS") == 1
    after = prior.tree(study.log.root)
    assert all(after[name] == raw for name, raw in original.items())


@pytest.mark.parametrize("case,expected", [("salt_missing", "UNAVAILABLE"),
                                           ("held", "REFUSED_PRECONDITION"),
                                           ("tail", "FAILED_VERIFICATION")])
@pytest.mark.parametrize("when", ("before", "after"))
def test_E2_nonPASS_publication_is_after_lease_and_interruption_is_not_terminal(
        case, expected, when, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    if case == "salt_missing":
        ref_path(study, study.S["body"]["salt"]).unlink()
    elif case == "held":
        fixture.hold(study, "seal07-held")
    else:
        prior.tail_event(study, "recorder_consume")
    fired = []

    def stop(moment, kind, destination, source):
        if kind == "outcome":
            assert not (study.log.root / "exclusive.lock").exists()
            if moment == when and not fired:
                fired.append(True)
                raise Stop()

    Publications(monkeypatch, study, stop)
    with pytest.raises(Stop):
        fixture.produce(study)
    assert fired
    assert fixture.labels(study) == ([expected] if when == "after" else [])
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    if when == "after" and expected == "FAILED_VERIFICATION":
        assert fixture.labels(study) == [expected, "REFUSED_PRECONDITION"]
    else:
        assert fixture.labels(study)[-1] == expected


def test_B3_stale_lock_requires_manual_prerequisite_and_is_never_deleted(bases, tmp_path):
    study = clone(bases, tmp_path)
    lock = study.log.root / "exclusive.lock"
    raw = b"synthetic dead-holder incident evidence\n"
    lock.write_bytes(raw)
    before = lock.stat()
    with pytest.raises(records.IntegrityError, match="busy|interrupted"):
        pv.produce_private_verification(study.log, verifier=fixture.VERIFIER,
            expected_tip=study.issue_S["digest"], operation_id="synthetic-lock-refusal")
    assert lock.read_bytes() == raw
    assert lock.stat().st_mtime_ns == before.st_mtime_ns
    assert fixture.written_W(study) == []


@pytest.mark.parametrize("pass_number", (1, 2), ids=("entry", "post-PASS-recheck"))
def test_R01_audited_source_checker_rejects_at_both_protected_checks(
        pass_number, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    target, check = mapped_read(study, "S7-R01", tmp_path)
    count = []

    def checked():
        count.append(True)
        if len(count) == pass_number:
            with monkeypatch.context() as patch:
                seen = mode_at(patch, target, stat.S_IFIFO)
                try:
                    check()
                finally:
                    assert seen["stat"] and not seen["open"]
        else:
            check()

    study.log.source_check = checked
    calls = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert len(count) == pass_number
    assert len(calls) == (0 if pass_number == 1 else 1)
    assert fixture.labels(study) == (["REFUSED_PRECONDITION"] if pass_number == 1 else ["PASS"])


@pytest.mark.parametrize("race", ("opened-type", "opened-identity", "read-identity", "read-size"))
def test_regular_reader_checks_opened_and_consumed_object_and_closes(race, tmp_path, monkeypatch):
    path = tmp_path / "exact.bin"
    path.write_bytes(b"complete retained bytes")
    original_open, original_fstat = Path.open, os.fstat
    streams, calls = [], []

    def tracked(file, *args, **kwargs):
        stream = original_open(file, *args, **kwargs)
        if file == path:
            streams.append(stream)
        return stream

    def changed(fd):
        value = original_fstat(fd)
        calls.append(fd)
        fields = list(value)
        if race == "opened-type" and len(calls) == 1:
            fields[0] = stat.S_IFSOCK | 0o600
        if race == "opened-identity" and len(calls) == 1 or race == "read-identity" and len(calls) == 2:
            fields[1] += 1
        if race == "read-size" and len(calls) == 2:
            fields[6] += 1
        return os.stat_result(fields)

    monkeypatch.setattr(Path, "open", tracked)
    monkeypatch.setattr(os, "fstat", changed)
    with pytest.raises(records.IntegrityError):
        records.regular_bytes(path)
    assert streams and all(stream.closed for stream in streams)


def test_regular_reader_never_caches_type_and_preserves_regular_symlinks(tmp_path, monkeypatch):
    target, link = tmp_path / "target.bin", tmp_path / "link.bin"
    target.write_bytes(b"exact")
    assert records.regular_bytes(target) == b"exact"
    with monkeypatch.context() as patch:
        seen = mode_at(patch, target, stat.S_IFIFO)
        with pytest.raises(records.IntegrityError):
            records.regular_bytes(target)
        assert seen["stat"] and not seen["open"]
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"native symlink creation unavailable on this root: {exc.winerror}")
    assert records.regular_bytes(link) == b"exact"


@pytest.mark.parametrize("role", ("candidate", "canonical"))
@pytest.mark.parametrize("mode", NONREGULAR, ids=("fifo", "socket", "character", "block", "directory"))
def test_R18_publication_comparisons_share_regular_boundary(role, mode, tmp_path, monkeypatch):
    canonical, candidate = tmp_path / "canonical.json", tmp_path / "staging.json"
    raw = fixture.encode({"complete": True})
    if role == "canonical":
        canonical.write_bytes(raw)
    seen = None

    def writer(path, material):
        nonlocal seen
        auth.durable_bytes(path, material)
        seen = mode_at(monkeypatch, candidate, mode)

    if role == "canonical":
        seen = mode_at(monkeypatch, canonical, mode)
    with pytest.raises(records.IntegrityError):
        records.publish_once(canonical, raw, candidate, writer=writer)
    assert seen is not None and seen["stat"] and not seen["open"]


def test_publication_flushes_readbacks_and_installs_without_overwrite(tmp_path, monkeypatch):
    canonical = tmp_path / "new-parent" / "canonical.json"
    candidate = tmp_path / "new-parent" / "candidate.json"
    raw, events = fixture.encode({"exact": "canonical"}), []
    original_link, original_fsync = os.link, os.fsync

    def fsync(fd):
        events.append("file-flush")
        return original_fsync(fd)

    def link(source, target, *args, **kwargs):
        assert Path(source).read_bytes() == raw and not Path(target).exists()
        assert "file-flush" in events
        events.append("install")
        return original_link(source, target, *args, **kwargs)

    def directory(path):
        events.append(("metadata", path))
        return False  # explicit platform limit does not fabricate a successful native flush

    monkeypatch.setattr(os, "fsync", fsync)
    monkeypatch.setattr(os, "link", link)
    monkeypatch.setattr(records, "flush_directory", directory)
    records.publish_once(canonical, raw, candidate, writer=auth.durable_bytes)
    assert canonical.read_bytes() == candidate.read_bytes() == raw
    assert events[-1] == ("metadata", canonical.parent)
    assert ("metadata", canonical.parent.parent) in events
    before = canonical.stat()
    records.publish_once(canonical, raw, candidate, writer=lambda *_: pytest.fail("canonical rewritten"))
    assert canonical.stat().st_mtime_ns == before.st_mtime_ns
    with pytest.raises(records.IntegrityError):
        records.publish_once(canonical, raw + b"changed", tmp_path / "other", writer=auth.durable_bytes)
    assert canonical.read_bytes() == raw


@pytest.mark.parametrize("collision", ("exact", "wrong"))
def test_atomic_publication_collision_compares_without_overwrite(collision, tmp_path, monkeypatch):
    canonical, candidate = tmp_path / "canonical", tmp_path / "candidate"
    raw = fixture.encode({"exact": True})

    def collided(source, target, *args, **kwargs):
        Path(target).write_bytes(raw if collision == "exact" else b"foreign retained bytes")
        raise FileExistsError(errno.EEXIST, "synthetic ordinary race")

    monkeypatch.setattr(os, "link", collided)
    if collision == "wrong":
        with pytest.raises(records.IntegrityError):
            records.publish_once(canonical, raw, candidate, writer=auth.durable_bytes)
        assert canonical.read_bytes() == b"foreign retained bytes"
    else:
        records.publish_once(canonical, raw, candidate, writer=auth.durable_bytes)
        assert canonical.read_bytes() == raw
    assert candidate.read_bytes() == raw


def test_unsupported_atomic_backend_refuses_without_direct_write_fallback(tmp_path, monkeypatch):
    canonical, candidate = tmp_path / "canonical", tmp_path / "candidate"
    raw = fixture.encode({"exact": True})

    def unsupported(*args, **kwargs):
        raise OSError(errno.ENOTSUP, "synthetic unsupported hard links")

    monkeypatch.setattr(os, "link", unsupported)
    monkeypatch.setattr(os, "replace", lambda *_: pytest.fail("overwrite-capable fallback"))
    monkeypatch.setattr(os, "rename", lambda *_: pytest.fail("rename fallback"))
    with pytest.raises(OSError):
        records.publish_once(canonical, raw, candidate, writer=auth.durable_bytes)
    assert not canonical.exists() and candidate.read_bytes() == raw


class CandidateFault:
    """Mechanical scoped writer interception; original canonical expectations stay fixed."""

    def __init__(self, monkeypatch, wanted, condition):
        self.fired, self.candidates = [], {}
        pending = []
        original_publish, original_writer = pv._publish, pv.durable_bytes

        def publication(folder, ordinal, path, raw):
            pending.append(output_kind(path, raw))
            try:
                return original_publish(folder, ordinal, path, raw)
            finally:
                pending.pop()

        def writer(path, raw):
            if pending and pending[-1] == wanted and not self.fired:
                self.fired.append(wanted)
                if condition == "partial":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw[:len(raw) // 2])
                elif condition == "complete":
                    original_writer(path, raw)
                self.candidates[path] = path.read_bytes() if path.exists() else None
                raise Stop()
            return original_writer(path, raw)

        monkeypatch.setattr(pv, "_publish", publication)
        monkeypatch.setattr(pv, "durable_bytes", writer)


@pytest.mark.parametrize("requirement,kind", [
    ("S7-C02/B1", "intent"), ("S7-C05/B4", "result"), ("S7-C07/B6", "retained-W"),
    ("S7-C09/B8", "W"), ("S7-C11/B10", "outcome")])
@pytest.mark.parametrize("condition", ("absent", "partial", "complete"))
def test_candidate_interruptions_rederive_same_state_and_preserve_old_candidate(
        requirement, kind, condition, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    original = scientific_bytes(study)
    injected = CandidateFault(monkeypatch, kind, condition)
    with pytest.raises(Stop):
        fixture.produce(study)
    assert injected.fired == [kind], requirement
    assert fixture.labels(study) == [] and prior.lock_free(study)
    calls = fixture.verifier_spy(monkeypatch)
    reference = fixture.produce(study)
    assert len(calls) == 1 and fixture.labels(study) == ["PASS"]
    assert records.record_ref(fixture.read_W(study)) == reference
    assert fixture.outcomes(study)[0]["interrupted_prior_attempts"] == [1]
    for path, raw in injected.candidates.items():
        assert (path.read_bytes() if path.exists() else None) == raw
    assert scientific_bytes(study) == original


@pytest.mark.parametrize("case,expected", [("salt_missing", "UNAVAILABLE"),
                                           ("held", "REFUSED_PRECONDITION"),
                                           ("tail", "FAILED_VERIFICATION")])
def test_C15_E1_torn_nonPASS_candidate_does_not_invent_terminal_failure(
        case, expected, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    if case == "salt_missing":
        ref_path(study, study.S["body"]["salt"]).unlink()
    elif case == "held":
        fixture.hold(study, "seal07-outcome-staging")
    else:
        prior.tail_event(study, "recorder_consume")
    fault = CandidateFault(monkeypatch, "outcome", "partial")
    with pytest.raises(Stop):
        fixture.produce(study)
    assert fault.fired and not fixture.outcomes(study)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert fixture.labels(study) == [expected]
    assert all(path.read_bytes() == raw for path, raw in fault.candidates.items())


@pytest.mark.parametrize("changed", ("verifier", "source", "payload", "salt", "audit", "K"))
def test_F2_recovery_rejects_scientific_or_instrument_substitution(changed, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    raw_W = (fixture.w_folder(study) / "W.json").read_bytes()
    if changed == "verifier":
        call = lambda: fixture.produce(study, verifier=fixture.SECOND_CHECKER)
    else:
        if changed == "source":
            study.flags["source_drift"] = True
        else:
            ref = study.refs["K"] if changed == "K" else study.S["body"][changed]
            path = ref_path(study, ref)
            path.write_bytes(path.read_bytes() + b"substitution")
        call = lambda: fixture.produce(study)
    with pytest.raises(records.IntegrityError):
        call()
    assert "PASS" not in fixture.labels(study)
    assert (fixture.w_folder(study) / "W.json").read_bytes() == raw_W


@pytest.mark.parametrize("outcome", ("FAILED_VERIFICATION", "PASS"))
def test_F2_contradictory_completed_outcome_blocks_before_verifier(outcome, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    folder = fixture.w_folder(study)
    W = fixture.read_W(study)
    (folder / prior.OUTCOME).write_bytes(fixture.encode({"attempt": 1, "outcome": outcome,
        "reason": None, "W": records.record_ref(W) if outcome == "PASS" else None,
        "interrupted_prior_attempts": []}))
    calls = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert calls == [] and fixture.labels(study).count("PASS") <= 1


def death_driver(root: str, configuration: str, kind: str, when: str):
    """Bounded-child entry point. All scientific material was prepared by the parent fixture."""
    from tools.research.v6.e9.v2.qualification_guard import prohibit_experiment_producers

    patch = pytest.MonkeyPatch()
    prohibit_experiment_producers.__wrapped__(patch)
    config = json.loads(Path(configuration).read_bytes())
    checks = []

    def source_check():
        checks.append(True)
        if kind == "recheck" and len(checks) == 2:
            os._exit(79)

    log = auth.AuthorityLog(Path(root), fixture.STUDY, config["bindings"], actors=config["actors"],
        resolver=lambda ref: config["records"][ref["digest"]], source_check=source_check)
    original_link, original_publish, original_writer = os.link, pv._publish, pv.durable_bytes
    pending = []

    def publication(folder, ordinal, path, raw):
        pending.append(output_kind(path, raw))
        try:
            return original_publish(folder, ordinal, path, raw)
        finally:
            pending.pop()

    def writer(path, raw):
        if when == "partial-candidate" and pending[-1] == kind:
            with path.open("xb") as stream:
                stream.write(raw[:len(raw) // 2])
                stream.flush()
                os.fsync(stream.fileno())
            os._exit(79)
        return original_writer(path, raw)

    def link(source, destination, *args, **kwargs):
        label = output_kind(Path(destination), Path(source).read_bytes())
        if when == "before-install" and label == kind:
            os._exit(79)
        result = original_link(source, destination, *args, **kwargs)
        if when == "after-install" and label == kind:
            os._exit(79)
        return result

    patch.setattr(pv, "_publish", publication)
    patch.setattr(pv, "durable_bytes", writer)
    patch.setattr(os, "link", link)
    if kind == "allocation":
        original_mkdir = Path.mkdir

        def allocated(path, *args, **kwargs):
            result = original_mkdir(path, *args, **kwargs)
            if path.name == "attempt-0001.staging":
                os._exit(79)
            return result

        patch.setattr(Path, "mkdir", allocated)
    if kind == "verification":
        patch.setattr(pv, "verify_complete_private", lambda **_: os._exit(79))
    pv.produce_private_verification(log, verifier=fixture.VERIFIER, expected_tip=config["tip"],
                                   operation_id=fixture.PV_OP)
    if kind == "returned":
        os._exit(79)
    raise AssertionError("selected death boundary was not reached")


def dead_child(study, tmp_path, kind, when, sequence):
    configuration = tmp_path / f"child-input-{sequence}.json"
    configuration.write_bytes(fixture.encode({"bindings": study.log.bindings,
        "actors": study.log.actors, "records": study.by_digest, "tip": study.log.tip}))
    expression = ("from engine.tests.test_v6_e9_v2_independent_gate8_seal07 import death_driver; "
                  "import sys; death_driver(*sys.argv[1:])")
    result = subprocess.run([sys.executable, "-c", expression, str(study.log.root),
                             str(configuration), kind, when], capture_output=True, timeout=30,
                            check=False, cwd=fixture.ROOT)
    assert result.returncode == 79, result.stderr.decode(errors="replace")
    return result


def synthetic_incident_clearance(study, tmp_path, child, sequence):
    """Explicit test-only manual prerequisite; no operational clearance is granted."""
    lock = study.log.root / "exclusive.lock"
    assert child.returncode == 79  # bounded child has exited; this test owns its unique root
    if not lock.exists():
        return
    raw, metadata = lock.read_bytes(), lock.stat()
    evidence = tmp_path / f"synthetic-manual-clearance-{sequence}.json"
    evidence.write_bytes(fixture.encode({"synthetic_only": True, "dead_child": True,
        "sole_root_owner": "this isolated test", "operator": "independent-test-author",
        "authorization": "Scope03 synthetic prerequisite only", "action": "unlink exact lock",
        "sha256_raw": digest(raw), "bytes_hex": raw.hex(), "mtime_ns": metadata.st_mtime_ns,
        "size": metadata.st_size}))
    assert digest(lock.read_bytes()) == digest(raw)
    lock.unlink()  # deliberate synthetic incident action after proof/evidence, never producer repair


@pytest.mark.parametrize("requirement,kind,when", [
    ("C01/B0", "allocation", "after-allocation"),
    ("C02/B1", "intent", "partial-candidate"), ("C03/B2", "intent", "after-install"),
    ("C04/B3", "verification", "during-verification"),
    ("C05/B4", "result", "partial-candidate"), ("C06/B5", "result", "after-install"),
    ("C07/B6", "retained-W", "partial-candidate"), ("C08/B7", "retained-W", "after-install"),
    ("C09/B8", "W", "partial-candidate"), ("C10/B9", "W", "after-install"),
    ("C11/B10", "outcome", "partial-candidate"), ("C12/B11", "outcome", "after-install"),
    ("C13/B12", "recheck", "during-recheck"),
    ("C14/B13", "returned", "after-return")])
def test_actual_process_death_preserves_outputs_and_requires_explicit_lock_prerequisite(
        requirement, kind, when, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    scientific = scientific_bytes(study)
    child = dead_child(study, tmp_path, kind, when, 1)
    folder = fixture.w_folder(study)
    old = prior.tree(study.log.root)
    canonical = [folder / "W.json", *folder.glob("attempt-*.intent.json"),
                 *folder.glob("attempt-*.outcome.json")]
    for path in canonical:
        if path.exists():
            raw = path.read_bytes()
            assert raw == fixture.encode(json.loads(raw)), requirement
    stale = study.log.root / "exclusive.lock"
    if stale.exists():
        raw_lock = stale.read_bytes()
        with pytest.raises(records.IntegrityError, match="busy|interrupted"):
            pv.produce_private_verification(study.log, verifier=fixture.VERIFIER,
                expected_tip=study.issue_S["digest"], operation_id=fixture.PV_OP)
        assert stale.read_bytes() == raw_lock
    synthetic_incident_clearance(study, tmp_path, child, 1)
    calls = fixture.verifier_spy(monkeypatch)
    if "PASS" in fixture.labels(study):
        with pytest.raises(records.IntegrityError):
            fixture.produce(study)
        assert calls == [] and fixture.labels(study).count("PASS") == 1
    else:
        fixture.produce(study)
        assert len(calls) == 1 and fixture.labels(study).count("PASS") == 1
        assert "FAILED_VERIFICATION" not in fixture.labels(study)
    after = prior.tree(study.log.root)
    assert all(after[name] == raw for name, raw in old.items() if name != "exclusive.lock")
    assert scientific_bytes(study) == scientific


def test_repeated_recovery_process_death_keeps_same_W_then_one_PASS(bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    first = dead_child(study, tmp_path, "W", "after-install", 1)
    synthetic_incident_clearance(study, tmp_path, first, 1)
    W = (fixture.w_folder(study) / "W.json").read_bytes()
    second = dead_child(study, tmp_path, "outcome", "partial-candidate", 2)
    synthetic_incident_clearance(study, tmp_path, second, 2)
    old = prior.tree(study.log.root)
    calls = fixture.verifier_spy(monkeypatch)
    fixture.produce(study)
    assert len(calls) == 1 and fixture.labels(study) == ["PASS"]
    assert (fixture.w_folder(study) / "W.json").read_bytes() == W
    assert all(prior.tree(study.log.root)[name] == raw for name, raw in old.items())


@pytest.mark.skipif(os.name != "posix", reason="native POSIX objects require a suitable host")
@pytest.mark.parametrize("kind", ("fifo", "socket", "device"))
def test_native_nonregular_objects_are_refused_in_bounded_subprocess(kind, tmp_path):
    import socket

    target = tmp_path / kind
    handle = None
    if kind == "fifo":
        os.mkfifo(target)
    elif kind == "socket":
        handle = socket.socket(socket.AF_UNIX)
        handle.bind(str(target))
    else:
        target = Path("/dev/null")
    expression = ("from pathlib import Path; import sys; "
        "from tools.research.v6.e9.v2.records import regular_bytes, IntegrityError; "
        "\ntry: regular_bytes(Path(sys.argv[1]))\n"
        "except IntegrityError: sys.exit(0)\nelse: sys.exit(1)\n")
    try:
        result = subprocess.run([sys.executable, "-c", expression, str(target)], timeout=10,
                                capture_output=True, check=False, cwd=fixture.ROOT)
        assert result.returncode == 0, result.stderr.decode(errors="replace")
    finally:
        if handle is not None:
            handle.close()


@pytest.mark.parametrize("target_kind", ("event", "active"))
def test_R03_protected_action_is_not_entered_with_unsupported_authority_state(
        target_kind, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    expected_tip = study.log.tip
    target = (fixture.event_files(study)[0] if target_kind == "event" else
              study.log.root / "active.json")
    seen = mode_at(monkeypatch, target, stat.S_IFIFO)
    entered = []
    with pytest.raises(records.IntegrityError):
        study.log.protected("private_verification", expected_tip=expected_tip,
            operation_id=fixture.PV_OP, action=lambda lease: entered.append(lease))
    assert seen["stat"] and not seen["open"] and not entered


@pytest.mark.parametrize("phase", ("entry", "verification"))
def test_R09_catalogue_is_guarded_at_entry_and_complete_verification(
        phase, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    calls = []
    if phase == "entry":
        seen = mode_at(monkeypatch, CATALOGUE, stat.S_IFIFO)
    else:
        verifier = pv.verify_complete_private
        seen = {}

        def checked(**kwargs):
            calls.append(True)
            seen.update(mode_at(monkeypatch, CATALOGUE, stat.S_IFIFO))
            return verifier(**kwargs)

        monkeypatch.setattr(pv, "verify_complete_private", checked)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert bool(calls) == (phase == "verification")
    assert not seen.get("open", 0) and "PASS" not in fixture.labels(study)


def test_exact_recovery_performs_no_generation_salt_registration_or_authority_append(
        bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    scientific = scientific_bytes(study)
    seen = prior.scientific_spy(monkeypatch)
    fixture.produce(study)
    assert seen["calls"] == [] and seen["operations"] == ["private_verification"]
    assert scientific_bytes(study) == scientific and fixture.labels(study) == ["PASS"]


@pytest.mark.parametrize("fault", ("write", "flush", "fsync", "readback"))
def test_candidate_infrastructure_faults_never_publish_partial_canonical(fault, tmp_path, monkeypatch):
    path, candidate = tmp_path / "canonical.json", tmp_path / "candidate.json"
    raw = fixture.encode({"canonical": "complete"})
    original_open, original_fsync = Path.open, os.fsync
    injected = OSError(errno.EIO, "synthetic candidate storage failure")

    class Broken:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, material):
            if fault == "write":
                self.stream.write(material[:len(material) // 2])
                raise injected
            return self.stream.write(material)

        def flush(self):
            if fault == "flush":
                raise injected
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    def opened(file, mode="r", *args, **kwargs):
        stream = original_open(file, mode, *args, **kwargs)
        return Broken(stream) if file == candidate and mode == "xb" else stream

    def fsync(fd):
        if fault == "fsync" and stat.S_ISREG(os.fstat(fd).st_mode):
            raise injected
        return original_fsync(fd)

    monkeypatch.setattr(Path, "open", opened)
    monkeypatch.setattr(os, "fsync", fsync)
    if fault == "readback":
        original_read = records.regular_bytes

        def read(file):
            value = original_read(file)
            return value + b"wrong" if file == candidate else value

        monkeypatch.setattr(records, "regular_bytes", read)
    with pytest.raises((OSError, records.IntegrityError)):
        records.publish_once(path, raw, candidate, writer=auth.durable_bytes)
    assert not path.exists() and candidate.exists()


def test_C01_B0_allocated_attempt_without_intent_is_interrupted_and_never_reused(
        bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    original_mkdir, fired = Path.mkdir, []

    def allocated(path, *args, **kwargs):
        result = original_mkdir(path, *args, **kwargs)
        if path.name == "attempt-0001.staging" and not fired:
            fired.append(path)
            raise Stop()
        return result

    monkeypatch.setattr(Path, "mkdir", allocated)
    with pytest.raises(Stop):
        fixture.produce(study)
    assert fired and fired[0].is_dir()
    calls = fixture.verifier_spy(monkeypatch)
    fixture.produce(study)
    assert len(calls) == 1 and fired[0].is_dir()
    assert fixture.labels(study) == ["PASS"]
    assert fixture.outcomes(study)[0]["attempt"] == 2
    assert fixture.outcomes(study)[0]["interrupted_prior_attempts"] == [1]


def test_B0_unexplained_allocation_gap_refuses_and_preserves_evidence(bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    folder = fixture.w_folder(study)
    gap = pv._staging(folder) / "attempt-0002.staging"
    gap.mkdir(parents=True)
    calls = fixture.verifier_spy(monkeypatch)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert calls == [] and gap.is_dir() and not fixture.labels(study)


def test_R04_retained_nonregular_object_cannot_escape_through_resolver_fallback(
        bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    target, call = mapped_read(study, "S7-R04", tmp_path)
    original = study.log.resolver
    invoked = []

    def resolver(ref):
        invoked.append(ref)
        exact_S = study.records["S"]
        return exact_S if ref == records.record_ref(exact_S) else original(ref)

    study.log.resolver = resolver
    with monkeypatch.context() as patch:
        seen = mode_at(patch, target, stat.S_IFIFO)
        with pytest.raises(records.IntegrityError):
            call()
        assert seen["stat"] and not seen["open"] and not invoked
    ref = records.record_ref(study.records["S"])
    target.unlink()  # ordinary absent retained record still permits the audited callback
    assert records.record_ref(study.log.resolve(ref)) == ref and invoked == [ref]
    study.log.resolver = lambda _: study.records["G"]
    with pytest.raises(records.IntegrityError):
        study.log.resolve(ref)


@pytest.mark.parametrize("role", ("intent", "W", "retained-W", "result"))
def test_R18_recovery_consumed_paths_reject_nonregular_before_open(
        role, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    interrupt_complete_W(monkeypatch, study)
    W = fixture.read_W(study)
    if role == "intent":
        target = fixture.w_folder(study) / prior.INTENT
    elif role == "W":
        target = fixture.w_folder(study) / "W.json"
    elif role == "retained-W":
        target = study.log.root / "evidence-records" / (W["digest"] + ".json")
    else:
        ref = next(ref for ref in W["body"]["evidence"] if ref["evidence_id"] == prior.RESULT_ID)
        target = ref_path(study, ref)
    seen = mode_at(monkeypatch, target, stat.S_IFIFO)
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert seen["stat"] and not seen["open"] and "PASS" not in fixture.labels(study)


def test_directory_metadata_limit_is_explicit_on_Windows(tmp_path):
    if os.name == "nt":
        assert records.flush_directory(tmp_path) is False
    else:
        assert records.flush_directory(tmp_path) is True


@pytest.mark.parametrize("case,expected", [("salt_missing", "UNAVAILABLE"),
                                           ("held", "REFUSED_PRECONDITION"),
                                           ("tail", "FAILED_VERIFICATION")])
@pytest.mark.parametrize("boundary", ("partial-candidate", "after-install"), ids=("C15-E1", "C16-E2"))
def test_actual_nonPASS_process_death_keeps_classification_and_terminal_rule(
        case, expected, boundary, bases, tmp_path):
    study = clone(bases, tmp_path)
    if case == "salt_missing":
        ref_path(study, study.S["body"]["salt"]).unlink()
    elif case == "held":
        fixture.hold(study, "seal07-dead-diagnostic")
    else:
        prior.tail_event(study, "recorder_consume")
    child = dead_child(study, tmp_path, "outcome", boundary, 1)
    assert child.returncode == 79 and prior.lock_free(study)
    old = prior.tree(study.log.root)
    assert fixture.labels(study) == ([expected] if boundary == "after-install" else [])
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    if expected == "FAILED_VERIFICATION" and boundary == "after-install":
        assert fixture.labels(study) == [expected, "REFUSED_PRECONDITION"]
    else:
        assert fixture.labels(study)[-1] == expected
    assert "PASS" not in fixture.labels(study)
    after = prior.tree(study.log.root)
    assert all(after[name] == raw for name, raw in old.items())


# ==== S7-DEV-F1 addendum: typed registry unavailability under the frozen F1 precedence ======
# Appended 2026-10-07 by a fresh independent test-author context, separate from the implementer
# and from the earlier author of this module. Governing texts only: the lead disposition
# v2_seal07_lead_disposition_b1_f1_01 ("Ruling") sections 3 and 4, v2_gate8_scope_02
# body.repairs.F1 (order and classification), the v2_gate8_scope_03 read_map row for
# authority.registered_producers (S7-R08) and S7_DEV_F1 of v2_seal07_continuation_verification_01.
# The implementer's Seal-07 module and its F1 cases were not read, and no test was run while
# writing this. Implementation sources were read for paths and interfaces only. Comments marked
# "Own derivation" go beyond the Ruling's explicit text.
#
# Each trigger makes one read inside AuthorityLog.registered_producers fail through the typed
# DurableUnavailable path (private_verification's Unavailable), never as a bare OSError:
#   other-G-first/-last  a real directory as another G's registry entry, sorted before or after
#                        this G's entry. Only the registry scan reads producer-roots/*.json, so
#                        the object stays in place until disarmed.
#   other-G-unreadable   a regular other-G entry whose open fails with an OSError, which
#                        regular_bytes reports as the typed unavailability (Seal 06 raised a bare
#                        OSError for this read).
#   G-record             a real directory at evidence-records/<G digest>.json.
#   event                a real directory in place of one authority event file.
# The protected entry check (_state/_check, S7-R03/S7-R04) also reads the G record and the event
# files. Its own unchanged classification would end the attempt before the producer boundary,
# and the Ruling concerns those reads "while registered_producers reads" them. Those two objects
# therefore exist only while registered_producers runs, and the exact prior bytes are restored.

F1_TRIGGERS = ("other-G-first", "other-G-last", "other-G-unreadable", "G-record", "event")


def f1_registry_unavailable(study, trigger, tmp_path, monkeypatch):
    """Arm one typed registry-scan unavailability; return (errors escaping the scan, disarm)."""
    root, G = study.log.root, study.log.bindings["G"]["digest"]
    original = auth.AuthorityLog.registered_producers
    escaped, armed = [], [True]
    static = target = blocked = None
    if trigger.startswith("other-G-"):
        other = ("0" if trigger == "other-G-first" else "f") * 64
        assert other != G and (other < G) == (trigger == "other-G-first")
        static = root / "producer-roots" / (other + ".json")
        if trigger == "other-G-unreadable":
            static.write_bytes(b"{}\n")
            blocked = prior.block_reads(monkeypatch, static)
        else:
            static.mkdir()
    elif trigger == "G-record":
        target = root / "evidence-records" / (G + ".json")
    else:
        assert trigger == "event"
        target = fixture.event_files(study)[0]

    def scan(log):
        held, installed = None, bool(armed) and target is not None
        if installed:
            if target.exists():
                held = tmp_path / ("f1-scan-held-" + target.name)
                os.replace(target, held)
            target.mkdir()
        try:
            return original(log)
        except BaseException as exc:
            escaped.append(exc)
            raise
        finally:
            if installed:
                target.rmdir()
                if held is not None:
                    os.replace(held, target)

    def disarm():
        armed.clear()
        if blocked is not None:
            blocked.clear()
        if static is not None and static.is_dir():
            static.rmdir()
        elif static is not None:
            static.unlink()

    monkeypatch.setattr(auth.AuthorityLog, "registered_producers", scan)
    return escaped, disarm


def assert_scan_typed_unavailable(escaped, *, required=True):
    """Ruling 4 precondition: the registry read failed as the typed Unavailable, not OSError."""
    assert escaped or not required, "the registry scan was not reached or stayed available"
    assert all(isinstance(exc, records.DurableUnavailable) and not isinstance(exc, OSError)
               for exc in escaped), [type(exc).__name__ for exc in escaped]


@pytest.mark.parametrize("form", ("substituted", "corrupt", "reencoded"))
@pytest.mark.parametrize("trigger", F1_TRIGGERS)
def test_S7_DEV_F1_typed_registry_unavailability_never_masks_present_marker_mismatch(
        trigger, form, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    marker = prior.durable(study, "marker")
    expected = marker.read_bytes()
    assert expected == study.log.read_artifact(prior.bound(study, "marker"))
    prior.replace_file(marker, prior.wrong_bytes(study, "marker", form, tmp_path))
    before = prior.tree(study.log.root)
    escaped, disarm = f1_registry_unavailable(study, trigger, tmp_path, monkeypatch)
    with pytest.raises(records.IntegrityError) as raised:
        fixture.produce(study)
    # Ruling 3 first bullet and Ruling 4; Scope02 F1 order item "3.": a present marker with wrong
    # bytes, hash or identity is FAILED_VERIFICATION even though the registry is unavailable.
    assert fixture.labels(study) == ["FAILED_VERIFICATION"]
    # Own derivation (case validity): Ruling 4 requires the registry read to be unavailable
    # through the typed path in this attempt, and F1 order item "2." compares each durable
    # artifact. Without this check the case could pass without the combined condition.
    assert_scan_typed_unavailable(escaped)
    # Own derivation: the error the caller receives is not a typed unavailability.
    assert not isinstance(raised.value, records.DurableUnavailable)
    disarm()
    # Scope02 F1 recovery_constraint: the producer writes neither the marker nor the registry.
    # Every earlier byte, including the wrong marker and any restored scan target, is unchanged.
    after = prior.tree(study.log.root)
    assert all(after.get(name) == raw for name, raw in before.items())
    assert fixture.written_W(study) == []  # Own derivation, as in the existing F1 checks
    prior.assert_attempts_private_free(study)  # Scope02 F1 unchanged: value-free reasons
    prior.replace_file(marker, expected)
    # Scope02 F1 classification: after FAILED_VERIFICATION every later attempt for S is refused.
    with pytest.raises(records.IntegrityError):
        fixture.produce(study)
    assert fixture.labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


@pytest.mark.parametrize("marker_state", ("present", "missing"))
@pytest.mark.parametrize("trigger", F1_TRIGGERS)
def test_S7_DEV_F1_typed_registry_unavailability_without_marker_mismatch_is_UNAVAILABLE(
        trigger, marker_state, bases, tmp_path, monkeypatch):
    study = clone(bases, tmp_path)
    marker = prior.durable(study, "marker")
    expected = marker.read_bytes()
    assert expected == study.log.read_artifact(prior.bound(study, "marker"))
    if marker_state == "missing":  # Own addition: Ruling 3 third bullet beside the registry case
        marker.unlink()
    before = prior.tree(study.log.root)
    escaped, disarm = f1_registry_unavailable(study, trigger, tmp_path, monkeypatch)
    with pytest.raises(records.IntegrityError) as raised:
        fixture.produce(study)
    # Ruling 3 second ("present") and third ("missing") bullets and Ruling 4; Scope02 F1 order
    # item "4.": registry unavailability with no positive mismatch evidence is UNAVAILABLE.
    assert fixture.labels(study) == ["UNAVAILABLE"]
    # Ruling 4 requires the typed registry unavailability for the present marker. Own
    # derivation: with both artifacts unavailable, either read order satisfies F1 item "4.", so
    # the scan need not be reached; any failure it does report must still be typed.
    assert_scan_typed_unavailable(escaped, required=marker_state == "present")
    # Own derivation: the caller receives the typed unavailability that UNAVAILABLE records.
    assert isinstance(raised.value, records.DurableUnavailable)
    assert not isinstance(raised.value, OSError)
    disarm()
    # Scope02 F1 recovery_constraint: nothing written or replaced, and no marker created.
    after = prior.tree(study.log.root)
    assert all(after.get(name) == raw for name, raw in before.items())
    assert marker.exists() == (marker_state == "present")
    assert fixture.written_W(study) == []  # Own derivation, as in the existing F1 checks
    prior.assert_attempts_private_free(study)  # Scope02 F1 unchanged: value-free reasons
    # Own derivation from the existing UNAVAILABLE rule (F1 classification and
    # recovery_constraint, as the independent Seal-06 F1 checks apply it): it is not terminal.
    # Once the condition clears and only required evidence is restored exactly, a new attempt
    # against the same S proceeds.
    if marker_state == "missing":
        marker.write_bytes(expected)
    reference = fixture.produce(study)
    assert fixture.labels(study) == ["UNAVAILABLE", "PASS"]
    assert records.record_ref(fixture.read_W(study)) == reference
