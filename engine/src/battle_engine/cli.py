import argparse
import json
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from battle_engine.agent_api import AgentValidationError
from battle_engine.agent_parameters import EMPTY_PARAMETER_SCHEMA, resolve_parameters
from battle_engine.agents import agent_runtime_label, discover_agents, resolve_agent
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
from battle_engine.python_runtime import PythonEntrantInitializationError
from battle_engine.ruleset_policy import (
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
        choices=[BYTEFRAY_RULESET_V4_ID],
        default=None,
        help=(
            f"gameplay Ruleset identity. {BYTEFRAY_RULESET_V4_ID} is the "
            "only Ruleset Agent API v2 (process) agents can run under, and "
            "is selected automatically when this flag is omitted. Affects "
            "gameplay semantics and is recorded in the match's result/replay "
            "artifacts."
        ),
    )

    # Agent selection
    p.add_argument(
        "--a-type",
        type=str,
        default="v4_claimer",
        help="Agent name for side A (folder under /agents/<name>)",
    )
    p.add_argument(
        "--b-type",
        type=str,
        default="v4_scout",
        help="Agent name for side B (folder under /agents/<name>)",
    )
    p.add_argument(
        "--c-type",
        type=str,
        default="",
        help="Optional agent name for side C (folder under /agents/<name>)",
    )

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

    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv)


# ----------------------------
# Agent Resolution
# ----------------------------


def _resolve_agent(
    letter: str,
    args: argparse.Namespace,
) -> tuple[str, int, Any | None]:
    """Resolve a discovered Python agent for slot A/B/C.

    V6 Phase 2B.12 retired VM/blob execution: the only remaining resolution
    path is discovery by name under ``/agents``, and every match entrant is
    a Python (Agent API v2) agent. ``start`` is read from ``args`` rather
    than computed here -- ``main()`` resolves every slot's effective start
    address up front via ``resolve_direct_match_starts`` before any agent is
    looked up.
    """
    start = getattr(args, f"{letter.lower()}_start")
    agent_name = getattr(args, f"{letter.lower()}_type")
    if not agent_name:
        return "", start, None

    root = _data_root()
    try:
        spec_obj = resolve_agent(root, agent_name)
    except AgentValidationError as exc:
        raise SystemExit(str(exc)) from exc
    except SystemExit:
        spec_obj = None

    if spec_obj is None or spec_obj.kind != "python":
        print(
            f"ERROR: Unknown agent '{agent_name}'. Expected a discovered "
            f"Python agent under {root / 'agents' / agent_name} with "
            "agent.yaml and agent.py.",
            file=sys.stderr,
        )
        sys.exit(2)

    return agent_name, start, spec_obj


def _requested_entrant_metadata(
    letter: str, args: argparse.Namespace, root: Path
) -> dict[str, Any] | None:
    """Determine slot ``letter``'s compatibility metadata without building it.

    Mirrors ``_resolve_agent``'s own discovery lookup, minus anything that
    requires a resolved start address -- so the omitted-Ruleset default
    (which start-address *placement* itself depends on, via
    ``resolve_direct_match_starts``) can be computed before any agent is
    built. Returns ``None`` when the slot has no requested entrant at all
    (mirrors ``_resolve_agent``'s own "not requested" case for an omitted
    ``--c-type``); every other outcome errors identically to
    ``_resolve_agent`` once agent construction actually runs, so a wrong
    guess here can never let an invalid invocation execute -- it can only
    affect which Ruleset an already-valid invocation defaults to.
    """
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
    # An unresolvable name is projected as a current Agent API v2 entrant so
    # ruleset resolution succeeds and control reaches `_resolve_agent`, which
    # raises the specific "Unknown agent" diagnostic -- never a generic
    # ruleset-compatibility error for what is really a typo.
    return {"agent_id": agent_name, "kind": "python", "api_version": 2}


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
        print("\n[Python] agents run under bytefray-rules-4 with Agent API v2.")
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

    # Resolve effective start addresses once, before any agent is built.
    # ``args.c_start`` only participates when a C entrant was actually
    # requested; an unused, un-omitted ``--c-start`` is otherwise inert (C
    # never becomes a match entrant) and is left as the caller supplied it.
    c_requested = bool(args.c_type)
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
            _requested_entrant_metadata("A", args, root),
            _requested_entrant_metadata("B", args, root),
            _requested_entrant_metadata("C", args, root) if c_requested else None,
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

    nameA, startA, pythonA = _resolve_agent("A", args)
    nameB, startB, pythonB = _resolve_agent("B", args)
    nameC, startC, pythonC = _resolve_agent("C", args)

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
            # Reports the values that were actually resolved and will
            # actually reach the agent.
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

    if pythonA is None or pythonB is None:
        print(
            "ERROR: agents A and B must be discovered Python agents",
            file=sys.stderr,
        )
        return 2

    # Agent validation above must complete before this owned output is opened;
    # otherwise an invalid invocation could truncate an existing replay.
    entrants = [
        MatchEntrant.python("A", nameA, startA, pythonA, paramsA),
        MatchEntrant.python("B", nameB, startB, pythonB, paramsB),
    ]
    if nameC and pythonC is not None:
        entrants.append(MatchEntrant.python("C", nameC, startC, pythonC, paramsC))
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
