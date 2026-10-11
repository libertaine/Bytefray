"""Pygame sensing replay: filtered entrant drawing and explicit omniscience.

No ReplaySession, reconstruction facts, analysis cache or operator report is
passed into draw_entrant. Each redraw starts from a blank surface.
"""

from __future__ import annotations

import math
import textwrap
from typing import Any

from battle_client.renderers.base import RendererDependencyError
from battle_client.sensing import OmniscientView, SensingView
from battle_client.sensing_presentation import SensingMarker, SensingPresentation, entrant_scene


class SensingReplayRenderer:
    def __init__(self) -> None:
        self.pg: Any = None
        self.screen: Any = None
        self.font: Any = None
        self.help_visible = False
        self.scrubbing = False
        self.scroll_offset = 0
        self.last_lines: tuple[str, ...] = ()
        self.last_markers: tuple[SensingMarker, ...] = ()
        self._arena_rect = (20, 150, 600, 300)
        self._timeline_rect = (20, 650, 1060, 20)

    def run(
        self, presentation: SensingPresentation, *, start_tick: int | None,
        start_paused: bool, initial_speed: float | None, initial_perspective: str | None,
    ) -> None:
        try:
            import pygame
        except ImportError as exc:
            raise RendererDependencyError("Pygame not available. Install the replay extra.") from exc
        self.pg = pygame
        pygame.init()
        try:
            self.screen = pygame.display.set_mode((1100, 750), pygame.RESIZABLE)
            pygame.display.set_caption("Bytefray — Experimental sensing replay")
            self.font = pygame.font.SysFont("consolas", 15)
            if initial_speed is not None:
                presentation.controller.set_speed(initial_speed)
            if initial_perspective in {"broadcast", "omniscient"}:
                presentation.switch(False)
            if start_tick is not None:
                presentation.seek_relative(start_tick - presentation.position.tick)
            if not start_paused and not presentation.at_end:
                presentation.controller.play()
            clock = pygame.time.Clock()
            running = True
            while running:
                elapsed = clock.tick(60) / 1000
                for event in pygame.event.get():
                    if not self.handle_event(event, presentation):
                        running = False
                        break
                if not running:
                    break
                if self.scrubbing:
                    self.seek_from_mouse(pygame.mouse.get_pos(), presentation)
                presentation.controller.update(elapsed)
                self.draw(presentation)
                pygame.display.flip()
        finally:
            pygame.quit()

    def handle_event(self, event: Any, presentation: SensingPresentation) -> bool:
        pg = self.pg
        if event.type == pg.QUIT:
            return False
        if event.type == pg.KEYDOWN:
            from battle_client.renderers.pygame_renderer import dispatch_key

            action = dispatch_key(pg, event.key, event.mod, presentation)
            if action.quit_requested:
                return False
            if action.cycle_perspective:
                presentation.switch(not isinstance(presentation.current_view, SensingView))
                self.scroll_offset = 0
            if action.select_perspective_index in {0, 1}:
                presentation.switch(action.select_perspective_index == 1)
                self.scroll_offset = 0
            if action.toggle_help:
                self.help_visible = not self.help_visible
        elif event.type == pg.VIDEORESIZE:
            self.screen = pg.display.set_mode((max(900, event.w), max(650, event.h)), pg.RESIZABLE)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if 55 <= event.pos[1] <= 90:
                if 20 <= event.pos[0] <= 390:
                    presentation.switch(True)
                    self.scroll_offset = 0
                elif 410 <= event.pos[0] <= 810:
                    presentation.switch(False)
                    self.scroll_offset = 0
            elif self.seek_from_mouse(event.pos, presentation):
                self.scrubbing = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.scrubbing = False
        elif event.type == pg.MOUSEWHEEL:
            self.scroll_offset = max(0, self.scroll_offset - event.y * 3)
        return True

    def seek_from_mouse(self, pos: tuple[int, int], presentation: SensingPresentation) -> bool:
        x, y, width, height = self._timeline_rect
        if not self.scrubbing and not (x <= pos[0] <= x + width and y <= pos[1] <= y + height):
            return False
        fraction = max(0.0, min(1.0, (pos[0] - x) / width))
        presentation.seek_index(round(fraction * (len(presentation.controller.positions) - 1)))
        return True

    def text(self, value: str, x: int, y: int) -> None:
        self.screen.blit(self.font.render(value, True, (240, 240, 240)), (x, y))

    def point(self, address: int, arena_size: int) -> tuple[int, int]:
        cols = min(32, arena_size)
        rows = math.ceil(arena_size / cols)
        x, y, width, height = self._arena_rect
        return (x + int((address % cols + .5) * width / cols), y + int((address // cols + .5) * height / rows))

    def draw(self, presentation: SensingPresentation) -> None:
        # Control plane supplies one approved payload, never the canonical session.
        self.screen.fill((14, 17, 22))
        width, height = self.screen.get_size()
        self._arena_rect = (20, 160, int(width * .55), min(320, height - 310))
        self._timeline_rect = (20, height - 90, width - 40, 20)
        view = presentation.current_view
        if isinstance(view, SensingView):
            self.draw_entrant(view)
        else:
            self.draw_omniscient(view)
            report = presentation.verification
            self.text(
                f"Operator verification: artifact consistency={report.artifact_pair_consistent}; "
                f"independent reconstruction={report.exchange_reconstructed}", 20, height - 175,
            )
            self.text(
                f"Teaching exchange complete={report.teaching_complete}; "
                f"filtered perspective available={report.knowledge_projected}; "
                f"demo sidecar verified={presentation.sidecar_verified}", 20, height - 155,
            )
            self.text(presentation.notice, 20, height - 135)
        self.pg.draw.rect(self.screen, (160, 160, 160), (20, 55, 370, 35), 1)
        self.pg.draw.rect(self.screen, (160, 160, 160), (410, 55, 400, 35), 1)
        self.text("2: Agent A — delivered information", 28, 64)
        self.text("1: Omniscient — full world state", 418, 64)
        x, y, track_width, track_height = self._timeline_rect
        self.pg.draw.rect(self.screen, (110, 110, 110), self._timeline_rect, 1)
        fraction = presentation.index / max(1, len(presentation.controller.positions) - 1)
        playhead = x + round(fraction * track_width)
        self.pg.draw.line(self.screen, (255, 255, 255), (playhead, y), (playhead, y + track_height), 3)
        playing = "Playing" if presentation.controller.playing else "Paused"
        self.text(f"{playing} / {presentation.speed:g}x — Space: play/pause; arrows: phase step; Shift+arrows: 10 ticks", 20, height - 58)
        self.text("Home: restart; End: recorded end; +/-: speed; V/P: perspective; drag bar: phase seek; ?: help", 20, height - 34)
        if presentation.terminal_text is not None:
            self.text(presentation.terminal_text, 20, height - 120)
        if self.help_visible:
            self.text("Scan ring = request; + = receipt; diamond = historical sample; arrow = MOVE; X = recorded WRITE", 20, 112)

    def draw_entrant(self, view: SensingView) -> None:
        """The entire entrant drawing boundary accepts only a filtered view."""
        scene = entrant_scene(view)
        self.last_lines, self.last_markers = scene.lines, scene.markers
        self.text(scene.label, 20, 16)
        self.text(scene.phase, 20, 38)
        self.pg.draw.rect(self.screen, (50, 55, 65), self._arena_rect)
        self.text("? Unknown arena; markers are delivered facts only", 20, 140)
        if view.own_core_base is not None and view.own_core_size is not None:
            for offset in range(view.own_core_size):
                point = self.point((view.own_core_base + offset) % view.arena_size, view.arena_size)
                self.pg.draw.rect(self.screen, (230, 230, 230), (*point, 5, 5), 1)
        for marker in scene.markers:
            self.draw_marker(marker, view.arena_size)
        x = self._arena_rect[0] + self._arena_rect[2] + 22
        chars = max(24, (self.screen.get_width() - x - 15) // 9)
        y = 140
        wrapped_lines = [wrapped for line in scene.lines for wrapped in textwrap.wrap(line, width=chars)]
        visible_count = max(1, (self.screen.get_height() - 155 - y) // 19)
        self.scroll_offset = min(self.scroll_offset, max(0, len(wrapped_lines) - visible_count))
        self.text("Wheel: scroll delivered history", x, 112)
        for wrapped in wrapped_lines[self.scroll_offset:self.scroll_offset + visible_count]:
            self.text(wrapped, x, y)
            y += 19
        self.text("Historical samples stay at their recorded address; they do not track opponents.", 20, self._arena_rect[1] + self._arena_rect[3] + 20)

    def draw_marker(self, marker: SensingMarker, arena_size: int) -> None:
        pg = self.pg
        point = self.point(marker.address, arena_size)
        color = (250, 225, 150)
        x, y = point
        if marker.kind == "request":
            for offset in range(-marker.half_width, marker.half_width + 1):
                pg.draw.circle(self.screen, (130, 130, 130), self.point((marker.address + offset) % arena_size, arena_size), 3, 1)
            pg.draw.circle(self.screen, color, point, 10, 2)
            self.text("SENSE / pending", x + 12, y - 20)
        elif marker.kind == "historical":
            pg.draw.polygon(self.screen, color, [(x,y-7),(x+7,y),(x,y+7),(x-7,y)], 1)
            self.text(f"sample {marker.address}", x + 10, y)
        elif marker.kind == "move" and marker.origin is not None:
            origin = self.point(marker.origin, arena_size)
            pg.draw.line(self.screen, color, origin, point, 2)
            angle = math.atan2(y - origin[1], x - origin[0])
            pg.draw.polygon(self.screen, color, [point, (x-10*math.cos(angle-.5), y-10*math.sin(angle-.5)), (x-10*math.cos(angle+.5), y-10*math.sin(angle+.5))])
        elif marker.kind in {"write", "receipt"}:
            pg.draw.line(self.screen, color, (x-6,y-6 if marker.kind == "write" else y), (x+6,y+6 if marker.kind == "write" else y), 2)
            pg.draw.line(self.screen, color, (x-6 if marker.kind == "write" else x,y+6 if marker.kind == "write" else y-6), (x+6 if marker.kind == "write" else x,y-6 if marker.kind == "write" else y+6), 2)
        else:
            pg.draw.rect(self.screen, color, (x-4,y-4,8,8))

    def draw_omniscient(self, view: OmniscientView) -> None:
        self.last_lines, self.last_markers = (), ()
        self.text(view.label, 20, 16)
        self.text(f"Tick {view.tick} / {view.phase.value} — verified sub-tick reconstruction", 20, 38)
        self.pg.draw.rect(self.screen, (50, 55, 65), self._arena_rect)
        for address, value in enumerate(view.memory):
            point = self.point(address, len(view.memory))
            owner = view.owners[address]
            color = (value, 140 if owner == "A" else 55, 140 if owner == "B" else 55)
            self.pg.draw.rect(self.screen, color, (*point, 5, 5))
        for entrant, process, anchor in view.anchors:
            point = self.point(anchor, len(view.memory))
            self.pg.draw.circle(self.screen, (255,255,255), point, 7, 1)
            self.text(f"{entrant}/{process}", point[0]+8, point[1])
        self.text("Full world state includes information agents did not possess.", 20, 140)
