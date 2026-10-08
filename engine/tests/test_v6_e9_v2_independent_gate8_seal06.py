"""Independent seal-06 qualification: S6-F1 to S6-F4 of v2_gate8_scope_02.json.

Written by the independent test author, a context separate from the implementation author,
from the write-once seal-06 scope record (v6-e9-v2-gate8-scope-0761c4e07487: repairs F1-F4
and qualification.required_coverage), its lead confirmation (the F1 check order, the two
preserved F3 classifications, and A1-A6 including A6 and its limit), disposition 03
(G8-IQ-F1..F4 FIX IN SEAL 06; F5-F9 are record only and are not tested here) and the Gate-8
scope 01 that scope 02 amends. It was not written from the implementer's seal-06 tests or
from the revised producer's decision path. Expected outcomes come from those records. The
on-disk names used to reach the evidence (the S folder, the attempt records, W.json, the
durable registry and first-raw marker, and the GATE8-W-VERIFICATION-RESULT artifact) are the
layout that the scopes and the sealed authority module name.

D4 provenance, recorded here and outside the frozen-shape entropy declaration. Every
REAL-labelled study in this module is a synthetic qualification fixture of the independent
seal-05 producer module (test_v6_e9_v2_independent_gate8_producer): study
"synthetic-e9-v2-only", synthetic actors, hash-derived synthetic uint64 values and a literal
32-byte test constant standing in for the salt, all built by hand inside pytest temporary
roots. REAL appears only as an input declaration with the frozen entropy_declaration shape.
No fixture consumes entropy, calls os.urandom or secrets, invokes salt_creation, writes
salt.bin, runs a native match or a bootstrap analysis, or writes to the repository or to an
operational or private store. Faults are injected only into files under those temporary
roots and into in-process calls. None of this material is operational evidence, and no
real-study path accepts it.

No REAL entropy was consumed. REAL was represented only as an input declaration inside
synthetic qualification fixtures.
"""

from __future__ import annotations

import builtins
import errno
import inspect
import io
import json
import os
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from engine.tests import test_v6_e9_v2_independent_gate8_producer as producer
from tools.research.v6.e9.v2 import private_verification as pv
from tools.research.v6.e9.v2.authority import AuthorityLog
from tools.research.v6.e9.v2.generation import Generator
from tools.research.v6.e9.v2.records import IntegrityError, make_record, record_ref

SCOPE = json.loads((producer.FROZEN / "v2_gate8_scope_02.json").read_bytes())["body"]
ADMISSIBLE_ONLY_IF = SCOPE["repairs"]["F4"]["admissible_only_if"]
RESULT_ID = "GATE8-W-VERIFICATION-RESULT"  # scope 02, F4 A5
RESULT_KIND = "GATE8_PRIVATE_VERIFICATION_RESULT_V1"  # scope 02, F4 A5
REFUSED = ("refused", "refused", "refused")
INTENT, OUTCOME = "attempt-0001.intent.json", "attempt-0001.outcome.json"

LEAD, RECORDER, INTEGRITY = producer.LEAD, producer.RECORDER, producer.INTEGRITY
VERIFIER, SECOND_CHECKER, OP = producer.VERIFIER, producer.SECOND_CHECKER, producer.OP
clone, produce, encode = producer.clone, producer.produce, producer.encode
labels, outcomes, w_folder = producer.labels, producer.outcomes, producer.w_folder
read_W, written_W = producer.read_W, producer.written_W


# ---- Bases ----------------------------------------------------------------------------------

_LOCAL: dict[str, producer.Study] = {}


def _w_produced(root: Path, get: Any) -> producer.Study:
    """An issued study whose W the producer has written, before the lead's ISSUE(+W)."""
    study = clone(get("issued"), root)
    produce(study)
    return study


LOCAL_BUILDERS = {"w-produced": _w_produced}


@pytest.fixture
def bases(tmp_path_factory):
    """The cached base studies of the seal-05 producer module plus this module's own."""
    get = producer.base_getter(tmp_path_factory)

    def base(name: str) -> producer.Study:
        if name not in LOCAL_BUILDERS:
            return get(name)
        if name not in _LOCAL:
            _LOCAL[name] = LOCAL_BUILDERS[name](tmp_path_factory.mktemp(name), get)
        return _LOCAL[name]
    return base


# ---- Durable producer registry and first-raw marker (F1) ---------------------------------

DURABLE = {"registry": ("producer-roots", "PRODUCER-ROOT-"), "marker": ("first-raw", "FIRST-RAW-")}


def durable(study: producer.Study, artifact: str) -> Path:
    """<authority root>/producer-roots/<G digest>.json or <authority root>/first-raw/<G>.json."""
    return study.log.root / DURABLE[artifact][0] / (study.log.bindings["G"]["digest"] + ".json")


def bound(study: producer.Study, artifact: str) -> dict:
    """The expected identity: the one boundary-bound artifact of that kind (scope 02 F1)."""
    (ref,) = [ref for ref in study.boundary["body"]["evidence"]
              if ref["evidence_id"].startswith(DURABLE[artifact][1])]
    return ref


