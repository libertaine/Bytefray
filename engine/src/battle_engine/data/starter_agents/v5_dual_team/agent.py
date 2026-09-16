"""Bytefray V5 starter -- Dual Team (two processes, two jobs).

THE LESSON: an Agent API v2 entrant is a team, not a single robot.

``declare_processes`` may return more than one process.  Each gets its own
anchor and its own reach, and the shares say how the entrant's eight
actions per tick are split between them.  Every process is served by the
same ``act`` method on the same object, so:

* ``observation.self_process_id`` is how you tell which one is asking; and
* ordinary attributes on ``self`` are shared memory between them.

This agent uses both facts.  The ``raider`` goes out and fights, the
``keeper`` stays home and holds the core, and whichever of them sees the
opponent first writes that sighting into one shared memory the other can
use.  That is real cooperation in about a dozen lines, and it is the whole
point of the example.

WHAT THIS AGENT IS ALLOWED TO KNOW
    Only ``ObservationV2``: the shared contact memory is built from the
    ordinary ``visible_enemy_anchor_addresses`` sensor channel, and the
    keeper defends using OUR OWN ``own_core_base``/``own_core_size``.  No
    enemy core address is available to any process, and none is assumed.

READ THIS ONE AFTER THE OTHER THREE
    ``v5_region_attacker``, ``v5_scout_striker`` and ``v5_core_defender``
    each do one job with one process.  This one is the smallest example
    that combines two of them; ``v4_quorum`` is the advanced six-process
    version and is much harder to read.

ITS ONE PARAMETER
    ``agent.yaml`` declares ``raider_share``, and the engine hands its
    resolved value to ``reset`` on ``context.parameters``.  The keeper takes
    whatever is left, so the two shares still total exactly 1.0 whatever
    the parameter says -- which is the point.  How you divide a fixed quota
    between roles is the decision this whole example exists to show, so it
    is the thing worth making adjustable.  See docs/AGENT_API_V2.md.
"""

from battle_engine.agent_api import (
    ActionKindV2,
    AgentAction,
    MatchContextV2,
    ObservationV2,
    ProcessDeclaration,
)

# Two roles, one quota.  The shares must be non-negative and total exactly
# 1.0, and the engine turns them into whole actions: 0.5/0.5 of the Q=8
# entrant quota gives each process four actions per tick.
RAIDER_REACH = 32
KEEPER_REACH = 12

# The raider's default slice of the quota; the keeper always gets the rest.
RAIDER_SHARE = 0.5

SIGNATURE = 0x6B

# The raider gives up on a sighting this old and goes back to searching.
CONTACT_MEMORY_TICKS = 90

MAX_MOVE_DELTA = 64


