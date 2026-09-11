import argparse
import hashlib
import json
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from battle_engine.agent_api import AgentValidationError
from battle_engine.agent_parameters import EMPTY_PARAMETER_SCHEMA, resolve_parameters
from battle_engine.agents import agent_runtime_label, discover_agents, resolve_agent
from battle_engine.builtins import SUPPORTED, build_agent
from battle_engine.core import Config, Weights
from battle_engine.match_service import (
    MatchEntrant,
    MatchRequest,
    NativeMatchService,
    OverlappingCoreError,
    PythonMatchExecutionError,
    RulesetAgentUnsupportedError,
    RulesetRuntimeUnsupportedError,
    UnsupportedMatchCompositionError,
)
from battle_engine.paths import get_data_root
from battle_engine.placement import resolve_direct_match_starts
from battle_engine.pmars import PMarsError, run_pmars
from battle_engine.python_runtime import PythonEntrantInitializationError
from battle_engine.result_model import SCHEMA_VERSION_V1 as RESULT_SCHEMA_VERSION_V1
from battle_engine.result_model import ResultEnvelope, stable_id, write_json_atomic
from battle_engine.rules import BYTEFRAY_RULESET_ID
from battle_engine.ruleset_policy import (
    BYTEFRAY_RULESET_V2_ID,
    BYTEFRAY_RULESET_V4_ALPHA1_ID,
    BYTEFRAY_RULESET_V4_ALPHA2_ID,
    BYTEFRAY_RULESET_V4_ID,
    NoCompatibleRulesetError,
    resolve_omitted_ruleset_for_agents,
)
from battle_engine.starters import (
    describe_bootstrap_errors,
    describe_starter_refresh,
    ensure_starter_agents,
)

DEFAULT_REPLAY_RELATIVE_PATH = Path("runs") / "_loose" / "replay.jsonl"

# ----------------------------
# Helpers
# ----------------------------


def _pmars_arguments(
    red_a: Path,
    red_b: Path,
    *,
    core_size: int,
    max_cycles: int,
    max_processes: int,
    max_len: int,
    min_dist: int,
    rounds: int,
) -> list[str]:
    """Build pMARS arguments without resolving or invoking the executable."""
    return [
        "-b",
        "-r",
        str(rounds),
        "-s",
        str(core_size),
        "-c",
        str(max_cycles),
        "-p",
        str(max_processes),
        "-l",
        str(max_len),
        "-d",
        str(min_dist),
        str(red_a),
        str(red_b),
    ]



def _data_root() -> Path:
    """Return the shared writable data root."""
    return get_data_root()


def _resolve_replay_path(value: str | None) -> Path:
    """Resolve the default under the data root or an explicit path from the CWD."""
    if value is None:
        return (_data_root() / DEFAULT_REPLAY_RELATIVE_PATH).resolve()
    return Path(value).expanduser().resolve()


def _resolve_trace_path(value: str | None) -> Path | None:
    """Resolve an explicit trace path from the CWD, or ``None`` if omitted.

    Unlike ``--replay``, ``--trace`` has no implicit default: omission must
    stay ``None`` all the way into ``MatchRequest.trace_path`` so ordinary
    ``bytefray run`` invocations never start writing a trace artifact.
    """
    if value is None:
        return None
    return Path(value).expanduser().resolve()


def _parse_env_json(varname: str) -> dict[str, Any]:
    """
    Read JSON object from environment variable.
    Return {} on empty/missing.
    """
    raw = os.environ.get(varname, "").strip()
    if not raw:
        return {}

    try:
        obj = json.loads(raw)
    except Exception as exc:
        raise SystemExit(f"Malformed JSON in ${varname}: {exc}\nValue: {raw[:200]}...")

    if not isinstance(obj, dict):
        raise SystemExit(
            f"${varname} must be a JSON object (got {type(obj).__name__})."
        )

    return obj


def _merge_params(
    defaults: dict[str, Any], overrides: dict[str, Any]
) -> dict[str, Any]:
    merged = dict(defaults or {})
    merged.update(overrides or {})
    return merged


def _parse_param_assignment(raw: str) -> tuple[str, str]:
    """Split one ``--a-param KEY=VALUE`` flag into its two halves.

    The value is left as text on purpose. Every type decision belongs to the
    agent's declared schema, applied once by
    ``agent_parameters.resolve_parameters`` -- the CLI must not guess that
    ``8`` means an integer and ``0.25`` a float, because only the manifest
    knows which the parameter actually is.
    """

    key, separator, value = raw.partition("=")
    if not separator or not key.strip():
        raise SystemExit(
            f"Invalid --*-param value {raw!r}: expected KEY=VALUE, e.g. "
            f"'sweep_span_cores=2'."
        )
    return key.strip(), value


