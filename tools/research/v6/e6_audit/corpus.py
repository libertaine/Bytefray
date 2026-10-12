"""PA-1: read the frozen E6 corpus, verifying every byte read against its pin.

The pins are the E6 records themselves:

* ``tools/research/v6/e6/pre_reveal_manifest.json`` pins each field's
  ``experiment_result.json``, ``provenance.json``, trace index and telemetry
  summaries, with its cell count, and every record the interpretation read;
* ``tools/research/v6/e6/final_record.json`` pins ``d6.json`` and
  ``e6_interpretation.json``, and the revealed seed list;
* each telemetry summary line pins its cell's stored callback rows
  (``rows_sha256``, the SHA-256 of the uncompressed canonical rows).

Nothing here writes a file. A mismatch raises ``IntegrityError``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.research.v6.e6 import telemetry, traces

REPO_ROOT = Path(__file__).resolve().parents[4]
MATRIX_ID = "v6-e6-matrix-v2-7de29a4a6954"
CORPUS_ROOT = Path("runs/research_v6_e6") / MATRIX_ID
MANIFEST = Path("tools/research/v6/e6/pre_reveal_manifest.json")
FINAL_RECORD = Path("tools/research/v6/e6/final_record.json")
SEEDS_REVEALED = Path("tools/research/v6/e6/seeds_revealed.txt")

#: The four E6 conditions and their (sensing, disruption) factor levels:
#: sensing 0 = no radius, 1 = radius 32; disruption 0 = whole tick, 1 = lambda 1.
CONDITIONS: tuple[str, ...] = ("C-E6", "T-E6", "C-E6L", "T-E6L")
FACTORS: Mapping[str, tuple[int, int]] = {"C-E6": (0, 0), "T-E6": (1, 0), "C-E6L": (0, 1), "T-E6L": (1, 1)}
FIELDS: tuple[str, ...] = ("F1", "F2")
FIELD_FILES: tuple[str, ...] = (
    "experiment_result.json", "provenance.json", "traces/summaries.jsonl", "traces/trace_index.json",
)


class IntegrityError(RuntimeError):
    """A byte read from the corpus does not match its pin."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise IntegrityError(message)


def verify_pins(repo: Path = REPO_ROOT) -> dict[str, Any]:
    """PA-1 at the file level: every pinned corpus file and record, and the seed list."""

    manifest = _json(repo / MANIFEST)
    final = _json(repo / FINAL_RECORD)
    root = repo / CORPUS_ROOT
    _require(manifest["structural_matrix_id"] == MATRIX_ID, "manifest names another matrix")
    _require(final["structural_matrix_id"] == MATRIX_ID, "final record names another matrix")
    files = 0
    for key, pins in sorted(manifest["fields"].items()):
        for name in FIELD_FILES:
            _require(sha256_file(root / key / name) == pins[name], f"{key}/{name}: SHA-256 differs from the manifest")
            files += 1
    for name, digest in sorted(manifest["records"].items()):
        _require(sha256_file(root / "records" / name) == digest, f"records/{name}: SHA-256 differs from the manifest")
        files += 1
    for name in ("d6", "e6_interpretation"):
        pin = final[name if name == "d6" else "interpretation"]
        _require(sha256_file(repo / pin["path"]) == pin["sha256"], f"{pin['path']}: SHA-256 differs from the final record")
        files += 1
    _require(final["e6_analysis"]["sha256"] == manifest["records"]["e6_analysis.json"],
             "final record and manifest disagree on e6_analysis.json")
    seeds_bytes = (repo / SEEDS_REVEALED).read_bytes()
    commitment = sha256_bytes(seeds_bytes)
    _require(commitment == manifest["seed_commitment"] == final["seed_commitment"], "seed list does not match the commitment")
    _require(commitment == final["revealed_list"]["sha256"], "seed list does not match the final record")
    seeds = [int(line) for line in seeds_bytes.decode("ascii").splitlines()]
    _require(len(seeds) == len(set(seeds)) == final["revealed_list"]["seeds"], "seed list is not 32 unique seeds")
    return {
        "structural_matrix_id": MATRIX_ID,
        "execution_matrix_identity": manifest["execution_matrix_identity"],
        "freeze_id": manifest["freeze_id"],
        "seed_commitment": commitment,
        "pinned_files_verified": files,
        "seeds": len(seeds),
    }


def load_seeds(repo: Path = REPO_ROOT) -> list[int]:
    return [int(line) for line in (repo / SEEDS_REVEALED).read_text(encoding="ascii").splitlines()]


@dataclass
class Corpus:
    """The frozen cells and telemetry summaries of all four conditions."""

    repo: Path
    seeds: list[int]
    cells: dict[str, dict[str, list[dict[str, Any]]]]
    summaries: dict[str, dict[str, dict[str, dict[str, Any]]]]
    trace_records: dict[str, dict[str, Mapping[str, traces.TraceRecord]]]
    rows_verified: int = field(default=0)

    def field_root(self, condition: str, field_id: str) -> Path:
        return self.repo / CORPUS_ROOT / condition / field_id

    def rows(self, condition: str, field_id: str, schedule_id: str) -> list[list[Any]]:
        """One cell's stored callback rows, verified against its summary's ``rows_sha256``."""

        record = self.trace_records[condition][field_id][schedule_id]
        rows = telemetry.read_callbacks(self.field_root(condition, field_id), record)
        pinned = self.summaries[condition][field_id][schedule_id]["rows_sha256"]
        _require(sha256_bytes(telemetry.rows_bytes(rows)) == pinned,
                 f"{condition}/{field_id} {schedule_id}: callback rows differ from their pinned SHA-256")
        self.rows_verified += 1
        return rows


def load_corpus(repo: Path = REPO_ROOT) -> Corpus:
    """Load every cell and summary; the files were pinned by ``verify_pins``."""

    manifest = _json(repo / MANIFEST)
    seeds = load_seeds(repo)
    on_list = set(seeds)
    cells: dict[str, dict[str, list[dict[str, Any]]]] = {}
    summaries: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    records: dict[str, dict[str, Mapping[str, traces.TraceRecord]]] = {}
    for condition in CONDITIONS:
        cells[condition], summaries[condition], records[condition] = {}, {}, {}
        for field_id in FIELDS:
            root = repo / CORPUS_ROOT / condition / field_id
            result = _json(root / "experiment_result.json")
            field_cells = [cell for block in result["conditions"] for cell in block["cells"]]
            _require(len(field_cells) == manifest["fields"][f"{condition}/{field_id}"]["cells"],
                     f"{condition}/{field_id}: cell count differs from the manifest")
            _require(all(cell["seed"] in on_list for cell in field_cells), f"{condition}/{field_id}: a seed is off the list")
            cells[condition][field_id] = field_cells
            lines = [json.loads(line) for line in (root / "traces" / "summaries.jsonl").read_text(encoding="utf-8").splitlines() if line]
            summaries[condition][field_id] = {line["schedule_id"]: line for line in lines}
            _require(set(summaries[condition][field_id]) == {cell["schedule_id"] for cell in field_cells},
                     f"{condition}/{field_id}: summaries do not cover exactly the cells")
            records[condition][field_id] = traces.records_by_schedule(traces.read_index(root))
    return Corpus(repo=repo, seeds=seeds, cells=cells, summaries=summaries, trace_records=records)


def frozen_analysis(repo: Path = REPO_ROOT) -> dict[str, Any]:
    """The frozen ``e6_analysis.json`` (pinned by ``verify_pins``)."""

    data: dict[str, Any] = _json(repo / CORPUS_ROOT / "records" / "e6_analysis.json")
    return data