def replace_file(path: Path, raw: bytes) -> None:
    if path.is_dir():
        path.rmdir()
    path.unlink(missing_ok=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def wrong_bytes(study: producer.Study, artifact: str, form: str, tmp_path: Path) -> bytes:
    """Present bytes that are not the expected identity: substituted, corrupt or re-encoded."""
    expected = study.log.read_artifact(bound(study, artifact))
    item = json.loads(expected)
    if form == "corrupt":
        wrong = expected[: len(expected) // 2]
    elif form == "reencoded":  # the same JSON value in other bytes: an inconsistent restoration
        wrong = json.dumps(item, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    elif artifact == "registry":  # a substituted producer root
        foreign = os.path.normcase(str((tmp_path / "substituted-producer").resolve()))
        wrong = encode({**item, "producer_root": foreign})
    else:  # a marker bound to another producer registry
        other = producer.sha(b"substituted registry")
        wrong = encode({**item, "producer_registry": {**item["producer_registry"],
                                                      "sha256_raw": other}})
    assert wrong != expected
    return wrong


def block_reads(monkeypatch, target: Path) -> set[str]:
    """Make every open of one path fail as an unreadable file; clearing the set restores it."""
    blocked = {os.path.normcase(os.path.abspath(target))}

    def guard(original: Callable) -> Callable:
        def spy(file, *args, **kwargs):
            if (blocked and isinstance(file, (str, bytes, os.PathLike))
                    and os.path.normcase(os.path.abspath(os.fsdecode(file))) in blocked):
                raise PermissionError(errno.EACCES, "Permission denied", os.fsdecode(file))
            return original(file, *args, **kwargs)
        return spy
    for module in (io, builtins, os):
        monkeypatch.setattr(module, "open", guard(module.open))
    return blocked


def make_unavailable(state: str, path: Path, monkeypatch) -> Callable[[], None]:
    """Make one durable artifact missing or unreadable; return its exact restoration."""
    expected = path.read_bytes()
    if state == "missing":
        path.unlink()
        return lambda: path.write_bytes(expected)
    if state == "directory":  # not a regular file
        path.unlink()
        path.mkdir()
        return lambda: replace_file(path, expected)
    assert state == "read_error"  # an OSError on read
    return block_reads(monkeypatch, path).clear


def tree(root: Path) -> dict[str, bytes]:
    """Every regular file under an authority root, by relative path."""
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in sorted(root.rglob("*")) if path.is_file()}


SCIENTIFIC = ((AuthorityLog, ("append", "consume_generation", "register_producer",
                              "mark_first_raw", "renew_before_generation")),
              (Generator, ("__init__", "consume", "draw_one", "complete", "seal_payload",
                           "snapshot", "generation_receipt")))


def scientific_spy(monkeypatch) -> dict[str, list[str]]:
    """S6-F1-09: record every authority append, registration, marking, generation or salt step
    and every protected operation started while the producer runs."""
    seen: dict[str, list[str]] = {"calls": [], "operations": []}

    def spied(name: str, original: Callable) -> Callable:
        def spy(*args, **kwargs):
            seen["calls"].append(name)
            return original(*args, **kwargs)
        return spy
    for owner, names in SCIENTIFIC:
        for name in names:
            monkeypatch.setattr(owner, name, spied(f"{owner.__name__}.{name}",
                                                   getattr(owner, name)))
    protected = AuthorityLog.protected

    def protected_spy(log, operation, **kwargs):
        seen["operations"].append(operation)
        return protected(log, operation, **kwargs)
    monkeypatch.setattr(AuthorityLog, "protected", protected_spy)
    return seen


def assert_attempts_private_free(study: producer.Study) -> None:
    for path in w_folder(study).glob("attempt-*.json"):
        producer.assert_private_free(study, path.read_bytes())


# ---- Authority events and chain shapes (F2) ------------------------------------------------

def tail_event(study: producer.Study, kind: str) -> dict:
    """One later authority event; each passes the sealed authority checks."""
    log = study.log
    if kind == "recorder_consume":  # W-04 forbidden
        return log.append("CONSUME", RECORDER, expected_tip=log.tip,
                          operation_id="synthetic-tail-consumption")
    if kind == "lead_revoke_nothing":  # W-04 forbidden; revokes no authorization
        stop = log.retain_artifact(encode({"kind": "SYNTHETIC_STOP_EVIDENCE",
                                           "label": "revoke-nothing"}),
                                   "SYNTHETIC-STOP-revoke-nothing")
        return log.append("REVOKE", LEAD, expected_tip=log.tip, operation_id=OP, affected=[],
                          evidence=[stop])
    assert kind == "extending_issue"  # a redundant ISSUE keeps every earlier binding
    return log.append("ISSUE", LEAD, expected_tip=log.tip, operation_id=OP)


def durable_events(study: producer.Study) -> list[dict]:
    return [json.loads(path.read_bytes())["body"] for path in producer.event_files(study)]


def continuation(study: producer.Study) -> str:
    """The shape by scope 02's definition: 'completed' when the last CONTINUE or RELEASE binds
    S, 'partial' when continuations exist but the last does not, 'none' without any."""
    binds_S = ["S" in event["binding_tuple"] for event in durable_events(study)
               if event["event_kind"] in ("CONTINUE", "RELEASE")]
    if not binds_S:
        return "none"
    return "completed" if binds_S[-1] else "partial"


SHAPES = {"issued": "none", "partial-release-continue": "partial",
          "generated-continue": "completed", "generated-release": "completed"}


# ---- Durable writes, lock and tip (F3) -----------------------------------------------------

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND
ATTEMPT_RECORD = re.compile(r"attempt-(\d+)\.(intent|outcome)\.json")


class Writes:
    """Observe, and optionally interrupt, durable writes under one study's authority root.

    Scope03 support exception: logical scoped publication is observed at its staged writer;
    atomic installation emits a separate successful-publication hook. Physical candidate
    opens retain their existing negative-read visibility. The lock and tip are captured at
    each logical write, including producer-local W retention. Unrelated opens/replace remain
    observed as before. Candidate fault hooks never write a torn canonical destination."""

    def __init__(self, monkeypatch, study: producer.Study,
                 hook: Callable[[str, Path | None], None] | None = None):
        from tools.research.v6.e9.v2 import authority as authority_io
        from tools.research.v6.e9.v2 import records as record_io

        self.study, self.hook, self.inside = study, hook, False
        self.events: list[tuple[str, str, bool, str | None]] = []
        self.storage: list[tuple[str, str, bool, str | None]] = []
        self.root = os.path.normcase(os.path.abspath(study.log.root))
        for module in (io, builtins):
            monkeypatch.setattr(module, "open", self._open(module.open))
        monkeypatch.setattr(os, "open", self._os_open(os.open))
        monkeypatch.setattr(os, "replace", self._replace(os.replace))
        self.pending: tuple[str, Path] | None = None
        publish, writer, link = pv._publish, pv.durable_bytes, os.link

        def publication(folder, ordinal, path, raw):
            kind = "other"
            if path.name == "W.json":
                kind = "W.json"
            elif match := ATTEMPT_RECORD.fullmatch(path.name):
                kind = f"{match[2]}-{int(match[1])}"
            elif json.loads(raw).get("body", {}).get("record_role") == "W":
                kind = "W-retention"
            previous, self.pending = self.pending, (kind, path)
            try:
                result = publish(folder, ordinal, path, raw)
                if self.hook is not None:
                    self.hook(kind + "-published", path)  # includes completed metadata flush
                return result
            finally:
                self.pending = previous

        def staged(candidate, raw):
            if self.pending is not None:
                kind, target = self.pending
                self._seen(kind, target.name, candidate)
                self.inside = True
                try:
                    return writer(candidate, raw)
                finally:
                    self.inside = False
            return writer(candidate, raw)

        def installed(source, target, *args, **kwargs):
            result = link(source, target, *args, **kwargs)
            storage("installed")
            return result

        def storage(phase):
            if self.pending is not None:
                previous, self.inside = self.inside, True
                try:
                    lock, tip = self._state()
                    self.storage.append((phase, self.pending[0], lock, tip))
                finally:
                    self.inside = previous

        read_regular = record_io.regular_bytes
        fsync, flush_directory = os.fsync, record_io.flush_directory

        def readback(path):
            result = read_regular(path)
            storage("readback")
            return result

        def synced(fd):
            result = fsync(fd)
            storage("fsync")
            return result

        def metadata(path):
            result = flush_directory(path)
            storage("directory-flush-complete")
            return result

        monkeypatch.setattr(pv, "_publish", publication)
        monkeypatch.setattr(pv, "durable_bytes", staged)
        monkeypatch.setattr(os, "link", installed)
        monkeypatch.setattr(os, "fsync", synced)
        monkeypatch.setattr(record_io, "regular_bytes", readback)
        monkeypatch.setattr(authority_io, "regular_bytes", readback)
        monkeypatch.setattr(record_io, "flush_directory", metadata)

    def kinds(self) -> list[str]:
        return [kind for kind, *_ in self.events if kind != "other"]

    def watched(self, kind: str) -> list[tuple[str, str, bool, str | None]]:
        return [event for event in self.events if event[0] == kind]

    def _state(self) -> tuple[bool, str | None]:
        root = self.study.log.root
        active = root / "active.json"
        tip = json.loads(active.read_bytes())["tip"] if active.exists() else None
        return (root / "exclusive.lock").exists(), tip

    def _seen(self, kind: str, name: str, path: Path | None) -> None:
        self.inside = True
        try:
            lock, tip = self._state()
            self.events.append((kind, name, lock, tip))
            if kind != "other" and self.hook is not None:
                self.hook(kind, path)
        finally:
            self.inside = False

    def _path(self, file: Any) -> None:
        if self.inside or self.pending is not None or not isinstance(file, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(file))
        absolute = os.path.normcase(os.path.abspath(path))
        if not absolute.startswith(self.root + os.sep) or path.name == "exclusive.lock":
            return
        kind = "other"
        if path.parent.name == self.study.S["digest"]:
            match = ATTEMPT_RECORD.fullmatch(path.name)
            if path.name == "W.json":
                kind = "W.json"
            elif match:
                kind = f"{match[2]}-{int(match[1])}"
        self._seen(kind, path.name, path)

    def _open(self, original: Callable) -> Callable:
        def spy(file, mode="r", *args, **kwargs):
            if isinstance(mode, str) and any(flag in mode for flag in "wxa+"):
                self._path(file)
            return original(file, mode, *args, **kwargs)
        return spy

    def _os_open(self, original: Callable) -> Callable:
        def spy(path, flags, *args, **kwargs):
            if flags & WRITE_FLAGS:
                self._path(path)
            return original(path, flags, *args, **kwargs)
        return spy

    def _replace(self, original: Callable) -> Callable:
        def spy(source, target, *args, **kwargs):
            self._path(target)
            return original(source, target, *args, **kwargs)
        return spy


def lock_free(study: producer.Study) -> bool:
    return not (study.log.root / "exclusive.lock").exists()


# ---- Operational W admissibility (F4) -------------------------------------------------------

def admissible(study: producer.Study) -> Any:
    """verify_operational_w accepts: it writes nothing and its result exposes no private value."""
    before = tree(study.log.root)
    result = pv.verify_operational_w(study.log)
    assert tree(study.log.root) == before and lock_free(study)
    producer.assert_private_free(study, json.dumps(result, sort_keys=True,
                                                   default=str).encode("utf-8"))
    return result


def outcome_of(study: producer.Study, call: Callable[[], Any]) -> str:
    """'refused' only for an IntegrityError that wrote nothing and names no private value."""
    before = tree(study.log.root)
    try:
        call()
    except IntegrityError as error:
        if tree(study.log.root) != before:
            return "refused after writing"
        if producer.exposed(str(error), **producer.study_forms(study)):
            return "refused exposing a private value"
        return "refused"
    return "accepted"


def consumers(study: producer.Study, body: dict, U: dict | None) -> tuple[str, ...]:
    """The F4 consumers in operational order: W admissibility, the pre-U check (no receipt
    retained on refusal) and dedicated issuance (no attestation, U retention or event)."""
    results = (outcome_of(study, lambda: pv.verify_operational_w(study.log)),
               outcome_of(study, lambda: producer.pre_u(study, body)))
    if U is None:
        return results
    return (*results, outcome_of(study, lambda: producer.issue_U(study, U)))


def receipt_and_U(study: producer.Study) -> tuple[dict, dict, dict]:
    """While W is admissible: the template, a PASS pre-U receipt and a U binding it."""
    body = producer.template_body(study)
    passed = producer.pre_u(study, body)
    assert passed["decision"] == "PASS"
    return body, passed, producer.make_U(study, body, [passed["receipt"]])


def issue_and_publish_U(study: producer.Study, tmp_path: Path) -> None:
    body, _, U = receipt_and_U(study)
    producer.issue_U(study, U)
    assert study.log.bindings["U"] == record_ref(U)
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"
    C = producer.public_C(body, U)
    assert producer.publish(study, C, tmp_path / "C.json") == record_ref(C)
    assert producer.u_consumed(study)


def substitute(value: Any, old: Any, new: Any) -> Any:
    if value == old:
        return new
    if isinstance(value, dict):
        return {key: substitute(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [substitute(item, old, new) for item in value]
    return value


def renamed(record: Any, *pairs: tuple[Any, Any]) -> bytes:
    """The record with every value equal to an old value replaced; at least one must occur."""
    result = record
    for old, new in pairs:
        result = substitute(result, old, new)
    assert result != record, pairs
    return encode(result)


def renumbered(record: dict) -> dict:
    """The same attempt record as attempt 2, in the same number form."""
    if "attempt" not in record:
        return dict(record)
    number = record["attempt"]
    return {**record, "attempt": 2 if isinstance(number, int) else str(number)[:-1] + "2"}


def folder_files(study: producer.Study) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(w_folder(study).iterdir())
            if path.is_file()}


def restore_folder(study: producer.Study, files: dict[str, bytes]) -> None:
    folder = w_folder(study)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    for name, raw in files.items():
        (folder / name).write_bytes(raw)


# ==== S6-F1: durable producer registry and first-raw marker ===================================

@pytest.mark.parametrize("artifact", ["registry", "marker"])
@pytest.mark.parametrize("state", ["missing", "directory", "read_error"])
def test_s6_f1_01_to_04_and_09_unavailable_durable_artifact_recovers_by_exact_restoration(
        state, artifact, bases, tmp_path, monkeypatch, request):
    study = clone(bases("issued"), tmp_path)
    path = durable(study, artifact)
    assert path.read_bytes() == study.log.read_artifact(bound(study, artifact))
    before, bindings, tip = tree(study.log.root), dict(study.log.bindings), study.log.tip
    spied = scientific_spy(monkeypatch)
    entropy = producer.entropy_spy(monkeypatch, request)
    restore = make_unavailable(state, path, monkeypatch)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE"] and written_W(study) == []
    assert_attempts_private_free(study)
    # Recovery replaces nothing: the producer did not write the artifact itself.
    if state == "missing":
        assert not path.exists()
    elif state == "directory":
        assert path.is_dir()
    restore()  # only the already-required evidence, byte-identical
    reference = produce(study)  # a new attempt against the same S
    assert labels(study) == ["UNAVAILABLE", "PASS"]
    W = read_W(study)
    assert record_ref(W) == reference
    # S6-F1-09: the same S, G, boundary, payload, salt, audit and K; nothing replaced.
    assert study.log.bindings == bindings and study.log.tip == tip
    assert W["body"]["dependencies"]["S"] == record_ref(study.S)
    assert W["body"]["dependencies"]["G"] == bindings["G"]
    assert (W["body"]["payload"], W["body"]["salt"]) == (study.S["body"]["payload"],
                                                         study.S["body"]["salt"])
    assert W["body"]["active_authority_tip"] == tip
    after = tree(study.log.root)
    assert {name: after.get(name) for name in before} == before
    added = set(after) - set(before)
    assert not [name for name in added
                if name.startswith(("producer-roots/", "first-raw/", "event-", "active"))]
    assert spied["calls"] == [] and set(spied["operations"]) == {"private_verification"}
    assert entropy == []


@pytest.mark.parametrize("artifact", ["registry", "marker"])
@pytest.mark.parametrize("form", ["substituted", "corrupt"])
def test_s6_f1_05_06_present_durable_artifact_with_wrong_bytes_fails_verification(
        form, artifact, bases, tmp_path):
    study = clone(bases("issued"), tmp_path)
    path = durable(study, artifact)
    expected = path.read_bytes()
    replace_file(path, wrong_bytes(study, artifact, form, tmp_path))
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    assert_attempts_private_free(study)
    replace_file(path, expected)  # even the exact bytes do not reopen a completed failure
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]
    assert written_W(study) == []


@pytest.mark.parametrize("artifact", ["registry", "marker"])
@pytest.mark.parametrize("form", ["substituted", "reencoded"])
def test_s6_f1_07_inconsistent_restoration_after_unavailable_fails_verification(
        form, artifact, bases, tmp_path):
    study = clone(bases("issued"), tmp_path)
    path = durable(study, artifact)
    expected = path.read_bytes()
    path.unlink()
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE"]
    replace_file(path, wrong_bytes(study, artifact, form, tmp_path))
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE", "FAILED_VERIFICATION"]
    replace_file(path, expected)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["UNAVAILABLE", "FAILED_VERIFICATION", "REFUSED_PRECONDITION"]
    assert written_W(study) == []
    assert_attempts_private_free(study)


@pytest.mark.parametrize("missing, wrong", [("registry", "marker"), ("marker", "registry")])
def test_s6_f1_08_a_mismatched_artifact_beside_a_missing_one_fails_verification(
        missing, wrong, bases, tmp_path):
    study = clone(bases("issued"), tmp_path)
    saved = {name: durable(study, name).read_bytes() for name in DURABLE}
    durable(study, missing).unlink()
    replace_file(durable(study, wrong), wrong_bytes(study, wrong, "substituted", tmp_path))
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    for name, raw in saved.items():
        replace_file(durable(study, name), raw)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


@pytest.mark.parametrize("case, missing", [("synthetic", "marker"),
                                           ("producer_absent", "registry")])
def test_s6_f1_10_boundary_content_defect_stays_failed_verification_with_an_artifact_missing(
        case, missing, bases, tmp_path):
    study = clone(bases("consumed"), tmp_path)
    producer.write_boundary(study, producer.w05_evidence(study, case, tmp_path), own_root=False)
    producer.draw(study, producer.raw_sequence(study, producer.accepted_values(study)))
    producer.seal(study)
    producer.issue_S(study)
    path = durable(study, missing)
    held = path.read_bytes()
    path.unlink()
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    assert_attempts_private_free(study)
    path.write_bytes(held)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]


# ==== S6-F2: W-04 classification in every chain shape ========================================

@pytest.mark.parametrize("shape", list(SHAPES))
@pytest.mark.parametrize("event", ["recorder_consume", "lead_revoke_nothing"])
def test_s6_f2_01_a_forbidden_tail_event_fails_verification_in_every_chain_shape(
        event, shape, bases, tmp_path, monkeypatch):
    study = clone(bases(shape), tmp_path)
    assert continuation(study) == SHAPES[shape]
    tail_event(study, event)
    calls = producer.verifier_spy(monkeypatch)
    for expected in (["FAILED_VERIFICATION"], ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]):
        with pytest.raises(IntegrityError):
            produce(study)
        assert labels(study) == expected and calls == [] and written_W(study) == []
    assert_attempts_private_free(study)