def _parameter_overrides(letter: str, args: argparse.Namespace) -> dict[str, Any]:
    """One slot's explicit parameter overrides, from every CLI source.

    ``BYTEFRAY_AGENT_{letter}_PARAMS_JSON`` (the pre-existing path the Agent
    Designer already exports and the only one that existed before V5 Alpha 1
    Phase D) first, then repeated ``--{letter}-param KEY=VALUE`` flags over
    the top: an explicitly typed flag beats an ambient environment variable.

    This is the *override* layer only. Schema defaults and any selected
    preset are applied underneath it by the canonical resolver, never here.
    """

    overrides: dict[str, Any] = dict(_parse_env_json(f"BYTEFRAY_AGENT_{letter}_PARAMS_JSON"))
    for raw in getattr(args, f"{letter.lower()}_param", None) or []:
        key, value = _parse_param_assignment(raw)
        overrides[key] = value
    return overrides


def _resolve_entrant_parameters(
    letter: str, spec: Any, args: argparse.Namespace
) -> dict[str, Any]:
    """Resolve one Python entrant's parameters before the match is built.

    Deliberately called from ``main`` rather than from inside the runtime, so
    an unknown key or an out-of-range value fails the invocation with a
    presentable diagnostic *before* any agent module is imported.
    """

    schema = getattr(spec, "parameter_schema", EMPTY_PARAMETER_SCHEMA)
    overrides = _parameter_overrides(letter, args)
    preset = getattr(args, f"{letter.lower()}_preset", None)

    # Resolved parameters are delivered as MatchContextV2.parameters, which
    # only an Agent API v2 agent receives.
    if getattr(spec, "api_version", None) != 2:
        if preset is not None:
            # `--*-preset` is new in Phase D, so refusing it here breaks no
            # existing invocation, and a silently-ignored preset name would
            # be indistinguishable from one that worked.
            raise SystemExit(
                f"Agent {letter}: --{letter.lower()}-preset was given, but "
                f"{getattr(spec, 'name', '<unknown>')!r} declares Agent API "
                f"{getattr(spec, 'api_version', None)!r}. Only Agent API v2 "
                f"agents declare parameter schemas and presets."
            )
        if overrides:
            # Free-form overrides for a v1 agent are the pre-existing
            # behaviour and must stay a no-op: the Agent Designer's Agent
            # Params field exports $BYTEFRAY_AGENT_*_PARAMS_JSON for whatever
            # agent is selected, and a v1 agent has always ignored it. Making
            # that an error would break a working path to enforce a rule that
            # arrived after it. Warn instead of failing, and instead of
            # staying silent as this did before Phase D.
            print(
                f"WARNING: agent {letter} parameters "
                f"({_keys_preview(overrides)}) were ignored: "
                f"{getattr(spec, 'name', '<unknown>')!r} declares Agent API "
                f"{getattr(spec, 'api_version', None)!r}, and only Agent API "
                f"v2 agents receive resolved parameters.",
                file=sys.stderr,
            )
        return {}

    try:
        return resolve_parameters(
            schema,
            legacy_defaults=getattr(spec, "defaults", None),
            preset=preset,
            overrides=overrides,
            path=getattr(spec, "dir", None),
        )
    except AgentValidationError as exc:
        raise SystemExit(f"Agent {letter}: {exc}") from exc


def _keys_preview(d: dict[str, Any]) -> str:
    return "{" + ", ".join(sorted(map(str, (d or {}).keys()))) + "}"


def read_blob(path: str | os.PathLike[str]) -> bytes:
    p = Path(path).expanduser().resolve()
    return p.read_bytes()


def _load_agents_spec_from_env() -> tuple[dict[str, Any], Path | None]:
    """
    Back-compat:
      BYTEFRAY_AGENTS_JSON='{"A":{"type":"blob","path":"agents/x/model.blob"}}'
    """
    raw = os.environ.get("BYTEFRAY_AGENTS_JSON", "").strip()
    if not raw:
        return {}, None

    try:
        spec = json.loads(raw)
    except Exception as exc:
        raise SystemExit(f"Malformed JSON in $BYTEFRAY_AGENTS_JSON: {exc}")

    if not isinstance(spec, dict):
        raise SystemExit("$BYTEFRAY_AGENTS_JSON must be a JSON object.")

    base = os.environ.get("BYTEFRAY_AGENTS_DIR", "").strip()
    base_dir = Path(base).expanduser().resolve() if base else _data_root()
    return spec, base_dir


