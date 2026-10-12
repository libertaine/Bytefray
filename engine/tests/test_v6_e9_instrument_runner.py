"""Native adapter construction and locked, complete-rectangle orchestration."""

import ast
from pathlib import Path

import pytest

from tools.research.v6.e9 import instrument, runner
from tools.research.v6.e9.collection import Dispatcher, Journal
from tools.research.v6.e9.protocol import (
    Cell,
    IntegrityError,
    canonical,
    load_protocol,
    read_json,
    write_once,
)


@pytest.mark.parametrize("row,opponent,seat", [("A", "ADAPT8", "A"), ("A", "ADAPT8", "B"),
    ("RUSH8", "RUSH8", "A"), ("REACQ8", "REACQ8", "B"), ("S16", "STRESS8", "B")])
def test_native_adapter_exact_environment_defaults_and_self_twins(tmp_path, row, opponent, seat):
    protocol = load_protocol()
    defaults = runner.materialize(tmp_path, protocol)
    cell = Cell(row, opponent, 1, seat)
    request = runner.native_request(tmp_path, tmp_path / "attempt", cell, 7, protocol, defaults)
    assert request.max_ticks == 1000 and request.agent_call_timeout is None
    assert request.scheduler_chunk_size is request.scheduler_rotate_start is None
    assert tuple(e.name for e in request.entrants) == cell.packages(protocol)
    assert tuple(e.agent_id for e in request.entrants) == ("A", "B")
    assert request.config.instr_per_tick == 8 and request.config.weights.kill == 5
    assert len(defaults) == 41
    defaults[cell.packages(protocol)[0]]["unregistered"] = True
    with pytest.raises(IntegrityError):
        runner.native_request(tmp_path, tmp_path / "attempt", cell, 7, protocol, defaults)


def test_cli_unapproved_execution_refuses_before_private_data_or_worker(monkeypatch):
    monkeypatch.setattr(runner.sys, "argv", ["e9", "collect"])
    monkeypatch.setattr(runner, "preflight", lambda *_: pytest.fail("unauthorized preflight"))
    assert runner.main() == 2


def test_no_seed_generator_or_rng_choice_in_instrument_sources():
    for name in instrument.MODULES:
        source = Path(instrument.__file__).with_name(name).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            if isinstance(call.func, ast.Attribute):
                assert call.func.attr not in {"urandom", "token_bytes", "randbits", "randrange", "choice", "choices"}


def test_completed_validation_resume_never_reexecutes(tmp_path):
    journal = Journal(tmp_path, Cell("A", "RUSH8", 1, "A"), {"synthetic": True})
    attempt = journal.start()
    write_once(attempt / "result.json", {"synthetic": True})
    journal.complete(1)

    def derived(path):
        from tools.research.v6.e9.protocol import file_digest
        for name in ("replay.jsonl", "trace.jsonl", "diagnostic.json"):
            write_once(path / name, {"synthetic": True})
        return {name: file_digest(path / name) for name in ("result.json", "replay.jsonl", "trace.jsonl", "diagnostic.json")}

    # The dispatcher resumes validation only. Real authoritative files must
    # already exist; the fixture validator stands in for the offline checker.
    output = Dispatcher(lambda _: pytest.fail("completed evidence reexecuted"), derived,
                        lambda _: pytest.fail("completed evidence requested recovery")).dispatch(journal)
    assert output == attempt and len([e for e in journal.events() if e["kind"] == "started"]) == 1


def test_incomplete_rectangle_seals_not_evaluable_without_payoff_analysis(tmp_path, monkeypatch):
    protocol = load_protocol()
    cell = Cell("A", "RUSH8", 1, "A")
    execution = {"synthetic": "no experimental execution"}
    monkeypatch.setattr(runner, "preflight", lambda *_: (protocol, "1" * 64, tmp_path, [7], execution))
    monkeypatch.setattr(runner, "cells", lambda _: iter([cell]))
    monkeypatch.setattr(runner, "assemble", lambda *_: pytest.fail("incomplete outcomes were analyzed"))
    output = runner.finalize(None, tmp_path / "not-read")
    assert output["classification"] == {"priority": 1, "primary": "NOT EVALUABLE"}
    assert output["collection"]["missing"] == 1
    assert canonical(read_json(tmp_path / "final_registered_result.json")) == canonical(output)
    with pytest.raises(FileExistsError):
        instrument.seal(output, tmp_path / "final_registered_result.json")