class DualTeamAgent:
    """A raider and a keeper sharing one quota and one contact memory."""

    def reset(self, context: MatchContextV2) -> None:
        self.context = context
        self.arena = context.arena_size
        self.signature = SIGNATURE
        # Already validated and coerced against the schema in agent.yaml --
        # bounded to [0.0, 1.0] there, which is what keeps the pair of
        # shares below legal without any checking in this file.  The
        # fallback is that schema's own declared default.
        self.raider_share = float(context.parameters.get("raider_share", RAIDER_SHARE))
        # Shared between both processes -- this is the cooperation channel.
        self.last_contact: int | None = None
        self.last_contact_tick = -1
        # Private cursors, one per role.
        self.raid_cursor = 0
        self.keep_cursor = 0

    def declare_processes(self) -> list[ProcessDeclaration]:
        # The keeper's share is derived rather than declared separately, so
        # the pair can never drift out of the required total of 1.0 however
        # ``raider_share`` was set.
        return [
            ProcessDeclaration(
                id="raider", reach=self._reach(RAIDER_REACH), share=self.raider_share
            ),
            ProcessDeclaration(
                id="keeper",
                reach=self._reach(KEEPER_REACH),
                share=1.0 - self.raider_share,
            ),
        ]

    def act(self, observation: ObservationV2) -> AgentAction:
        # Either process may be the one that spots the opponent, and both
        # record what they see before doing their own job.
        self._share_contact(observation)
        if observation.self_process_id == "keeper":
            return self._act_keeper(observation)
        return self._act_raider(observation)

    # -- the raider: go and fight ----------------------------------------

    def _act_raider(self, observation: ObservationV2) -> AgentAction:
        target = self._shared_contact(observation.current_tick)

        # Nobody has seen anything recently: go looking.
        if target is None:
            return AgentAction(
                kind=ActionKindV2.MOVE,
                operand=self._clamp(max(1, observation.self_reach)),
            )

        core_size = max(1, observation.own_core_size)

        # Close until the whole block is inside reach, not merely until the
        # contact is touchable -- stopping at maximum range would leave the
        # far end of the block permanently unwritable.
        if self._distance(target, observation.self_anchor) > max(
            0, observation.self_reach - core_size
        ):
            return self._move_toward(observation, target)

        # A block of consecutive addresses one core wide, starting at the
        # contact.  ``own_core_size`` is OUR core's width; an attacker is
        # never told the enemy's, so this is an assumption that both sides
        # are built alike rather than knowledge of the objective.
        for _ in range(core_size):
            address = (target + self.raid_cursor % core_size) % self.arena
            self.raid_cursor += 1
            if self._within_reach(observation, address):
                return self._claim(address)
        return self._claim(target % self.arena)

    # -- the keeper: stay home -------------------------------------------

    def _act_keeper(self, observation: ObservationV2) -> AgentAction:
        core_size = max(1, observation.own_core_size)
        base = observation.own_core_base % self.arena
        station = (base + core_size // 2) % self.arena

        # Both processes start at the core base, which is one end of the
        # core.  The keeper's first job is to walk to the middle, where
        # every cell of the core is inside KEEPER_REACH.
        if observation.self_anchor != station:
            return self._move_toward(observation, station)

        # An enemy standing on our ground gets disrupted first.
        for address in sorted(set(observation.visible_enemy_anchor_addresses)):
            if self._within_reach(observation, address):
                return self._claim(address)

        # Otherwise rewrite our own core cells in rotation.  The keeper
        # never READs, so unlike ``v5_core_defender`` it cannot tell a cell
        # it still owns from one it has lost -- it simply refreshes all of
        # them.  Cheaper, less informed, and a useful contrast.
        for _ in range(core_size):
            address = (base + self.keep_cursor % core_size) % self.arena
            self.keep_cursor += 1
            if self._within_reach(observation, address):
                return self._claim(address)
        return self._move_toward(observation, station)

    # -- shared contact memory -------------------------------------------

    def _share_contact(self, observation: ObservationV2) -> None:
        visible = observation.visible_enemy_anchor_addresses
        if not visible:
            return
        self.last_contact = min(
            visible, key=lambda a: (self._distance(a, observation.self_anchor), a)
        )
        self.last_contact_tick = observation.current_tick

    def _shared_contact(self, tick: int) -> int | None:
        if self.last_contact is None:
            return None
        if tick - self.last_contact_tick > CONTACT_MEMORY_TICKS:
            return None
        return self.last_contact

    # -- geometry --------------------------------------------------------

    def _claim(self, address: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.WRITE, operand=address, value=self.signature
        )

    def _move_toward(self, observation: ObservationV2, target: int) -> AgentAction:
        return AgentAction(
            kind=ActionKindV2.MOVE,
            operand=self._clamp(self._shortest_delta(target, observation.self_anchor)),
        )

    def _within_reach(self, observation: ObservationV2, address: int) -> bool:
        return self._distance(observation.self_anchor, address) <= observation.self_reach

    def _distance(self, a: int, b: int) -> int:
        delta = abs((a - b) % self.arena)
        return min(delta, self.arena - delta)

    def _shortest_delta(self, target: int, anchor: int) -> int:
        forward = (target - anchor) % self.arena
        backward = forward - self.arena
        return backward if abs(backward) < abs(forward) else forward

    def _reach(self, desired: int) -> int:
        return max(1, min(desired, self.arena - 1))

    @staticmethod
    def _clamp(delta: int) -> int:
        return max(-MAX_MOVE_DELTA, min(MAX_MOVE_DELTA, delta))


def create_agent() -> DualTeamAgent:
    return DualTeamAgent()