# ----------------------------
# CLI
# ----------------------------


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="bytefray run",
        description=(
            "Bytefray engine CLI. Choose built-ins or point to discovered agents "
            "under /agents/<name>/."
        ),
    )

    # Run/replay basics
    p.add_argument("--ticks", type=int, default=3000)
    p.add_argument(
        "--replay",
        default=None,
        help=(
            "replay output path; explicit relative paths use the current working "
            "directory (default: <data-root>/runs/_loose/replay.jsonl)"
        ),
    )
    p.add_argument(
        "--trace",
        default=None,
        help=(
            "optional match trace output path; explicit relative paths use "
            "the current working directory. Omitted by default, which "
            "matches current behavior: no trace artifact is written."
        ),
    )
    p.add_argument(
        "--pygame",
        action="store_true",
        help="(deprecated/no-op) rendering moved to `bytefray replay`",
    )

    # Config overrides
    p.add_argument("--seed", type=int)
    p.add_argument("--arena", type=int)
    p.add_argument("--quota", type=_positive_int, help="instructions per agent per tick")
    p.add_argument("--alive-w", type=float)
    p.add_argument("--kill-w", type=float)
    p.add_argument("--territory-w", type=float, help="points per territory bucket")
    p.add_argument(
        "--territory-bucket",
        type=int,
        help="cells per bucket for territory scoring",
    )
    p.add_argument(
        "--win-mode",
        choices=["survival", "score", "score_fallback"],
        help="winner resolution mode at timeout",
    )
    p.add_argument(
        "--ruleset",
        choices=[
            BYTEFRAY_RULESET_ID,
            BYTEFRAY_RULESET_V2_ID,
            BYTEFRAY_RULESET_V4_ALPHA1_ID,
            BYTEFRAY_RULESET_V4_ALPHA2_ID,
            BYTEFRAY_RULESET_V4_ID,
        ],
        default=None,
        help=(
            "gameplay Ruleset identity. If omitted, Agent API v1 Python-only "
            f"matches use {BYTEFRAY_RULESET_V2_ID}, Agent API v2 Python-only "
            f"matches use {BYTEFRAY_RULESET_V4_ID}, and VM/blob matches "
            f"use {BYTEFRAY_RULESET_ID}; a mixed Python/VM match without an "
            f"explicit choice uses {BYTEFRAY_RULESET_ID}. "
            f"{BYTEFRAY_RULESET_V2_ID}, {BYTEFRAY_RULESET_V4_ID}, and both v4 "
            "alphas support Python entrants only; every v4 identity requires "
            f"Agent API v2. {BYTEFRAY_RULESET_V4_ID} is the current, permanent "
            "v4 gameplay contract and is what an omitted Ruleset selects for "
            "an Agent API v2 roster; v4 alpha1/alpha2 remain selectable by "
            "name to reproduce historical prerelease matches. Affects "
            "gameplay semantics and is recorded in the match's result/replay "
            "artifacts."
        ),
    )

    # Agent selection
    p.add_argument(
        "--a-type",
        type=str,
        default="writer",
        help="Agent name for side A (folder under /agents/<name> or builtin)",
    )
    p.add_argument(
        "--b-type",
        type=str,
        default="runner",
        help="Agent name for side B (folder under /agents/<name> or builtin)",
    )
    p.add_argument(
        "--c-type",
        type=str,
        default="",
        help="Optional agent name for side C (folder under /agents/<name> or builtin)",
    )

    # Direct blob overrides
    p.add_argument("--a-blob")
    p.add_argument("--b-blob")
    p.add_argument("--c-blob")

    p.add_argument(
        "--list-agents",
        action="store_true",
        help="List discovered agents under /agents and exit",
    )

    # Entry positions. ``None`` means the caller omitted the flag -- distinct
    # from an explicit ``0`` -- so effective placement can be resolved
    # per-Ruleset (see ``battle_engine.placement.resolve_direct_match_starts``,
    # called in ``main()`` before agents are resolved) instead of always
    # defaulting to address 0.
    p.add_argument("--a-start", type=int, default=None)
    p.add_argument("--b-start", type=int, default=None)
    p.add_argument("--c-start", type=int, default=None)

    # Per-agent schema-driven parameters (V5 Alpha 1 Phase D). Both are
    # optional and inert for an agent that declares no `parameters` section
    # in its agent.yaml -- see docs/AGENT_API_V2.md's "Parameters and
    # presets". Values are text here and are typed by the agent's own
    # declared schema, so `--a-param sweep_span_cores=2` and a JSON `2` in
    # $BYTEFRAY_AGENT_A_PARAMS_JSON resolve identically.
    for _letter in ("a", "b", "c"):
        p.add_argument(
            f"--{_letter}-param",
            action="append",
            metavar="KEY=VALUE",
            help=(
                f"override one declared parameter of agent {_letter.upper()}; "
                f"repeatable"
            ),
        )
        p.add_argument(
            f"--{_letter}-preset",
            metavar="NAME",
            help=f"select a declared parameter preset for agent {_letter.upper()}",
        )

    # Common agent params
    p.add_argument(
        "--byte",
        type=lambda x: int(x, 0),
        default="0x99",
        help="general byte value used by agents",
    )
    p.add_argument("--offset", type=int, default=128, help="writer offset from entry")
    p.add_argument("--stride", type=int, default=64, help="bomber/seeker stride")
    p.add_argument(
        "--ptr", type=int, default=512, help="initial pointer for pointer-based agents"
    )
    p.add_argument("--writes", type=int, help="flooder: writes per loop")
    p.add_argument("--step", type=int, help="spiral: fixed pointer step")
    p.add_argument(
        "--delta",
        type=int,
        help="spiral: A-register delta per loop (does not change pointer step)",
    )
    p.add_argument(
        "--target", type=lambda x: int(x, 0), help="seeker: target byte to find"
    )
    p.add_argument(
        "--attack-byte",
        type=lambda x: int(x, 0),
        help="optional alias for --byte (overrides it if provided)",
    )

    # ICWS'94 / pMARS backend flags
    p.add_argument(
        "--mode",
        choices=["native", "redcode94"],
        default="native",
        help="Engine mode: 'native' for Bytefray (default) or 'redcode94' to run pMARS.",
    )
    p.add_argument(
        "--red-a", type=str, help="Warrior A file (.red or .load) for redcode94 mode"
    )
    p.add_argument(
        "--red-b", type=str, help="Warrior B file (.red or .load) for redcode94 mode"
    )
    p.add_argument("--core-size", type=int, default=8000, help="ICWS'94 core size")
    p.add_argument("--max-cycles", type=int, default=80000, help="Max cycles per round")
    p.add_argument(
        "--max-processes", type=int, default=8000, help="Max processes per warrior"
    )
    p.add_argument("--max-len", type=int, default=100, help="Max warrior length")
    p.add_argument(
        "--min-dist",
        type=int,
        default=100,
        help="Minimum initial distance between warriors",
    )
    p.add_argument("--rounds", type=int, default=1, help="Number of rounds to run")

    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv)