@pytest.mark.parametrize("shape", ["generated-continue", "generated-release"])
def test_s6_f2_02_only_extending_issues_after_a_completed_continuation_are_refused(
        shape, bases, tmp_path, monkeypatch):
    study = clone(bases(shape), tmp_path)
    assert continuation(study) == "completed"
    tail_event(study, "extending_issue")
    tail_event(study, "extending_issue")
    reads = producer.private_read_spy(monkeypatch, study)
    calls = producer.verifier_spy(monkeypatch)
    for expected in (["REFUSED_PRECONDITION"], ["REFUSED_PRECONDITION"] * 2):  # not terminal
        with pytest.raises(IntegrityError, match="completed-stage continuation"):
            produce(study)
        assert labels(study) == expected
        assert reads == [] and calls == [] and written_W(study) == []


@pytest.mark.parametrize("shape, tail", [
    ("generated-continue", ("extending_issue", "recorder_consume")),
    ("generated-release", ("lead_revoke_nothing", "extending_issue"))])
def test_s6_f2_03_a_mixed_tail_after_a_completed_continuation_fails_verification(
        shape, tail, bases, tmp_path, monkeypatch):
    study = clone(bases(shape), tmp_path)
    assert continuation(study) == "completed"
    for kind in tail:
        tail_event(study, kind)
    calls = producer.verifier_spy(monkeypatch)
    for expected in (["FAILED_VERIFICATION"], ["FAILED_VERIFICATION", "REFUSED_PRECONDITION"]):
        with pytest.raises(IntegrityError):
            produce(study)
        assert labels(study) == expected and calls == [] and written_W(study) == []


