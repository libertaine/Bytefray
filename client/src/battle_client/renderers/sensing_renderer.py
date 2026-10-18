"""Pygame sensing replay: filtered entrant drawing and explicit omniscience.

No ReplaySession, reconstruction facts, analysis cache or operator report is
passed into draw_entrant. Each redraw starts from a blank surface.

Layout is computed from the active font's measured line height and text
widths, top to bottom: title, phase, A | B | Omni selector, content (arena map
plus scrollable history, or the static Help page), a dedicated wrapped
disclaimer row, the terminal row, the timeline and the wrapped footer.
"""

from __future__ import annotations

import math
from typing import Any

from battle_engine.ruleset_names import ACTIVE_SENSING_DISPLAY_NAME

from battle_client.renderers.base import RendererDependencyError
from battle_client.sensing import OmniscientView, SensingView
from battle_client.sensing_presentation import (
    PERSPECTIVE_ORDER,
    SELECTOR_LABELS,
    SELECTOR_ORDER,
    SensingMarker,
    SensingPresentation,
    entrant_scene,
    sensing_guide_lines,
)

Rect = tuple[int, int, int, int]

TEXT = (240, 240, 240)
MUTED = (160, 160, 160)
MARGIN = 20
# Every printable ASCII glyph plus the non-ASCII glyphs this viewer draws.
ROW_PROBE = "".join(chr(code) for code in range(33, 127)) + "—É"
ENTRANT_DISCLAIMER = (
    "Markers are delivered facts only; the rest of the arena is unknown. Historical samples stay at "
    "their recorded address; they do not track opponents."
)
ENTRANT_CAPTION = "Arena map: own core, own anchors and delivered samples"
OMNISCIENT_CAPTION = "Arena map: full world state (A green, B blue)"
OMNISCIENT_DISCLAIMER = (
    "Full world state includes information agents did not possess. Operator checks are not part "
    "of either agent's delivered view."
)
HELP_CONTROLS = (
    "Help (? closes it; wheel scrolls this page). It is static and does not describe the open replay.",
    (
        "Perspective: click A | B | Omni, or press 2 = Agent A, 3 = Agent B, 1 = Omniscient; "
        "V/P cycles Omni -> A -> B."
    ),
    (
        "Space: play/pause; Left/Right: phase step; Shift+Left/Right: 10 ticks; Home: restart; "
        "End: recorded end; +/-: speed; drag the bar: phase seek; wheel: scroll history."
    ),
    (
        "Map: small squares = own core; ring = SENSE request; + = receipt; diamond = historical sample; "
        "arrow = MOVE; X = recorded WRITE. Labels that would overlap are left off the map and counted; "
        "every delivered sample stays in the history list."
    ),
)


def intersects(a: Rect, b: Rect) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def contains(outer: Rect, inner: Rect) -> bool:
    return (
        inner[0] >= outer[0] and inner[1] >= outer[1]
        and inner[0] + inner[2] <= outer[0] + outer[2]
        and inner[1] + inner[3] <= outer[1] + outer[3]
    )