# ----------------------------
# Agent Resolution
# ----------------------------


def _resolve_agent(
    letter: str,
    spec: dict[str, Any],
    spec_dir: Path | None,
    args: argparse.Namespace,
    cfg: Config,
    common_kwargs: dict[str, Any],
) -> tuple[bytes | None, str, int, Any | None]:
    """
    Resolve an agent for slot A/B/C.

    Precedence:
      1) BYTEFRAY_AGENTS_JSON
      2) --a-blob / --b-blob / --c-blob
      3) discovered agent under /agents
      4) built-in by name
    """
    del cfg  # currently unused here, kept for compatibility
    start = getattr(args, f"{letter.lower()}_start")

    # 1) env agents spec
    if spec and letter in spec:
        s = spec[letter]
        ttype = s.get("type")

        if ttype == "blob":
            path = s["path"]
            if spec_dir is not None and not os.path.isabs(path):
                path = str((spec_dir / path).resolve())
            code = read_blob(path)
            name = s.get("name") or f"{letter}_blob"
            return code, name, start, None

        if ttype == "builtin":
            agent_id = s["id"]
            code = build_agent(agent_id, start, **common_kwargs)
            return code, agent_id, start, None

        print(f"ERROR: unknown agent type for {letter}: {ttype}", file=sys.stderr)
        sys.exit(2)

    # 2) direct blob flag
    blob = getattr(args, f"{letter.lower()}_blob")
    if blob:
        code = read_blob(blob)
        return code, f"{letter}_blob", start, None

    # 3) discovery agent
    agent_name = getattr(args, f"{letter.lower()}_type")
    if not agent_name:
        return None, "", start, None

    root = _data_root()

    try:
        spec_obj = resolve_agent(root, agent_name)
    except AgentValidationError as exc:
        raise SystemExit(str(exc)) from exc
    except SystemExit:
        spec_obj = None

    if spec_obj is not None:
        side_env = _parameter_overrides(letter, args)

        if spec_obj.kind == "python":
            # A Python entrant's parameters are resolved against its declared
            # schema in `main` (`_resolve_entrant_parameters`) and travel on
            # the MatchEntrant, because only the schema can say what
            # `sweep_span_cores=2` means. The VM branches below keep their
            # historical free-form kwargs path unchanged.
            return None, agent_name, start, spec_obj

        env_blob = side_env.get("blob_path")
        blob_path: Path | None
        if isinstance(env_blob, str) and env_blob:
            blob_path = Path(env_blob).expanduser()
            if not blob_path.is_absolute():
                blob_path = (root / blob_path).resolve()
            else:
                blob_path = blob_path.resolve()
        else:
            blob_path = spec_obj.blob

        # Manifest-only starter agents may intentionally select an existing
        # built-in implementation. Other discovered agents still require code.
        if (
            not (spec_obj.dir / "agent.py").exists()
            and agent_name not in SUPPORTED
            and (blob_path is None or not blob_path.exists())
        ):
            raise SystemExit(
                f"No blob specified for agent '{agent_name}'. "
                f"Provide model.blob in agents/{agent_name}/ or pass via env JSON "
                f"key 'blob_path' in $BYTEFRAY_AGENT_{letter}_PARAMS_JSON or use "
                f"--{letter.lower()}-blob."
            )

        if blob_path is not None and blob_path.exists():
            code = read_blob(str(blob_path))
            return code, agent_name, start, None

    # 4) built-in fallback
    if agent_name in SUPPORTED:
        side_env = _parameter_overrides(letter, args)
        code = build_agent(agent_name, start, **_merge_params(common_kwargs, side_env))
        return code, agent_name, start, None

    print(
        f"ERROR: Unknown agent '{agent_name}'. "
        f"Expected a built-in ({', '.join(SUPPORTED)}) or a folder "
        f"{root / 'agents' / agent_name} with agent.yaml (JSON) or agent.py",
        file=sys.stderr,
    )
    sys.exit(2)


