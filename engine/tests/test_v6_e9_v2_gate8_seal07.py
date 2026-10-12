"""Scope03 S7-R01..R18 / S7-C01..C16 implementer synthetic qualification.

REAL is only a frozen input label in hand-built temporary fixtures. No draws,
salt creation, native match or operational publication is authorized here.
Windows directory-flush and adversarial check/open limits are explicit.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.tests._e9_v2_synthetic_records import inventory_status
from engine.tests.test_v6_e9_v2_gate8_producer import INTEGRITY, LEAD, OP, VERIFIER, built
from engine.tests.test_v6_e9_v2_gate8_seal06 import (
    labels,
    marker_path,
    no_generation,
    substitute,
    verifier_calls,
)
from tools.research.v6.e9.v2 import authority as au
from tools.research.v6.e9.v2 import inventory
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2 import records as rec
from tools.research.v6.e9.v2.inventory import artifact


@pytest.mark.parametrize("mode", [stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR,
                                 stat.S_IFBLK, stat.S_IFDIR, 0])
def test_s7_nonregular_precheck_never_opens(tmp_path, monkeypatch, mode):
    """F1: unsupported objects are UNAVAILABLE before any potentially blocking open."""
    path = tmp_path / "durable"
    monkeypatch.setattr(Path, "stat", lambda self, **kw: SimpleNamespace(st_mode=mode))
    monkeypatch.setattr(Path, "open", lambda *a, **kw: pytest.fail("unsupported object opened"))
    with pytest.raises(pv.Unavailable, match="not a regular file"):
        rec.regular_bytes(path)


def test_s7_regular_missing_unreadable_and_opened_identity(tmp_path, monkeypatch):
    path = tmp_path / "regular"
    with pytest.raises(pv.Unavailable):
        rec.regular_bytes(path)
    path.write_bytes(b"complete")
    assert rec.regular_bytes(path) == b"complete"
    real = Path.open
    monkeypatch.setattr(Path, "open", lambda *a, **k: (_ for _ in ()).throw(PermissionError()))
    with pytest.raises(pv.Unavailable):
        rec.regular_bytes(path)
    monkeypatch.setattr(Path, "open", real)
    original = os.fstat

    def changed(fd):
        value = original(fd)
        return SimpleNamespace(st_mode=value.st_mode, st_dev=value.st_dev, st_ino=value.st_ino + 1)
    monkeypatch.setattr(os, "fstat", changed)
    with pytest.raises(rec.IntegrityError, match="identity changed"):
        rec.regular_bytes(path)
    monkeypatch.setattr(os, "fstat", lambda fd: SimpleNamespace(st_mode=stat.S_IFDIR))
    with pytest.raises(pv.Unavailable, match="opened durable object"):
        rec.regular_bytes(path)


def test_s7_symlink_to_regular_target_and_read_observer(tmp_path, monkeypatch):
    target, link = tmp_path / "target", tmp_path / "link"
    target.write_bytes(b"expected")
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("host does not authorize symlink creation")
    opened, real = [], Path.open

    def observe(path, *a, **kw):
        opened.append(path)
        return real(path, *a, **kw)
    monkeypatch.setattr(Path, "open", observe)
    assert rec.regular_bytes(link) == b"expected" and opened == [link]


@pytest.mark.parametrize("where", ["event", "active", "retained", "registry", "marker",
                                  "payload", "salt", "audit", "K", "outcome"])
def test_s7_operational_durable_objects_are_unavailable_without_read(tmp_path, monkeypatch, where):
    """S7-R03/R04/R08/R13/R14/R15/R16, exercised on the actual protected W path."""
    study = built(tmp_path)
    expected_tip = study.log.tip
    if where == "event":
        path = min(study.log.root.glob("event-*.json"))
    elif where == "active":
        path = study.log.root / "active.json"
    elif where == "retained":
        study.log.retain_record(study.S)
        path = study.log.root / "evidence-records" / (study.S["digest"] + ".json")
    elif where in ("registry", "marker"):
        folder = "producer-roots" if where == "registry" else "first-raw"
        path = study.log.root / folder / (study.log.bindings["G"]["digest"] + ".json")
    elif where == "outcome":
        study.folder.mkdir(parents=True, exist_ok=True)
        path = study.folder / "attempt-9999.outcome.json"
        path.write_bytes(b"unusable")
    else:
        ref = study.S["body"][where] if where != "K" else study.records["O"]["body"]["K"]
        path = study.log.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")
    retained = path.read_bytes()
    path.unlink()
    path.mkdir()
    opened, real = [], Path.open

    def observe(item, *a, **kw):
        if item == path:
            opened.append(item)
            pytest.fail("unsupported durable object opened")
        return real(item, *a, **kw)
    monkeypatch.setattr(Path, "open", observe)
    no_generation(monkeypatch)
    with pytest.raises(pv.Unavailable):
        study.produce(expected_tip=expected_tip)
    assert opened == []
    if where != "outcome":
        assert labels(study) == (["REFUSED_PRECONDITION"] if where in ("event", "active", "retained")
                                 else ["UNAVAILABLE"])
    monkeypatch.undo()
    path.rmdir()
    path.write_bytes(retained)


@pytest.mark.parametrize("fault", ["candidate-write", "readback", "link", "collision"])
def test_s7_publication_has_no_partial_canonical_or_overwrite(tmp_path, monkeypatch, fault):
    """S7-C01..C04/C15: failure preserves all evidence and never uses overwrite fallback."""
    destination, candidate = tmp_path / "canonical", tmp_path / "stage" / "candidate"
    raw = b'{"complete":true}\n'
    original_link = os.link
    if fault == "candidate-write":
        def writer(path, intended):
            path.write_bytes(intended[:4])
            raise OSError("stopped writer")
    elif fault == "readback":
        def writer(path, intended):
            au.durable_bytes(path, b"wrong")
    else:
        writer = au.durable_bytes
    if fault == "link":
        monkeypatch.setattr(os, "link", lambda *a, **k: (_ for _ in ()).throw(OSError("unsupported root")))
    elif fault == "collision":
        def race(source, target):
            Path(target).write_bytes(b"other complete record")
            return original_link(source, target)
        monkeypatch.setattr(os, "link", race)
    with pytest.raises((OSError, rec.IntegrityError)):
        rec.publish_once(destination, raw, candidate, writer=writer)
    if fault == "collision":
        assert destination.read_bytes() == b"other complete record"
    else:
        assert not destination.exists()
    assert candidate.exists()


def test_s7_publication_exact_readback_flush_and_reuse(tmp_path, monkeypatch):
    canonical, candidate = tmp_path / "new" / "canonical", tmp_path / "stage" / "candidate"
    seen, link = [], os.link
    real_flush = rec.flush_directory

    def install(source, target):
        assert rec.regular_bytes(Path(source)) == b"canonical"
        seen.append("install")
        return link(source, target)
    monkeypatch.setattr(os, "link", install)
    monkeypatch.setattr(rec, "flush_directory", lambda p: seen.append(("directory", p)) or real_flush(p))
    def writer(path, raw):
        au.durable_bytes(path, raw)
        seen.append("candidate-fsynced")
    rec.publish_once(canonical, b"canonical", candidate, writer=writer)
    assert canonical.read_bytes() == candidate.read_bytes() == b"canonical"
    assert seen.count("install") == 1
    flushed = seen.index(("directory", candidate.parent), seen.index("candidate-fsynced"))
    assert seen.index("candidate-fsynced") < flushed < seen.index("install")
    rec.publish_once(canonical, b"canonical", tmp_path / "unused", writer=lambda *a: pytest.fail("rewrite"))
    assert seen.count("install") == 1
    if os.name == "nt":
        assert rec.flush_directory(tmp_path) is False  # recorded platform limitation


def _logical(path, study):
    if path.parent.name == "evidence-raw":
        return "result"
    if path.parent.name == "evidence-records":
        return "retained-W"
    if path.name.endswith(".outcome.json"):
        return "PASS"
    return path.name


@pytest.mark.parametrize("boundary", ["intent", "recovery", "result", "retained-W", "W.json", "PASS"])
@pytest.mark.parametrize("side", ["before", "after"])
def test_s7_every_durable_boundary_recovers_same_material(tmp_path, monkeypatch, boundary, side):
    """B1/B2/B4..B11: before/after publication, full reverify, no rewriting scientific bytes."""
    study = built(tmp_path)
    no_generation(monkeypatch)
    initial = dict(study.log.bindings)
    snapshot = {p: p.read_bytes() for p in (study.log.root / "evidence-raw").glob("*.bin")}
    real = pv._publish

    def stop(folder, ordinal, path, raw):
        label = _logical(path, study)
        target = "attempt-0001.intent.json" if boundary == "intent" else "recovery.json" if boundary == "recovery" else boundary
        if label == target and side == "before":
            raise OSError("synthetic interruption")
        real(folder, ordinal, path, raw)
        if label == target and side == "after":
            raise OSError("synthetic interruption")
    monkeypatch.setattr(pv, "_publish", stop)
    with pytest.raises(OSError, match="synthetic interruption"):
        study.produce()
    assert not (study.log.root / "exclusive.lock").exists()  # unwind, not death evidence
    prior = {p: p.read_bytes() for base in (study.folder, pv._staging(study.folder))
             for p in base.rglob("*") if p.is_file()}
    monkeypatch.setattr(pv, "_publish", real)
    calls = verifier_calls(monkeypatch)
    if boundary == "PASS" and side == "after":
        with pytest.raises(pv.Refused):
            study.produce()
        assert calls == []
    else:
        study.produce()
        assert calls == [True]
        assert study.outcomes()[-1]["interrupted_prior_attempts"] == [1]
    assert labels(study).count("PASS") == 1 and "FAILED_VERIFICATION" not in labels(study)
    assert study.log.bindings == initial
    assert all(p.read_bytes() == raw for p, raw in snapshot.items())
    assert all(p.read_bytes() == raw for p, raw in prior.items())


@pytest.mark.parametrize("event", ["HOLD", "ISSUE", "REVOKE"])
def test_s7_intervening_authority_event_blocks_without_scientific_failure(tmp_path, monkeypatch, event):
    study = built(tmp_path)
    real = pv._finish
    monkeypatch.setattr(pv, "_finish", lambda *a, **k: (_ for _ in ()).throw(OSError("before PASS")))
    with pytest.raises(OSError):
        study.produce()
    raw = (study.folder / "W.json").read_bytes()
    monkeypatch.setattr(pv, "_finish", real)
    study.log.append(event, INTEGRITY if event == "HOLD" else LEAD,
                     expected_tip=study.log.tip, operation_id=OP,
                     evidence=[artifact(b"synthetic event", "S7-EVENT")])
    calls = verifier_calls(monkeypatch)
    with pytest.raises(rec.IntegrityError):
        study.produce()
    assert calls == [] and labels(study) == ["REFUSED_PRECONDITION"]
    assert (study.folder / "W.json").read_bytes() == raw


def test_s7_allocation_without_intent_is_retained_and_not_reused(tmp_path):
    study = built(tmp_path)
    stage = pv._staging(study.folder) / "attempt-0001.staging"
    stage.mkdir(parents=True)
    torn = stage / "attempt-0001.intent.json.candidate"
    torn.write_bytes(b"torn candidate")
    study.produce()
    assert labels(study) == ["PASS"]
    assert study.outcomes()[0]["attempt"] == 2
    assert study.outcomes()[0]["interrupted_prior_attempts"] == [1]
    assert torn.read_bytes() == b"torn candidate"


def test_s7_recovery_rederivation_and_published_mismatch_refuse(tmp_path, monkeypatch):
    study = built(tmp_path)
    real = pv._finish
    monkeypatch.setattr(pv, "_finish", lambda *a, **k: (_ for _ in ()).throw(OSError("before PASS")))
    with pytest.raises(OSError):
        study.produce()
    path = study.folder / "W.json"
    path.write_bytes(b"unexplained canonical damage")
    monkeypatch.setattr(pv, "_finish", real)
    calls = verifier_calls(monkeypatch)
    with pytest.raises(pv.Refused, match="published result/W mismatch"):
        study.produce()
    assert calls == [True] and labels(study) == []
    assert path.read_bytes() == b"unexplained canonical damage"


def test_s7_stale_lock_never_automatically_cleared(tmp_path):
    study = built(tmp_path)
    lock = study.log.root / "exclusive.lock"
    lock.write_bytes(b"synthetic known-dead owner; separate manual prerequisite")
    # Avoid the fixture's tip getter, which itself takes the same lock.
    expected = json.loads((study.log.root / "active.json").read_bytes())["tip"]
    with pytest.raises(rec.IntegrityError, match="busy or interrupted"):
        pv.produce_private_verification(study.log, verifier=VERIFIER,
                                        expected_tip=expected, operation_id=OP)
    assert lock.read_bytes() == b"synthetic known-dead owner; separate manual prerequisite"
    assert labels(study) == ["REFUSED_PRECONDITION"]


@pytest.mark.parametrize("site", ["catalogue", "status", "limitation", "adopted", "inventory", "template"])
def test_s7_frozen_contract_reads_reject_before_open(monkeypatch, site):
    """S7-R09/R10/R11/R12/R17: frozen files are injected, never modified."""
    contract = rec.BASE / "amended_rule_contract_v2_proposed_02.json"
    target = (rec.BASE / "amended_record_schemas_v2_proposed_02.json" if site == "catalogue"
              else rec.ADOPTED if site == "adopted" else contract)
    value = inventory_status() if site == "status" else None
    original_stat, original_open = Path.stat, Path.open

    def typed(path, *a, **kw):
        return SimpleNamespace(st_mode=stat.S_IFIFO) if path == target else original_stat(path, *a, **kw)

    def opened(path, *a, **kw):
        if path == target:
            pytest.fail("unsupported frozen evidence opened")
        return original_open(path, *a, **kw)
    monkeypatch.setattr(Path, "stat", typed)
    monkeypatch.setattr(Path, "open", opened)
    actions = {
        "catalogue": rec.catalogue,
        "status": lambda: rec._field("inventory_status", value, "InventoryStatus"),
        "limitation": lambda: rec._field("permanent_limitation", "irrelevant", "text"),
        "adopted": lambda: rec.read_record(rec.ADOPTED, "P"),
        "inventory": inventory.frozen_limitations,
        "template": pv._frozen_limitation,
    }
    with pytest.raises(pv.Unavailable):
        actions[site]()


def test_s7_source_callback_is_safe_at_entry_and_recheck(tmp_path, monkeypatch):
    """S7-R01: the real pinned callback is checked twice, without type caching."""
    path = tmp_path / "source.py"
    path.write_bytes(b"source bytes")
    P = rec.record_ref(rec.read_record(rec.ADOPTED, "P"))
    check = au.pinned_source_checker(tmp_path, {"body": {"implementation_sources": {
        "source.py": rec.sha256(path.read_bytes())}}}, {"body": {"qualification_sources": {
        "source.py": rec.sha256(path.read_bytes())}}}, P)
    check()
    path.unlink()
    path.mkdir()
    monkeypatch.setattr(Path, "open", Path.open)  # callback still uses the scoped observation surface
    with pytest.raises(pv.Unavailable):
        check()


@pytest.mark.parametrize("site", ["readback", "record-retention", "artifact-retention", "artifact-read", "log"])
def test_s7_remaining_authority_read_boundaries(tmp_path, monkeypatch, site):
    """S7-R02/R05/R06/R07/R15, real methods and immutable collision/readback paths."""
    study = built(tmp_path)
    if site == "readback":
        path = tmp_path / "new-readback"
        action = lambda: au.durable_bytes(path, b"canonical")
    elif site == "record-retention":
        path = study.log.root / "evidence-records" / (study.S["digest"] + ".json")
        action = lambda: study.log.retain_record(study.S)
    elif site in ("artifact-retention", "artifact-read"):
        ref = study.log.retain_artifact(b"synthetic retained bytes", "S7-RETAINED")
        path = study.log.root / "evidence-raw" / (ref["sha256_raw"] + ".bin")
        action = (lambda: study.log.read_artifact(ref)) if site == "artifact-read" else (
            lambda: study.log.retain_artifact(b"synthetic retained bytes", "S7-RETAINED"))
    else:
        path = min(study.log.root.glob("event-*.json"))
        action = lambda: pv._durable_log(study.log)
    original_stat, original_open = Path.stat, Path.open

    def typed(item, *a, **kw):
        return SimpleNamespace(st_mode=stat.S_IFIFO) if item == path else original_stat(item, *a, **kw)

    def opened(item, mode="r", *a, **kw):
        if item == path and mode == "rb":
            pytest.fail("unsupported object entered read")
        return original_open(item, mode, *a, **kw)
    monkeypatch.setattr(Path, "stat", typed)
    monkeypatch.setattr(Path, "open", opened)
    with pytest.raises(pv.Unavailable):
        action()


# ---- S7-DEV-F1: typed producer-registry unavailability and first-raw marker precedence ----------

F1_REGISTRY_READS = ["other-G entry", "G record", "event file"]


def registry_fault(study, monkeypatch, read):
    """Make one mapped registered_producers read unavailable; returns its raised errors and a restorer."""
    raised, inside, active = [], [], [True]
    G = study.log.bindings["G"]

    def producers():
        inside.append(True)
        try:
            return au.AuthorityLog.registered_producers(study.log)
        except rec.IntegrityError as exc:
            raised.append(exc)
            raise
        finally:
            inside.pop()
    monkeypatch.setattr(study.log, "registered_producers", producers)
    if read == "other-G entry":
        other = study.log.root / "producer-roots" / ("f" * 64 + ".json")
        other.mkdir()  # a native non-regular entry: the typed regular-read refusal, before any open
        return raised, other.rmdir
    if read == "G record":
        real_resolve = study.log.resolve

        def resolve(ref):
            if active and inside and ref == G:
                raise rec.DurableUnavailable("simulated unavailable G record")
            return real_resolve(ref)
        monkeypatch.setattr(study.log, "resolve", resolve)
    else:
        real_read = au.regular_bytes

        def read_event(path):
            if active and inside and path.name.startswith("event-"):
                raise rec.DurableUnavailable("simulated unavailable event file")
            return real_read(path)
        monkeypatch.setattr(au, "regular_bytes", read_event)
    return raised, active.clear


@pytest.mark.parametrize("read", F1_REGISTRY_READS)
def test_s7_f1_unavailable_registry_read_does_not_mask_a_marker_mismatch(tmp_path, monkeypatch, read):
    """Lead disposition S7-DEV-F1: a present marker with other bytes is FAILED_VERIFICATION."""
    study = built(tmp_path)
    marker_path(study).write_bytes(substitute(study, "marker"))
    raised, _ = registry_fault(study, monkeypatch, read)
    no_generation(monkeypatch)
    with pytest.raises(rec.IntegrityError, match="first-raw marker") as failure:
        study.produce()
    assert not isinstance(failure.value, pv.Unavailable)
    assert raised and all(isinstance(exc, au.ProducerRegistryUnavailable) for exc in raised)
    assert all(isinstance(exc, rec.DurableUnavailable) and not isinstance(exc, OSError) for exc in raised)
    assert labels(study) == ["FAILED_VERIFICATION"] and not (study.folder / "W.json").exists()
    with pytest.raises(pv.Refused, match="already failed"):
        study.produce()


@pytest.mark.parametrize("read", F1_REGISTRY_READS)
def test_s7_f1_unavailable_registry_read_with_a_valid_marker_is_unavailable(tmp_path, monkeypatch, read):
    """Lead disposition S7-DEV-F1: without positive mismatch evidence the deferred condition is UNAVAILABLE."""
    study = built(tmp_path)
    marker = marker_path(study).read_bytes()
    raised, restore = registry_fault(study, monkeypatch, read)
    no_generation(monkeypatch)
    with pytest.raises(pv.Unavailable, match="producer registry unavailable"):
        study.produce()
    assert raised and all(isinstance(exc, au.ProducerRegistryUnavailable) for exc in raised)
    assert labels(study) == ["UNAVAILABLE"] and not (study.folder / "W.json").exists()
    assert marker_path(study).read_bytes() == marker
    restore()
    W = study.log.resolve(study.produce())
    assert labels(study) == ["UNAVAILABLE", "PASS"] and W["body"]["decision"] == "PASS"


def test_s7_f1_an_unmapped_unavailable_inside_the_registry_scan_is_not_deferred(tmp_path, monkeypatch):
    """Derived from the S7-DEV-F1 limit: only the mapped registry reads defer; a frozen-catalogue read does not."""
    study = built(tmp_path)
    marker_path(study).write_bytes(substitute(study, "marker"))
    raised, inside = [], []
    schemas = rec.BASE / "amended_record_schemas_v2_proposed_02.json"
    real_read = rec.regular_bytes

    def producers():
        inside.append(True)
        try:
            return au.AuthorityLog.registered_producers(study.log)
        except rec.IntegrityError as exc:
            raised.append(exc)
            raise
        finally:
            inside.pop()

    def read(path):
        if inside and path == schemas:
            raise rec.DurableUnavailable("simulated unavailable frozen catalogue")
        return real_read(path)
    monkeypatch.setattr(study.log, "registered_producers", producers)
    monkeypatch.setattr(rec, "regular_bytes", read)
    no_generation(monkeypatch)
    with pytest.raises(pv.Unavailable, match="simulated unavailable frozen catalogue"):
        study.produce()
    assert raised and not any(isinstance(exc, au.ProducerRegistryUnavailable) for exc in raised)
    assert labels(study) == ["UNAVAILABLE"]


DEATH_CHILD = r'''
import json, os, random, secrets, sys, time
from pathlib import Path
from battle_engine.match_service import NativeMatchService
from battle_engine.process_runtime import ProcessMatchController
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.authority import AuthorityLog
def forbidden(*args, **kwargs):
    raise AssertionError('prohibited entropy or native execution in synthetic child')
os.urandom = random._urandom = forbidden
secrets.token_bytes = secrets.randbits = secrets.randbelow = forbidden
NativeMatchService.run = ProcessMatchController.run = forbidden
state = json.loads(Path(sys.argv[1]).read_bytes())
log = AuthorityLog(Path(state['root']), state['study_id'], state['bindings'],
                   actors=state['actors'], resolver=lambda ref: state['records'][ref['digest']],
                   source_check=lambda: None)
real = pv._publish
def barrier(folder, ordinal, path, raw):
    if sys.argv[2] == 'before-PASS' and path.name.endswith('.outcome.json'):
        Path(sys.argv[3]).write_bytes(b'BEFORE PASS; child guard active')
        time.sleep(120)
    real(folder, ordinal, path, raw)
    if sys.argv[2] == 'after-W' and path.name == 'W.json':
        Path(sys.argv[3]).write_bytes(b'AFTER W; child guard active')
        time.sleep(120)
    if sys.argv[2] == 'after-PASS' and path.name.endswith('.outcome.json'):
        Path(sys.argv[3]).write_bytes(b'AFTER PASS; child guard active')
        time.sleep(120)
pv._publish = barrier
pv.produce_private_verification(log, verifier=state['verifier'], expected_tip=state['tip'],
                                operation_id='synthetic-private-verification')
'''


@pytest.mark.parametrize("point", ["before-PASS", "after-W", "after-PASS"])
def test_s7_real_process_death_retains_lock_and_exact_continuation(tmp_path, monkeypatch, point):
    """Process kill, not exception unwind; synthetic authorized manual-clearance prerequisite."""
    study = built(tmp_path)
    tip = study.log.tip
    state = tmp_path / "synthetic-child-state.json"
    state.write_bytes(pv._raw({"root": str(study.log.root), "study_id": study.log.study_id,
                              "bindings": study.log.bindings, "actors": study.log.actors,
                              "records": study.by_digest, "verifier": VERIFIER, "tip": tip}))
    ready = tmp_path / "synthetic-child-ready"
    command = [sys.executable, "-c", DEATH_CHILD, str(state), point, str(ready)]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)) as process:
        deadline = time.monotonic() + 90
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        observed = ready.exists()
        process.kill()
        stdout, stderr = process.communicate(timeout=10)
        assert observed, (stdout, stderr)
        assert process.returncode != 0
    lock = study.log.root / "exclusive.lock"
    retained_lock = lock.read_bytes()
    metadata = lock.stat()
    assert retained_lock and metadata.st_size == len(retained_lock)
    before = {p: p.read_bytes() for p in study.log.root.rglob("*") if p.is_file()}
    with pytest.raises(rec.IntegrityError, match="busy or interrupted"):
        study.produce(expected_tip=tip)
    assert lock.read_bytes() == retained_lock
    # Owning child proven dead above, no other user of this synthetic root; this is
    # the modeled incident prerequisite, never production automatic lock clearance.
    lock.unlink()
    calls = verifier_calls(monkeypatch)
    if point == "after-PASS":
        with pytest.raises(pv.Refused):
            study.produce(expected_tip=tip)
        assert calls == []
    else:
        study.produce(expected_tip=tip)
        assert calls == [True]
    assert labels(study).count("PASS") == 1 and "FAILED_VERIFICATION" not in labels(study)
    assert all(p.read_bytes() == raw for p, raw in before.items() if p != lock)


NATIVE_POSIX_PROGRAM = r'''
import json, os, socket, subprocess, sys
from pathlib import Path
from tools.research.v6.e9.v2.records import DurableUnavailable, regular_bytes, publish_once, flush_directory
root = Path(sys.argv[1]); root.mkdir(parents=True, exist_ok=False)
fifo = root / 'fifo'; os.mkfifo(fifo)
sock = socket.socket(socket.AF_UNIX); sock.bind(str(root / 'socket'))
(root / 'device').symlink_to('/dev/null')
(root / 'directory').mkdir()
reports = {}
for name in ['fifo', 'socket', 'device', 'directory']:
    code = 'from pathlib import Path; from tools.research.v6.e9.v2.records import regular_bytes, DurableUnavailable; import sys\ntry: regular_bytes(Path(sys.argv[1]))\nexcept DurableUnavailable: print("UNAVAILABLE")\nelse: raise AssertionError("special object accepted")'
    result = subprocess.run([sys.executable, '-c', code, str(root / name)], capture_output=True, timeout=5)
    assert result.returncode == 0 and result.stdout.strip() == b'UNAVAILABLE', (name, result.stderr)
    reports[name] = 'UNAVAILABLE before potentially blocking read'
regular = root / 'regular'; regular.write_bytes(b'exact')
(root / 'regular-link').symlink_to(regular)
assert regular_bytes(root / 'regular-link') == b'exact'
def writer(path, raw):
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
publish_once(root / 'canonical', b'complete', root / 'candidate', writer=writer)
assert regular_bytes(root / 'canonical') == b'complete' and flush_directory(root)
sock.close()
print(json.dumps({'native_special_objects': reports, 'regular_symlink': 'PASS',
                  'hardlink_no_overwrite_publication': 'PASS', 'directory_fsync': 'PASS',
                  'physical_power_loss_claim': False, 'real_entropy_draws': 0}, sort_keys=True))
'''


@pytest.mark.skipif(os.name != "posix", reason="native POSIX special objects require POSIX; separately qualified via WSL")
def test_s7_native_posix_fifo_socket_device_and_publication(tmp_path):
    result = subprocess.run([sys.executable, "-c", NATIVE_POSIX_PROGRAM, str(tmp_path / "native")],
                            capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert len(report["native_special_objects"]) == 4 and report["real_entropy_draws"] == 0