# ==== S6-F3: the W/PASS transition inside the protected action ================================

PASS_WRITES = ("W-retention", "W.json", "outcome-1")


def test_s6_f3_01_W_retention_W_json_and_PASS_are_written_under_the_lease_at_its_tip(
        bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    tip = study.log.tip
    writes = Writes(monkeypatch, study)
    reference = produce(study)
    W = read_W(study)
    assert record_ref(W) == reference and W["body"]["active_authority_tip"] == tip
    kinds = writes.kinds()
    assert kinds.count("W.json") == kinds.count("outcome-1") == 1 and "W-retention" in kinds
    for kind, name, lock, durable_tip in writes.events:
        if kind == "intent-1":
            assert not lock, name  # the intent is written before the lease
        elif kind in PASS_WRITES:
            assert lock and durable_tip == tip, (kind, lock, durable_tip)
    first = [kinds.index(kind) for kind in PASS_WRITES]
    assert kinds.index("intent-1") < first[0] and first == sorted(first)
    under_lock = [event for event in writes.events if event[2]]
    assert under_lock[-1][0] == "outcome-1"  # PASS is the last write of the protected action
    for kind in PASS_WRITES:
        phases = [phase for phase, label, lock, durable_tip in writes.storage if label == kind]
        assert {"fsync", "readback", "installed", "directory-flush-complete"} <= set(phases)
        assert all(lock and durable_tip == tip for _phase, label, lock, durable_tip in writes.storage
                   if label == kind)
    assert writes.storage[-1] == ("directory-flush-complete", "outcome-1", True, tip)
    (outcome,) = outcomes(study)
    assert (outcome["outcome"], outcome["W"]) == ("PASS", reference)
    assert lock_free(study) and study.log.tip == tip


def test_s6_f3_02_an_append_attempted_before_the_PASS_write_is_refused_as_busy(
        bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    tip = study.log.tip
    events = {path.name: path.read_bytes() for path in producer.event_files(study)}
    stop = study.log.retain_artifact(encode({"kind": "SYNTHETIC_STOP_EVIDENCE",
                                             "label": "f3-interleave"}),
                                     "SYNTHETIC-STOP-f3-interleave")
    other = producer.authority(study.log.root, study.log.bindings, study.by_digest,
                               {"source_drift": False}, dict(study.log.actors))
    attempts: dict[str, str] = {}

    def interleave(kind: str, _path: Path | None) -> None:
        if kind in PASS_WRITES and kind not in attempts:
            try:
                other.append("HOLD", INTEGRITY, expected_tip=tip, operation_id=OP,
                             evidence=[stop])
            except IntegrityError as error:
                attempts[kind] = str(error)
            else:
                attempts[kind] = "APPENDED"
    Writes(monkeypatch, study, interleave)
    reference = produce(study)
    assert set(attempts) == set(PASS_WRITES)
    assert all("busy" in message for message in attempts.values()), attempts
    assert {path.name: path.read_bytes() for path in producer.event_files(study)} == events
    held = other.append("HOLD", INTEGRITY, expected_tip=tip, operation_id=OP, evidence=[stop])
    assert held["body"]["prior_tip"] == tip and study.log.tip == held["digest"] != tip
    W = read_W(study)
    assert record_ref(W) == reference and W["body"]["active_authority_tip"] == tip
    (outcome,) = outcomes(study)
    assert (outcome["outcome"], outcome["W"]) == ("PASS", reference)


PARTIAL_W = b'{"body":{"record_role":"W"'


@pytest.mark.parametrize("step, fault", [("W-retention", "integrity_error"),
                                         ("W.json", "os_error"),
                                         ("W.json", "partial_then_stop"),
                                         ("outcome-1", "stop")])
def test_s6_f3_03_a_write_step_exception_propagates_without_an_outcome(
        step, fault, bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    injected: BaseException = {
        "integrity_error": IntegrityError("durable evidence read-back failed (synthetic)"),
        "os_error": OSError(errno.EIO, "synthetic write fault"),
        "partial_then_stop": producer.SimulatedStop(),
        "stop": producer.SimulatedStop()}[fault]
    fired: list[str] = []

    def fault_once(kind: str, path: Path | None) -> None:
        if kind == step and not fired:
            fired.append(kind)
            if fault == "partial_then_stop":
                path.write_bytes(PARTIAL_W)
            raise injected
    Writes(monkeypatch, study, fault_once)
    with pytest.raises(type(injected)) as raised:
        produce(study)
    assert raised.value is injected and fired == [step]
    folder = w_folder(study)
    assert not (folder / OUTCOME).exists() and outcomes(study) == []  # no outcome record
    assert lock_free(study)
    left = (folder / "W.json").read_bytes() if step == "outcome-1" else None
    torn = {path: path.read_bytes() for path in pv._staging(folder).rglob("*")
            if path.is_file() and path.read_bytes() == PARTIAL_W}
    if step == "outcome-1":
        assert left == encode(json.loads(left))
    if fault == "partial_then_stop":
        assert torn and not (folder / "W.json").exists()
    calls = producer.verifier_spy(monkeypatch)
    reference = produce(study)
    assert labels(study) == ["PASS"] and record_ref(read_W(study)) == reference
    if step == "outcome-1" or fault == "partial_then_stop":
        assert len(calls) == 1  # superseded L1/L2b require complete exact re-verification
        if left is not None:
            assert (folder / "W.json").read_bytes() == left
        assert all(path.read_bytes() == raw for path, raw in torn.items())
    for record in outcomes(study):  # the next attempt lists the faulted one as interrupted
        assert len(record["interrupted_prior_attempts"]) == 1


def test_s6_f3_04_a_post_action_recheck_failure_after_PASS_propagates_with_one_outcome(
        bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)

    def drift_at_pass(kind: str, _path: Path | None) -> None:
        if kind == "outcome-1-published":
            study.flags["source_drift"] = True  # pinned-source drift seen only by the recheck
    Writes(monkeypatch, study, drift_at_pass)
    with pytest.raises(IntegrityError, match="source pin drift"):
        produce(study)
    study.flags["source_drift"] = False
    (outcome,) = outcomes(study)  # exactly one outcome for the attempt, and it is PASS
    W = read_W(study)
    assert (outcome["outcome"], outcome["W"]) == ("PASS", record_ref(W))
    assert lock_free(study)


@pytest.mark.parametrize("case, expected", [("salt_missing", "UNAVAILABLE"),
                                            ("held", "REFUSED_PRECONDITION"),
                                            ("tail_consume", "FAILED_VERIFICATION")])
def test_s6_f3_05_non_pass_outcomes_are_written_after_the_lease_is_released(
        case, expected, bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    if case == "salt_missing":
        salt = study.S["body"]["salt"]["sha256_raw"]
        (study.log.root / "evidence-raw" / (salt + ".bin")).unlink()
    elif case == "held":
        producer.hold(study, "f3-held")
    else:
        tail_event(study, "recorder_consume")
    writes = Writes(monkeypatch, study)
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == [expected] and written_W(study) == []
    (outcome_write,) = writes.watched("outcome-1")
    assert not outcome_write[2]  # written by the handler, after the lease
    assert all(not lock for _kind, _name, lock, _tip in writes.watched("intent-1"))
    assert not {"W-retention", "W.json"} & set(writes.kinds()) and lock_free(study)


# ==== S6-F4: operational W admissibility at the pre-U check and at U issuance =================

def test_s6_f4_01_a_hand_constructed_W_added_by_generic_issue_is_refused(bases, tmp_path):
    study = clone(bases("issued"), tmp_path)
    producer.issue_W(study, producer.hand_W(study))
    assert not w_folder(study).exists()  # the producer never ran for this S
    body = producer.template_body(study)
    assert consumers(study, body, producer.make_U(study, body, [])) == REFUSED


FOLDER_FAULTS = (
    "producer folder absent: W bytes without producer evidence",  # S6-F4-01
    "PASS outcome missing",  # S6-F4-02
    "PASS outcome names another W",  # S6-F4-03
    "PASS outcome copied from another study",  # S6-F4-03
    "W.json of another S",  # S6-F4-04
    "attempt records and W.json of another S",  # S6-F4-04
    "intent names another S",  # S6-F4-04
    "intent names another verifier",  # S6-F4-04
    "intent expects another authority tip",  # A4
    "W.json missing",  # A3
    "W.json not the canonical W bytes",  # A3
    "a second PASS outcome",  # A4
    "a FAILED_VERIFICATION attempt beside the PASS",  # A4
)


def test_s6_f4_01_to_04_producer_evidence_faults_refuse_pre_u_and_issuance(bases, tmp_path):
    study = clone(bases("w-issued"), tmp_path)
    other = clone(bases("partial-release-continue"), tmp_path / "other")
    other_ref = produce(other)
    assert other.S["digest"] != study.S["digest"] and other_ref != study.log.bindings["W"]
    body, _, U = receipt_and_U(study)
    folder, files, others = w_folder(study), folder_files(study), folder_files(other)
    intent, outcome = json.loads(files[INTENT]), json.loads(files[OUTCOME])
    W = study.records["W"]
    tip = W["body"]["active_authority_tip"]

    def write(name: str, raw: bytes) -> None:
        replace_file(folder / name, raw)

    def fault(name: str) -> None:
        if name.startswith("producer folder absent"):
            shutil.rmtree(folder)
        elif name == "PASS outcome missing":
            (folder / OUTCOME).unlink()
        elif name == "PASS outcome names another W":
            write(OUTCOME, encode({**outcome, "W": other_ref}))
        elif name == "PASS outcome copied from another study":
            write(OUTCOME, others[OUTCOME])
        elif name == "W.json of another S":
            write("W.json", others["W.json"])
        elif name == "attempt records and W.json of another S":
            for item in (INTENT, OUTCOME, "W.json"):
                write(item, others[item])
        elif name == "intent names another S":
            write(INTENT, renamed(intent, (record_ref(study.S), record_ref(other.S)),
                                  (study.S["digest"], other.S["digest"])))
        elif name == "intent names another verifier":  # a registered independent verifier
            write(INTENT, renamed(intent, (VERIFIER["actor_id"], SECOND_CHECKER["actor_id"])))
        elif name == "intent expects another authority tip":
            write(INTENT, renamed(intent, (tip, study.consume_tip)))
        elif name == "W.json missing":
            (folder / "W.json").unlink()
        elif name == "W.json not the canonical W bytes":
            write("W.json", json.dumps(W, indent=1).encode("utf-8"))
        elif name == "a second PASS outcome":
            write("attempt-0002.intent.json", encode(renumbered(intent)))
            write("attempt-0002.outcome.json", encode(renumbered(outcome)))
        else:
            assert name == "a FAILED_VERIFICATION attempt beside the PASS"
            write("attempt-0002.intent.json", encode(renumbered(intent)))
            write("attempt-0002.outcome.json", encode({
                **renumbered(outcome), "outcome": "FAILED_VERIFICATION", "W": None,
                "reason": "synthetic completed verification failure"}))
    pristine = tree(study.log.root)
    results: dict[str, tuple[str, ...]] = {}
    for name in FOLDER_FAULTS:
        fault(name)
        found = consumers(study, body, U)
        restore_folder(study, files)
        restored = (tree(study.log.root) == pristine
                    and outcome_of(study, lambda: admissible(study)) == "accepted")
        results[name] = (*found, "restored" if restored else "not restored")
        if results[name] != (*REFUSED, "restored"):
            break
    assert results == {name: (*REFUSED, "restored") for name in FOLDER_FAULTS}
    producer.issue_U(study, U)  # the same receipt and U issue once the evidence is intact
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"


IDENTITY_FAULTS = (
    "W verifier no longer a registered independent verifier",  # A1
    "durable first-raw marker missing",  # A2
    "durable producer registry missing",  # A2
    "durable registry names another producer root",  # A2, S6-F4-04
    "retained verification result bytes changed",  # A5
    "retained verification result missing",  # A5
)


def test_s6_f4_04_and_06_identity_boundary_and_result_faults_refuse_pre_u_and_issuance(
        bases, tmp_path):
    study = clone(bases("w-issued"), tmp_path)
    body, _, U = receipt_and_U(study)
    W = study.records["W"]
    (result,) = [ref for ref in W["body"]["evidence"] if ref["evidence_id"] == RESULT_ID]
    result_path = study.log.root / "evidence-raw" / (result["sha256_raw"] + ".bin")
    registry, marker = durable(study, "registry"), durable(study, "marker")
    saved = {path: path.read_bytes() for path in (registry, marker, result_path)}
    role = study.log.actors[VERIFIER["actor_id"]]

    def fault(name: str) -> None:
        if name.startswith("W verifier"):
            del study.log.actors[VERIFIER["actor_id"]]
        elif name == "durable first-raw marker missing":
            marker.unlink()
        elif name == "durable producer registry missing":
            registry.unlink()
        elif name == "durable registry names another producer root":
            replace_file(registry, wrong_bytes(study, "registry", "substituted", tmp_path))
        elif name == "retained verification result bytes changed":
            replace_file(result_path, saved[result_path][:-1] + b" ")
        else:
            assert name == "retained verification result missing"
            result_path.unlink()

    def restore() -> None:
        study.log.actors[VERIFIER["actor_id"]] = role
        for path, raw in saved.items():
            replace_file(path, raw)
    pristine = tree(study.log.root)
    results: dict[str, tuple[str, ...]] = {}
    for name in IDENTITY_FAULTS:
        fault(name)
        found = consumers(study, body, U)
        restore()
        restored = (tree(study.log.root) == pristine
                    and outcome_of(study, lambda: admissible(study)) == "accepted")
        results[name] = (*found, "restored" if restored else "not restored")
        if results[name] != (*REFUSED, "restored"):
            break
    assert results == {name: (*REFUSED, "restored") for name in IDENTITY_FAULTS}
    producer.issue_U(study, U)
    assert pv.verify_operational_u(study.log)["decision"] == "ADMISSIBLE"


def test_s6_f4_05_a_hand_W_after_failed_verification_is_refused_at_both(bases, tmp_path):
    source = clone(bases("w-issued"), tmp_path / "source")
    study = clone(bases("issued"), tmp_path / "failed")
    marker = durable(study, "marker")
    expected = marker.read_bytes()
    replace_file(marker, wrong_bytes(study, "marker", "substituted", tmp_path))
    with pytest.raises(IntegrityError):
        produce(study)
    assert labels(study) == ["FAILED_VERIFICATION"] and written_W(study) == []
    replace_file(marker, expected)
    # The producer's W of an identical study, its evidence and a PASS receipt, carried over and
    # issued by the lead's generic ISSUE: only the producer's own records differ.
    W = source.records["W"]
    for ref in W["body"]["evidence"]:
        study.log.retain_artifact(source.log.read_artifact(ref), ref["evidence_id"])
    study.log.retain_record(W)
    producer.issue_W(study, record_ref(W))
    body, passed, U = receipt_and_U(source)
    receipt = passed["receipt"]
    study.log.retain_artifact(source.log.read_artifact(receipt), receipt["evidence_id"])
    assert ([path.read_bytes() for path in producer.event_files(study)]
            == [path.read_bytes() for path in producer.event_files(source)])
    assert producer.template_body(study) == body
    assert producer.make_U(study, body, [receipt]) == U
    assert consumers(study, body, U) == REFUSED
    producer.issue_U(source, U)  # control: the same U issues where the producer's PASS exists
    assert pv.verify_operational_u(source.log)["decision"] == "ADMISSIBLE"


@pytest.mark.parametrize("fault", ["active_chain_tip", "entropy_source", "supplement_chain",
                                   "result_absent"])
def test_s6_f4_06_a5_a_W_whose_retained_result_does_not_match_is_refused(fault, bases,
                                                                         tmp_path):
    study = clone(bases("w-produced"), tmp_path)
    W, folder = read_W(study), w_folder(study)
    body = W["body"]
    (result_ref,) = [ref for ref in body["evidence"] if ref["evidence_id"] == RESULT_ID]
    result = json.loads(study.log.read_artifact(result_ref))
    # The producer's own retained result satisfies A5.
    assert result["kind"] == RESULT_KIND
    assert result["active_chain_tip"] == body["active_authority_tip"]
    assert result["supplement_chain"] == body["supplement_chain"]
    verified = result["verifier_result"]
    assert (verified["decision"], verified["entropy_source"]) == ("PASS", "REAL")
    evidence = [ref for ref in body["evidence"] if ref != result_ref]
    if fault != "result_absent":
        if fault == "active_chain_tip":
            result["active_chain_tip"] = study.consume_tip
        elif fault == "entropy_source":
            result["verifier_result"] = {**verified, "entropy_source": "SYNTHETIC"}
        else:
            result["supplement_chain"] = [record_ref(study.S)]
        evidence.append(study.log.retain_artifact(encode(result), RESULT_ID))
    # A W differing only in its retained result, with A1-A4 and A6 kept for it: W.json, the
    # PASS outcome and the lead's ISSUE all name it, and its tip and intent are unchanged.
    changed = make_record("W", {**body, "evidence": evidence})
    study.log.retain_record(changed)
    replace_file(folder / "W.json", encode(changed))
    outcome = json.loads((folder / OUTCOME).read_bytes())
    replace_file(folder / OUTCOME, encode({**outcome, "W": record_ref(changed)}))
    producer.issue_W(study, record_ref(changed))
    assert consumers(study, producer.template_body(study), None) == REFUSED[:2]


@pytest.mark.parametrize("event", ["recorder_consume", "lead_revoke_nothing"])
def test_s6_f4_06_a6_a_non_issue_event_before_the_lead_issue_W_is_refused(event, bases,
                                                                          tmp_path):
    study = clone(bases("w-produced"), tmp_path)
    W = read_W(study)
    tail_event(study, event)
    producer.issue_W(study, record_ref(W))
    assert consumers(study, producer.template_body(study), None) == REFUSED[:2]


def test_s6_f4_06_a6_a_W_revoked_after_its_issue_is_refused(bases, tmp_path):
    study = clone(bases("w-issued"), tmp_path)
    body, passed, _ = receipt_and_U(study)
    admissible(study)
    stop = study.log.retain_artifact(encode({"kind": "SYNTHETIC_STOP_EVIDENCE",
                                             "label": "revoke-W"}), "SYNTHETIC-STOP-revoke-W")
    study.log.append("REVOKE", LEAD, expected_tip=study.log.tip, operation_id=OP,
                     affected=[study.log.bindings["W"]], evidence=[stop])
    U = producer.make_U(study, body, [passed["receipt"]])
    assert consumers(study, body, U) == REFUSED


@pytest.mark.parametrize("case", ["extending_issue_before_issue_W",
                                  "non_revoking_events_after_issue_W"])
def test_s6_f4_06_a6_limit_other_events_leave_W_admissible(case, bases, tmp_path):
    if case == "extending_issue_before_issue_W":  # a tuple-extending ISSUE may intervene
        study = clone(bases("w-produced"), tmp_path)
        W = read_W(study)
        tail_event(study, "extending_issue")
        producer.issue_W(study, record_ref(W))
    else:  # later events that revoke nothing do not make W inadmissible
        study = clone(bases("w-issued"), tmp_path)
        tail_event(study, "recorder_consume")
        tail_event(study, "lead_revoke_nothing")
    admissible(study)
    issue_and_publish_U(study, tmp_path)


def test_s6_f4_07_a_valid_producer_W_progresses_and_stays_admissible(bases, tmp_path):
    study = clone(bases("w-issued"), tmp_path)
    W = study.records["W"]
    (outcome,) = outcomes(study)
    assert (outcome["outcome"], outcome["W"]) == ("PASS", record_ref(W))
    assert (w_folder(study) / "W.json").read_bytes() == encode(W)
    admissible(study)
    issue_and_publish_U(study, tmp_path)
    admissible(study)  # neither ISSUE(+U) nor the publisher's CONSUME of U revokes W


@pytest.mark.parametrize("shape", ["partial-release-continue", "generated-continue"])
def test_s6_f4_07_a_W_over_a_continuation_chain_is_admissible(shape, bases, tmp_path):
    study = clone(bases(shape), tmp_path)
    producer.issue_W(study, produce(study))
    assert read_W(study)["body"]["supplement_chain"]
    admissible(study)
    issue_and_publish_U(study, tmp_path)


def test_s6_f4_07_a4_admits_W_after_unavailable_interrupted_and_later_refused_attempts(
        bases, tmp_path, monkeypatch):
    study = clone(bases("issued"), tmp_path)
    salt = study.log.root / "evidence-raw" / (study.S["body"]["salt"]["sha256_raw"] + ".bin")
    held = salt.read_bytes()
    salt.unlink()
    with pytest.raises(IntegrityError):
        produce(study)  # attempt 1: UNAVAILABLE
    salt.write_bytes(held)
    sealed, stopped = pv.verify_complete_private, []

    def stop_once(**kwargs):
        if not stopped:
            stopped.append(True)
            raise producer.SimulatedStop
        return sealed(**kwargs)
    monkeypatch.setattr(pv, "verify_complete_private", stop_once)
    with pytest.raises(producer.SimulatedStop):
        produce(study)  # attempt 2: interrupted
    reference = produce(study)  # attempt 3: PASS
    with pytest.raises(IntegrityError):
        produce(study)  # attempt 4: refused
    assert labels(study) == ["UNAVAILABLE", "PASS", "REFUSED_PRECONDITION"]
    producer.issue_W(study, reference)
    admissible(study)
    issue_and_publish_U(study, tmp_path)


def test_s6_f4_08_public_signatures_unchanged_and_the_admissibility_check_takes_authority_only():
    def shape(function: Callable) -> list[tuple[str, Any]]:
        return [(p.name, p.kind) for p in inspect.signature(function).parameters.values()]
    positional, keyword = inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
    assert shape(pv.produce_private_verification) == [
        ("authority", positional), ("verifier", keyword), ("expected_tip", keyword),
        ("operation_id", keyword)]
    assert shape(pv.check_publication_template) == [
        ("authority", positional), ("proposed_body", positional), ("checker", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.issue_publication_authorization) == [
        ("authority", positional), ("U", positional), ("lead", keyword),
        ("expected_tip", keyword), ("operation_id", keyword)]
    assert shape(pv.verify_operational_u) == [("authority", positional)]
    (parameter,) = inspect.signature(pv.verify_operational_w).parameters.values()
    assert parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, positional)
    assert parameter.default is inspect.Parameter.empty
    for args, kwargs in (((), {}), ((object(), object()), {}),
                         ((object(),), {"expected_tip": "0" * 64}),
                         ((object(),), {"verifier": VERIFIER}),
                         ((object(),), {"W": {}})):
        with pytest.raises(TypeError):
            pv.verify_operational_w(*args, **kwargs)
    assert RESULT_ID in ADMISSIBLE_ONLY_IF["A5_retained_result"]
    assert RESULT_KIND in ADMISSIBLE_ONLY_IF["A5_retained_result"]