def _requested_entrant_metadata(
    letter: str, spec: dict[str, Any], args: argparse.Namespace, root: Path
) -> dict[str, Any] | None:
    """Determine slot ``letter``'s compatibility metadata without building it.

    Mirrors ``_resolve_agent``'s own precedence chain (env-JSON spec, direct
    blob flag, discovery, built-in fallback) exactly, minus anything that
    requires a resolved start address -- so the omitted-Ruleset default
    (which start-address *placement* itself depends on, via
    ``resolve_direct_match_starts``) can be computed before any agent is
    built. Returns ``None`` when the slot has no requested entrant at all
    (mirrors ``_resolve_agent``'s own "not requested" case for an omitted
    ``--c-type``); every other outcome errors identically to
    ``_resolve_agent`` once agent construction actually runs, so a wrong
    guess here can never let an invalid invocation execute -- it can only
    affect which Ruleset an already-valid invocation defaults to.

    Reports both authoritative compatibility fields (``kind`` and, for a
    discovered Python agent, its declared ``api_version``) rather than the
    runtime kind alone: ``bytefray-rules-2`` and ``bytefray-rules-4-alpha1``
    are both Python-only and are told apart by Agent API version, so the
    kind by itself can no longer choose between them.
    """
    if spec and letter in spec:
        return {"kind": "vm", "api_version": None}  # env-JSON entrants are blob/builtin.

    if getattr(args, f"{letter.lower()}_blob"):
        return {"kind": "vm", "api_version": None}

    agent_name = getattr(args, f"{letter.lower()}_type")
    if not agent_name:
        return None

    try:
        spec_obj = resolve_agent(root, agent_name)
    except (AgentValidationError, SystemExit):
        spec_obj = None

    if spec_obj is not None and spec_obj.kind == "python":
        return {
            "agent_id": agent_name,
            "kind": "python",
            "api_version": spec_obj.api_version,
        }
    return {"agent_id": agent_name, "kind": "vm", "api_version": None}