class SensingReplayRenderer:
    def __init__(self) -> None:
        self.pg: Any = None
        self.screen: Any = None
        self.font: Any = None
        self.help_visible = False
        self.help_scroll = 0
        self.scrubbing = False
        self.scroll_offset = 0
        self.last_lines: tuple[str, ...] = ()
        self.last_markers: tuple[SensingMarker, ...] = ()
        # Measured geometry of the last frame, for layout assertions.
        self.layout: dict[str, Rect] = {}
        self.rendered_text: list[tuple[str, Rect]] = []
        self.marker_label_rects: list[tuple[str, Rect]] = []
        self.marker_glyph_rects: list[Rect] = []
        self.omitted_marker_labels = 0
        self._selector_rects: dict[str | None, Rect] = {}
        self._caption_lines: list[str] = []
        self._line_font: Any = None
        self._line_pitch = 0
        self._arena_rect: Rect = (20, 150, 600, 300)
        self._map_rect: Rect = self._arena_rect
        self._timeline_rect: Rect = (20, 650, 1060, 20)

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
            pygame.display.set_caption(f"Bytefray — {ACTIVE_SENSING_DISPLAY_NAME} replay")
            self.font = pygame.font.SysFont("consolas", 15)
            if initial_speed is not None:
                presentation.controller.set_speed(initial_speed)
            initial = {"A": "A", "B": "B", "broadcast": None, "omniscient": None}
            if initial_perspective in initial and initial[initial_perspective] != presentation.selected:
                presentation.select(initial[initial_perspective])
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

    def _select(self, presentation: SensingPresentation, choice: str | None) -> None:
        presentation.select(choice)
        self._reset_view_state()

    def _reset_view_state(self) -> None:
        # A perspective change must not carry the previous view's history state.
        self.scroll_offset = 0
        self.scrubbing = False
        self.last_lines, self.last_markers = (), ()
        self.marker_label_rects = []
        self.omitted_marker_labels = 0

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
                presentation.cycle()
                self._reset_view_state()
            index = action.select_perspective_index
            if index is not None and 0 <= index < len(PERSPECTIVE_ORDER):
                self._select(presentation, PERSPECTIVE_ORDER[index])
            if action.toggle_help:
                self.help_visible = not self.help_visible
                self.help_scroll = 0
        elif event.type == pg.VIDEORESIZE:
            self.screen = pg.display.set_mode((max(900, event.w), max(650, event.h)), pg.RESIZABLE)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            hits = [c for c, r in self._selector_rects.items() if contains(r, (*event.pos, 1, 1))]
            if hits:
                self._select(presentation, hits[0])
            elif self.seek_from_mouse(event.pos, presentation):
                self.scrubbing = True
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            self.scrubbing = False
        elif event.type == pg.MOUSEWHEEL:
            if self.help_visible:
                self.help_scroll = max(0, self.help_scroll - event.y * 3)
            else:
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
        self.screen.blit(self.font.render(value, True, TEXT), (x, y))
        width, height = self.font.size(value)
        self.rendered_text.append((value, (x, y, width, height)))

    def line_height(self) -> int:
        """Row pitch that bounds every drawn string's measured height.

        Some font builds report a text height that varies by glyph and exceeds
        the nominal line spacing, so measure the union of the glyphs drawn here.
        """
        if self._line_font is not self.font:
            self._line_font = self.font
            self._line_pitch = max(self.font.get_linesize(), self.font.get_height(), self.font.size(ROW_PROBE)[1])
        return self._line_pitch

    def wrap(self, value: str, width: int) -> list[str]:
        """Greedy word wrap measured with the active font; long words are split."""
        lines: list[str] = []
        current = ""
        for word in value.split(" "):
            candidate = f"{current} {word}" if current else word
            if self.font.size(candidate)[0] <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
            while self.font.size(current)[0] > width and len(current) > 1:
                cut = len(current) - 1
                while cut > 1 and self.font.size(current[:cut])[0] > width:
                    cut -= 1
                lines.append(current[:cut])
                current = current[cut:]
        lines.append(current)
        return lines

    def point(self, address: int, arena_size: int) -> tuple[int, int]:
        cols = min(32, arena_size)
        rows = math.ceil(arena_size / cols)
        x, y, width, height = self._map_rect
        return (x + int((address % cols + .5) * width / cols), y + int((address // cols + .5) * height / rows))

    def _footer_lines(self, presentation: SensingPresentation, width: int) -> list[str]:
        playing = "Playing" if presentation.controller.playing else "Paused"
        lines = [
            f"{playing} / {presentation.speed:g}x — Space: play/pause; arrows: phase step; Shift+arrows: 10 ticks",
            "Home: restart; End: recorded end; +/-: speed; V/P or 1/2/3: perspective; drag bar: phase seek; ?: help",
        ]
        return [wrapped for line in lines for wrapped in self.wrap(line, width)]

    def compute_layout(self, presentation: SensingPresentation) -> dict[str, Any]:
        """Stack every region from measured font metrics; regions never share pixels."""
        width, height = self.screen.get_size()
        line = self.line_height()
        inner = width - 2 * MARGIN
        y = 10
        title = (MARGIN, y, inner, line)
        y += line + 2
        phase = (MARGIN, y, inner, line)
        y += line + 8
        selector = (MARGIN, y, inner, line + 10)
        content_top = y + line + 10 + 10
        footer_lines = self._footer_lines(presentation, inner)
        footer_h = len(footer_lines) * line
        footer = (MARGIN, height - 8 - footer_h, inner, footer_h)
        timeline = (MARGIN, footer[1] - 6 - 16, inner, 16)
        terminal_text = presentation.terminal_text
        terminal_lines = self.wrap(terminal_text, inner) if terminal_text else [""]
        terminal = (MARGIN, timeline[1] - 6 - len(terminal_lines) * line, inner, len(terminal_lines) * line)
        sensing = isinstance(presentation.current_view, SensingView)
        disclaimer_lines = self.wrap(ENTRANT_DISCLAIMER if sensing else OMNISCIENT_DISCLAIMER, inner)
        disclaimer_h = len(disclaimer_lines) * line
        disclaimer = (MARGIN, terminal[1] - 6 - disclaimer_h, inner, disclaimer_h)
        content = (MARGIN, content_top, inner, max(line, disclaimer[1] - 8 - content_top))
        left_w = int((inner - MARGIN) * .55)
        # Captions wrap to their own column: platform fonts differ in width.
        caption_lines = self.wrap(ENTRANT_CAPTION if sensing else OMNISCIENT_CAPTION, left_w)
        caption = (MARGIN, content_top, left_w, len(caption_lines) * line)
        arena_top = content_top + caption[3] + 4
        arena = (MARGIN, arena_top, left_w, max(line * 2, content[1] + content[3] - arena_top))
        right_x = MARGIN + left_w + MARGIN
        side = (right_x, content_top, width - MARGIN - right_x, content[3])
        return {
            "line": line,
            "rects": {
                "title": title, "phase": phase, "selector": selector, "content": content,
                "caption": caption, "arena": arena, "side": side, "disclaimer": disclaimer,
                "terminal": terminal, "timeline": timeline, "footer": footer,
            },
            "footer_lines": footer_lines, "terminal_lines": terminal_lines,
            "disclaimer_lines": disclaimer_lines, "caption_lines": caption_lines,
        }

    def draw(self, presentation: SensingPresentation) -> None:
        # Control plane supplies one approved payload, never the canonical session.
        self.screen.fill((14, 17, 22))
        self.rendered_text = []
        self.marker_label_rects = []
        self.marker_glyph_rects = []
        self.omitted_marker_labels = 0
        geometry = self.compute_layout(presentation)
        rects = geometry["rects"]
        line = geometry["line"]
        self.layout = dict(rects)
        self._caption_lines = geometry["caption_lines"]
        self._arena_rect = rects["arena"]
        # The bottom strip of the arena is reserved for the omitted-label count.
        x, y, w, h = self._arena_rect
        self._map_rect = (x, y, w, max(line, h - line - 6))
        self._timeline_rect = rects["timeline"]
        view = presentation.current_view
        if isinstance(view, SensingView):
            self.draw_entrant(view)
        else:
            self.draw_omniscient(view)
            if not self.help_visible:
                report = presentation.verification
                self.draw_column([
                    "Operator verification (not delivered to either agent):",
                    (
                        f"Artifact consistency={report.artifact_pair_consistent}; "
                        f"independent reconstruction={report.exchange_reconstructed}"
                    ),
                    (
                        f"Teaching exchange complete={report.teaching_complete}; "
                        f"filtered perspective available={report.knowledge_projected}; "
                        f"demo sidecar verified={presentation.sidecar_verified}"
                    ),
                    presentation.notice,
                ], rects["side"], 0)
        if self.help_visible:
            self.help_scroll = self.draw_column(
                [*HELP_CONTROLS, "", *sensing_guide_lines()], rects["content"], self.help_scroll
            )
            self.layout["help"] = rects["content"]
        self.draw_selector(presentation, rects["selector"])
        for index, value in enumerate(geometry["disclaimer_lines"]):
            self.text(value, rects["disclaimer"][0], rects["disclaimer"][1] + index * line)
        for index, value in enumerate(geometry["terminal_lines"]):
            if value:
                self.text(value, rects["terminal"][0], rects["terminal"][1] + index * line)
        x, y, track_width, track_height = self._timeline_rect
        self.pg.draw.rect(self.screen, (110, 110, 110), self._timeline_rect, 1)
        fraction = presentation.index / max(1, len(presentation.controller.positions) - 1)
        playhead = x + round(fraction * (track_width - 1))
        self.pg.draw.line(self.screen, (255, 255, 255), (playhead, y), (playhead, y + track_height - 1), 3)
        for index, value in enumerate(geometry["footer_lines"]):
            self.text(value, rects["footer"][0], rects["footer"][1] + index * line)

    def draw_selector(self, presentation: SensingPresentation, rect: Rect) -> None:
        x, y, _, height = rect
        self.text("Perspective:", x, y + 5)
        x += self.font.size("Perspective:")[0] + 10
        self._selector_rects = {}
        for index, choice in enumerate(SELECTOR_ORDER):
            if index:
                self.text("|", x, y + 5)
                x += self.font.size("|")[0] + 8
            label = SELECTOR_LABELS[choice]
            box = (x, y, self.font.size(label)[0] + 20, height)
            if choice == presentation.selected:
                self.pg.draw.rect(self.screen, (70, 90, 120), box)
            self.pg.draw.rect(self.screen, MUTED, box, 1)
            self.text(label, x + 10, y + 5)
            self._selector_rects[choice] = box
            x += box[2] + 8
        self.text("keys 2 / 3 / 1", x + 4, y + 5)

    def draw_column(self, lines: list[str], rect: Rect, offset: int) -> int:
        """Draw wrapped lines inside rect from a scroll offset; returns the clamped offset."""
        line = self.line_height()
        wrapped = [w for value in lines for w in (self.wrap(value, rect[2]) if value else [""])]
        visible = max(1, rect[3] // line)
        offset = max(0, min(offset, len(wrapped) - visible))
        y = rect[1]
        for value in wrapped[offset:offset + visible]:
            if value:
                self.text(value, rect[0], y)
            y += line
        return offset

    def draw_entrant(self, view: SensingView) -> None:
        """The entire entrant drawing boundary accepts only a filtered view."""
        scene = entrant_scene(view)
        self.last_lines, self.last_markers = scene.lines, scene.markers
        self.text(scene.label, *self.layout["title"][:2])
        self.text(scene.phase, *self.layout["phase"][:2])
        if self.help_visible:
            return
        self.draw_caption()
        self.pg.draw.rect(self.screen, (50, 55, 65), self._arena_rect)
        obstacles: list[Rect] = []
        if view.own_core_base is not None and view.own_core_size is not None:
            for offset in range(view.own_core_size):
                point = self.point((view.own_core_base + offset) % view.arena_size, view.arena_size)
                self.pg.draw.rect(self.screen, (230, 230, 230), (*point, 5, 5), 1)
                obstacles.append((*point, 5, 5))
        for marker in scene.markers:
            self.draw_marker(marker, view.arena_size)
            px, py = self.point(marker.address, view.arena_size)
            # Glyph extents: request circle r=10; diamonds/crosses/arrowheads within 10.
            obstacles.append((px - 10, py - 10, 21, 21))
        self.place_marker_labels(self.marker_labels(scene.markers, view.arena_size), obstacles)
        side = self.layout["side"]
        line = self.line_height()
        header = self.wrap("Wheel: scroll delivered history", side[2])
        for index, value in enumerate(header):
            self.text(value, side[0], side[1] + index * line)
        top = len(header) * line + 4
        history = (side[0], side[1] + top, side[2], side[3] - top)
        self.scroll_offset = self.draw_column(list(scene.lines), history, self.scroll_offset)

    def draw_caption(self) -> None:
        x, y = self.layout["caption"][:2]
        for index, value in enumerate(self._caption_lines):
            self.text(value, x, y + index * self.line_height())

    def marker_labels(self, markers: tuple[SensingMarker, ...], arena_size: int) -> list[tuple[str, tuple[int, int]]]:
        """Label requests first, then historical samples newest first."""
        requests = [m for m in markers if m.kind == "request"]
        samples = sorted(
            (m for m in markers if m.kind == "historical"),
            key=lambda m: (-m.sampled_callback, m.address),
        )
        labels = [("SENSE / pending", self.point(m.address, arena_size)) for m in requests]
        labels += [(f"sample {m.address}", self.point(m.address, arena_size)) for m in samples]
        return labels

    def place_marker_labels(
        self, labels: list[tuple[str, tuple[int, int]]], obstacles: list[Rect]
    ) -> None:
        """Place labels inside the map without covering text or glyphs; count the rest.

        A label stays beside its own marker: it takes the first adjacent
        position that is inside the map and intersects neither a placed label
        nor any marker glyph (``obstacles``). A label with no such position is
        omitted from the map only; its fact remains in the delivered history.
        """
        bounds = self._map_rect
        self.marker_glyph_rects = list(obstacles)
        placed: list[Rect] = []
        for value, (px, py) in labels:
            w, h = self.font.size(value)
            candidates = [
                (px + 11, py - h // 2), (px - 11 - w, py - h // 2),
                (px - w // 2, py - 11 - h), (px - w // 2, py + 11),
                (px + 11, py - h - 4), (px + 11, py + 4),
                (px - 11 - w, py - h - 4), (px - 11 - w, py + 4),
            ]
            choice = None
            for cx, cy in candidates:
                rect = (cx, cy, w, h)
                if (
                    contains(bounds, rect)
                    and not any(intersects(rect, other) for other in placed)
                    and not any(intersects(rect, glyph) for glyph in obstacles)
                ):
                    choice = rect
                    break
            if choice is None:
                self.omitted_marker_labels += 1
                continue
            placed.append(choice)
            self.screen.blit(self.font.render(value, True, TEXT), choice[:2])
            self.marker_label_rects.append((value, choice))
        if self.omitted_marker_labels:
            x, y, w, h = self._arena_rect
            count = self.omitted_marker_labels
            note = f"{count} more map labels not shown; see history"
            if self.font.size(note)[0] > w - 8:
                note = f"+{count} labels: see history"
            self.text(note, x + 4, y + h - self.line_height() - 2)
            self.layout["arena_note"] = self.rendered_text[-1][1]

    def draw_marker(self, marker: SensingMarker, arena_size: int) -> None:
        pg = self.pg
        point = self.point(marker.address, arena_size)
        color = (250, 225, 150)
        x, y = point
        if marker.kind == "request":
            for offset in range(-marker.half_width, marker.half_width + 1):
                pg.draw.circle(self.screen, (130, 130, 130), self.point((marker.address + offset) % arena_size, arena_size), 3, 1)
            pg.draw.circle(self.screen, color, point, 10, 2)
        elif marker.kind == "historical":
            pg.draw.polygon(self.screen, color, [(x,y-7),(x+7,y),(x,y+7),(x-7,y)], 1)
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
        self.text(view.label, *self.layout["title"][:2])
        self.text(f"Tick {view.tick} / {view.phase.value} — verified sub-tick reconstruction", *self.layout["phase"][:2])
        if self.help_visible:
            return
        self.draw_caption()
        self.pg.draw.rect(self.screen, (50, 55, 65), self._arena_rect)
        for address, value in enumerate(view.memory):
            point = self.point(address, len(view.memory))
            owner = view.owners[address]
            color = (value, 140 if owner == "A" else 55, 140 if owner == "B" else 55)
            self.pg.draw.rect(self.screen, color, (*point, 5, 5))
        labels = []
        obstacles: list[Rect] = []
        for entrant, process, anchor in view.anchors:
            point = self.point(anchor, len(view.memory))
            self.pg.draw.circle(self.screen, (255,255,255), point, 7, 1)
            labels.append((f"{entrant}/{process}", point))
            obstacles.append((point[0] - 8, point[1] - 8, 17, 17))
        self.place_marker_labels(labels, obstacles)