# ----------------------------
# Main
# ----------------------------


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if getattr(args, "list_agents", False):
        root = _data_root()
        try:
            bootstrap = ensure_starter_agents(data_root=root)
        except (FileNotFoundError, OSError) as exc:
            print(f"ERROR: Could not initialize starter agents: {exc}", file=sys.stderr)
            return 2
        warning = describe_bootstrap_errors(bootstrap)
        if warning:
            print(f"WARNING: {warning}", file=sys.stderr)
        # Reported on the discovery command rather than on every match: a
        # customized starter is a standing condition, so `bytefray run` would
        # repeat it forever, while listing agents is exactly where a user is
        # asking what their catalog contains (V5 Alpha 1 Phase E0).
        refresh = describe_starter_refresh(bootstrap)
        if refresh:
            print(f"NOTE: {refresh}", file=sys.stderr)
        try:
            specs = discover_agents(root)
        except AgentValidationError as exc:
            print(f"ERROR: Could not discover agents: {exc}", file=sys.stderr)
            return 2
        if not specs:
            print(f"No agents found under {root / 'agents'}")
            return 0

        print("Discovered agents:")
        for name, spec in sorted(specs.items()):
            disp = f"{spec.display}" if spec.display and spec.display != name else ""
            # ASCII "none", not an em-dash: the frozen PyInstaller
            # bytefray.exe mangles non-ASCII on stdout where the source
            # build renders it correctly, so the shipped product showed a
            # replacement character here. "none" also matches the CLI's own
            # existing vocabulary for an absent path (`agents test` prints
            # `result: none` / `replay: none`).
            blob = spec.blob.name if spec.blob else "none"
            print(f" - {name:20} {disp:20} {agent_runtime_label(spec):8} blob={blob}")
        print(
            "\n[Python] agents run under Ruleset v1 or v2 with Agent API v1; "
            "Ruleset v4 alpha1 uses Agent API v2."
            "\n[VM] agents run under Ruleset v1 only."
        )
        return 0

    # Build current Config correctly against Config.weights
    cfg_kwargs: dict[str, Any] = {}
    if args.seed is not None:
        cfg_kwargs["seed"] = args.seed
    if args.arena is not None:
        cfg_kwargs["arena_size"] = args.arena
    if args.win_mode:
        cfg_kwargs["win_mode"] = args.win_mode
    if args.quota is not None:
        cfg_kwargs["instr_per_tick"] = args.quota

    cfg = Config(**cfg_kwargs)

    # Preserve defaults unless caller overrides them.
    cfg.weights = Weights(
        alive=args.alive_w if args.alive_w is not None else cfg.weights.alive,
        kill=args.kill_w if args.kill_w is not None else cfg.weights.kill,
        territory=(
            args.territory_w if args.territory_w is not None else cfg.weights.territory
        ),
        territory_bucket=(
            args.territory_bucket
            if args.territory_bucket is not None
            else cfg.weights.territory_bucket
        ),
    )

    replay_path = _resolve_replay_path(args.replay)
    summary_path = replay_path.with_name("summary.json")
    trace_path = _resolve_trace_path(args.trace)

    if args.mode == "redcode94":
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        if not args.red_a or not args.red_b:
            print("redcode94 mode requires --red-a and --red-b", file=sys.stderr)
            return 2

        a_path = Path(args.red_a)
        b_path = Path(args.red_b)

        if not a_path.exists() or not b_path.exists():
            missing = a_path if not a_path.exists() else b_path
            print(f"Warrior file missing: {missing}", file=sys.stderr)
            return 2

        # Redcode mode currently produces a summary but no canonical replay.
        # Remove an artifact from an earlier invocation before starting pMARS.
        replay_path.unlink(missing_ok=True)
        summary_path.with_name("result.json").unlink(missing_ok=True)
        try:
            result = run_pmars(
                _pmars_arguments(
                    a_path,
                    b_path,
                    core_size=args.core_size,
                    max_cycles=args.max_cycles,
                    max_processes=args.max_processes,
                    max_len=args.max_len,
                    min_dist=args.min_dist,
                    rounds=args.rounds,
                )
            )
        except PMarsError as exc:
            replay_path.unlink(missing_ok=True)
            summary_path.unlink(missing_ok=True)
            summary_path.with_name("result.json").unlink(missing_ok=True)
            print(f"pMARS error: {exc}", file=sys.stderr)
            return exc.exit_code

        summary = {
            "version": 2,
            "mode": "redcode94",
            "ticks": args.max_cycles,
            "winner": result.winner,
            "A_score": None,
            "B_score": None,
            "A_alive_ticks": None,
            "B_alive_ticks": None,
            "A_territory": None,
            "B_territory": None,
            "params": {
                "core_size": args.core_size,
                "max_cycles": args.max_cycles,
                "max_processes": args.max_processes,
                "max_len": args.max_len,
                "min_dist": args.min_dist,
                "rounds": args.rounds,
            },
            "agents": {"A": str(a_path), "B": str(b_path)},
            "backend": {
                "cmd": list(result.command),
                "returncode": result.returncode,
            },
        }

        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        reproducibility = {
            **summary["params"],
            "entrants": [
                {
                    "agent_id": "A",
                    "source_sha256": hashlib.sha256(a_path.read_bytes()).hexdigest(),
                },
                {
                    "agent_id": "B",
                    "source_sha256": hashlib.sha256(b_path.read_bytes()).hexdigest(),
                },
            ],
        }
        match_id = stable_id("match", {"mode": "redcode94", **reproducibility})
        result_id = stable_id("result", {"match_id": match_id, "winner": result.winner})
        envelope = ResultEnvelope(
            result_id=result_id,
            match_id=match_id,
            mode="redcode94",
            winner=result.winner,
            termination_reason="backend_completed",
            ticks=args.max_cycles,
            entrants=tuple(reproducibility["entrants"]),
            reproducibility=reproducibility,
            replay=None,
            backend={"name": "pMARS", "returncode": result.returncode},
            # Phase 7A changes native result metadata only. Preserve the
            # established pMARS/Redcode result contract and behavior.
            schema_version=RESULT_SCHEMA_VERSION_V1,
        )
        write_json_atomic(summary_path.with_name("result.json"), envelope.as_dict())

        if not args.quiet:
            print(
                f"Winner: {summary['winner']}; "
                f"result: {summary_path.with_name('result.json')}; "
                f"summary: {summary_path}; replay: none"
            )
        return 0

    byte = args.byte
    if args.attack_byte is not None:
        byte = args.attack_byte

    common_kwargs = {
        "byte": byte,
        "offset": args.offset,
        "stride": args.stride,
        "ptr": args.ptr,
        "writes": args.writes,
        "step": args.step,
        "delta": args.delta,
        "target": args.target,
    }
    common_kwargs = {
        key: value for key, value in common_kwargs.items() if value is not None
    }

    env_spec, spec_dir = _load_agents_spec_from_env()
    root = _data_root()

    # A direct match is a valid first command in a fresh installation.  Seed
    # the bundled catalog here as well as in ``bytefray agents`` and the
    # Designer so packaged Python starters resolve without requiring a
    # discovery command to have run first.  The copy is deliberately
    # non-destructive: existing user files always win.
    try:
        bootstrap = ensure_starter_agents(data_root=root)
    except (FileNotFoundError, OSError) as exc:
        print(f"ERROR: Could not initialize starter agents: {exc}", file=sys.stderr)
        return 2
    warning = describe_bootstrap_errors(bootstrap)
    if warning:
        print(f"WARNING: {warning}", file=sys.stderr)

    # Resolve effective start addresses once, before any agent is built --
    # builtin construction bakes ``start`` into the agent's own bytecode
    # (``build_agent``), so the resolved value must be in place before
    # ``_resolve_agent`` runs, not applied to its return value after the
    # fact. ``args.c_start`` only participates when a C entrant was actually
    # requested; an unused, un-omitted ``--c-start`` is otherwise inert (C
    # never becomes a match entrant) and is left as the caller supplied it.
    c_requested = bool(args.c_type) or bool(args.c_blob) or ("C" in env_spec)
    entrant_count = 3 if c_requested else 2
    supplied_starts = [args.a_start, args.b_start]
    if c_requested:
        supplied_starts.append(args.c_start)

    # RC1 default-Ruleset-defect fix: resolve an omitted --ruleset from the
    # requested entrants' runtime kinds -- known here without building any
    # agent's bytecode (see _requested_entrant_metadata) -- before it is used
    # for placement or match execution, so both honor the exact same
    # resolved identity every downstream artifact records. An explicit
    # --ruleset is returned unchanged.
    requested_entrants = [
        metadata
        for metadata in (
            _requested_entrant_metadata("A", env_spec, args, root),
            _requested_entrant_metadata("B", env_spec, args, root),
            _requested_entrant_metadata("C", env_spec, args, root) if c_requested else None,
        )
        if metadata is not None
    ]
    try:
        resolved_ruleset_id = resolve_omitted_ruleset_for_agents(
            args.ruleset, requested_entrants
        )
    except NoCompatibleRulesetError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    resolved_starts = resolve_direct_match_starts(
        ruleset_id=resolved_ruleset_id,
        arena_size=cfg.arena_size,
        entrant_count=entrant_count,
        supplied_starts=supplied_starts,
        # The same seed this match actually runs under, so a v4 alpha2
        # match's seed-derived core placement is reproducible from nothing
        # but its recorded inputs. Inert for every other Ruleset.
        seed=cfg.seed,
    )
    args.a_start, args.b_start = resolved_starts[0], resolved_starts[1]
    if c_requested:
        args.c_start = resolved_starts[2]
    elif args.c_start is None:
        args.c_start = 0

    codeA, nameA, startA, pythonA = _resolve_agent(
        "A", env_spec, spec_dir, args, cfg, common_kwargs
    )
    codeB, nameB, startB, pythonB = _resolve_agent(
        "B", env_spec, spec_dir, args, cfg, common_kwargs
    )
    codeC, nameC, startC, pythonC = _resolve_agent(
        "C", env_spec, spec_dir, args, cfg, common_kwargs
    )

    # A Python entrant's parameters are resolved here, before any agent
    # module is imported: an unknown key, an out-of-range value or an unknown
    # preset must fail the invocation rather than the match. Empty for every
    # agent that declares no schema and is given no overrides.
    paramsA = _resolve_entrant_parameters("A", pythonA, args) if pythonA else {}
    paramsB = _resolve_entrant_parameters("B", pythonB, args) if pythonB else {}
    paramsC = _resolve_entrant_parameters("C", pythonC, args) if pythonC else {}

    try:
        resolved_preview = {"A": paramsA, "B": paramsB, "C": paramsC}

        def preview(letter: str, name: str) -> str:
            # For a Python entrant this reports the values that were actually
            # resolved and will actually reach the agent. For a VM entrant it
            # reports the free-form kwargs its program is built from, which is
            # the only parameter notion that path has ever had.
            resolved = resolved_preview[letter]
            if resolved:
                return " ".join(
                    f"{key}={resolved[key]!r}" for key in resolved
                )
            return _keys_preview(_parameter_overrides(letter, args))

        print("Agents:")
        print(f" A: {nameA} params={preview('A', nameA)}")
        print(f" B: {nameB} params={preview('B', nameB)}")
        if nameC:
            print(f" C: {nameC} params={preview('C', nameC)}")
    except Exception:
        pass

    if (codeA is None and pythonA is None) or (codeB is None and pythonB is None):
        print(
            "ERROR: agents A and B must be executable built-in, blob, or Python agents",
            file=sys.stderr,
        )
        return 2

    # Agent validation above must complete before this owned output is opened;
    # otherwise an invalid invocation could truncate an existing replay.
    entrants = [
        (
            MatchEntrant.python("A", nameA, startA, pythonA, paramsA)
            if pythonA is not None
            else MatchEntrant("A", nameA, startA, codeA)
        ),
        (
            MatchEntrant.python("B", nameB, startB, pythonB, paramsB)
            if pythonB is not None
            else MatchEntrant("B", nameB, startB, codeB)
        ),
    ]
    if nameC and (codeC is not None or pythonC is not None):
        entrants.append(
            MatchEntrant.python("C", nameC, startC, pythonC, paramsC)
            if pythonC is not None
            else MatchEntrant("C", nameC, startC, codeC)
        )
    try:
        match_result = NativeMatchService().run(
            MatchRequest(
                config=cfg,
                entrants=tuple(entrants),
                max_ticks=args.ticks,
                replay_path=replay_path,
                verbose=not args.quiet,
                trace_path=trace_path,
                ruleset_id=resolved_ruleset_id,
            )
        )
    except (
        UnsupportedMatchCompositionError,
        RulesetRuntimeUnsupportedError,
        RulesetAgentUnsupportedError,
        OverlappingCoreError,
        PythonEntrantInitializationError,
        PythonMatchExecutionError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    agent_stats = {
        agent.agent_id: agent.as_legacy_statistics() for agent in match_result.agents
    }
    score_map = dict(match_result.score)
    effective_winner = match_result.winner

    summary = {
        "version": 2,
        "mode": "b2",
        "seed": getattr(cfg, "seed", None),
        "ticks": match_result.ticks_run,
        "winner": effective_winner,
        "A_score": score_map.get("A", 0),
        "B_score": score_map.get("B", 0),
        "A_alive_ticks": agent_stats.get("A", {}).get("alive_ticks", 0),
        "B_alive_ticks": agent_stats.get("B", {}).get("alive_ticks", 0),
        "A_territory": agent_stats.get("A", {}).get("territory_last", 0),
        "B_territory": agent_stats.get("B", {}).get("territory_last", 0),
        "params": {
            "arena": cfg.arena_size,
            "ticks_requested": args.ticks,
            "ticks_run": match_result.ticks_run,
            "win_mode": cfg.win_mode,
            "alive_w": cfg.weights.alive,
            "kill_w": cfg.weights.kill,
            "territory_w": cfg.weights.territory,
            "territory_bucket": cfg.weights.territory_bucket,
            "ruleset_id": resolved_ruleset_id,
        },
        "agents": {
            "A": nameA,
            "B": nameB,
            **({"C": nameC} if nameC else {}),
        },
        "score": score_map,
        "agent_stats": agent_stats,
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if not args.quiet:
        print(
            f"Winner: {effective_winner}; "
            f"ruleset: {resolved_ruleset_id}; "
            f"result: {match_result.result_path}; "
            f"replay: {replay_path}; "
            f"summary: {summary_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
