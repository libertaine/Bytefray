"""Minimal in-Pygame "no replay loaded" screen and replay picker.

Shown by the standalone Replay Viewer's no-argument entry point before any
replay is loaded (Phase 3 UX-20..UX-23): a first-time Windows user who
double-clicks the "Replay Viewer" Start Menu shortcut must see a visible,
understandable window rather than nothing at all.

This module never parses replay content -- it only lets the user navigate
directories and pick a ``*.jsonl`` path, which the caller
(``battle_client.cli``) then feeds into the existing
``ReplaySession.load``/``PygameRenderer.run`` path. There is exactly one
replay-loading implementation; this is a path-selection UI only.

**Why not a native OS file dialog.** The standalone replay viewer is
deliberately built against only the ``replay`` extra (``pygame-ce`` --
see ``pyproject.toml``); the Agent Designer's PySide6 ``QFileDialog`` lives
behind the separate ``designer`` extra and is not installed alongside it
(``tools/replay_viewer.spec`` bundles no Qt runtime). Pulling PySide6 into
the packaged replay-viewer just to obtain one button would add a second GUI
toolkit's full runtime to what is otherwise a lean, single-dependency
package, breaking that deliberate boundary. A small in-Pygame directory
browser keeps the standalone viewer's dependency footprint exactly as it
already is.
"""

from __future__ import annotations

import os
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPLAY_SUFFIX = ".jsonl"

_BACKGROUND = (18, 20, 26)
_PANEL = (28, 31, 40)
_TEXT = (225, 228, 235)
_MUTED = (150, 156, 168)
_ACCENT = (90, 160, 240)
_BUTTON = (46, 96, 168)
_BUTTON_HOVER = (60, 116, 196)
_ERROR = (230, 110, 100)
_ROW_SELECTED = (52, 66, 96)


@dataclass(frozen=True)
class _Entry:
    path: Path
    is_dir: bool
    display_name: str | None = None

    @property
    def label(self) -> str:
        if self.display_name is not None:
            return self.display_name
        return f"[{self.path.name}]" if self.is_dir else self.path.name


def _list_directory(directory: Path) -> list[_Entry]:
    """Subdirectories first, then ``*.jsonl`` files -- both alphabetical.

    Never raises: an unreadable directory (permissions, or a race with
    deletion) yields an empty listing rather than crashing the picker.
    """
    try:
        children = list(directory.iterdir())
    except OSError:
        return []
    dirs = sorted((c for c in children if c.is_dir()), key=lambda c: c.name.lower())
    files = sorted(
        (c for c in children if c.is_file() and c.suffix.lower() == REPLAY_SUFFIX),
        key=lambda c: c.name.lower(),
    )
    return [_Entry(d, True) for d in dirs] + [_Entry(f, False) for f in files]


def _list_filesystem_roots() -> list[_Entry]:
    """Drive letters on Windows; the single root elsewhere.

    Lets the picker cross drives (``go_up`` from a drive root lands here)
    without needing a general "type a path" input. Uses
    ``GetLogicalDrives`` rather than probing each ``X:\\`` with
    ``Path.exists()``: an empty optical/removable drive can make ordinary
    filesystem access stall or prompt ("insert disk"), which
    ``GetLogicalDrives`` never does -- it only reports which drive letters
    are currently mounted, doing no I/O against any of them.
    """
    if os.name == "nt":
        import ctypes

        # ctypes.windll only exists in typeshed's win32-conditional stubs --
        # see battle_engine.process_containment for the identical pattern.
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
        return [
            _Entry(Path(f"{letter}:\\"), True, display_name=f"{letter}:\\")
            for index, letter in enumerate(string.ascii_uppercase)
            if bitmask & (1 << index)
        ]
    return [_Entry(Path("/"), True, display_name="/")]


class ReplayPicker:
    """A tiny modal directory browser drawn with plain Pygame primitives.

    Not a general file manager: it shows one directory at a time, lets the
    user descend into subdirectories or pick a ``*.jsonl`` file, and go back
    up (including across drives on Windows once a filesystem root is
    reached). Deliberately minimal per the Phase 3 brief's empty-state
    design constraint -- no thumbnails, search, sort, or history.
    """

    def __init__(self, directory: Path) -> None:
        self.at_roots = False
        self.directory = directory
        self.entries: list[_Entry] = _list_directory(directory)
        self.selected = 0
        self.scroll = 0

    def set_directory(self, directory: Path) -> None:
        self.at_roots = False
        self.directory = directory
        self.entries = _list_directory(directory)
        self.selected = 0
        self.scroll = 0

    def _set_roots(self) -> None:
        self.at_roots = True
        self.entries = _list_filesystem_roots()
        self.selected = 0
        self.scroll = 0

    def move(self, delta: int) -> None:
        if not self.entries:
            return
        self.selected = max(0, min(len(self.entries) - 1, self.selected + delta))

    def go_up(self) -> bool:
        """Move to the parent directory, or to the drive/root list if
        already at a filesystem root. Returns ``False`` only when already
        showing the root list itself (nothing higher to go)."""
        if self.at_roots:
            return False
        parent = self.directory.parent
        if parent == self.directory:
            self._set_roots()
            return True
        self.set_directory(parent)
        return True

    def activate(self, index: int | None = None) -> Path | None:
        """Enter the highlighted directory/root, or return the highlighted
        file's path.

        Returns ``None`` after entering a directory (browsing continues);
        returns a file path once a real ``*.jsonl`` file is activated.
        """
        if index is not None:
            if index < 0 or index >= len(self.entries):
                return None
            self.selected = index
        if not self.entries:
            return None
        entry = self.entries[self.selected]
        if entry.is_dir:
            self.set_directory(entry.path)
            return None
        return entry.path


def run_empty_state(
    pg: Any,
    *,
    title: str,
    initial_directory: Path,
    message: str = "",
    window_size: tuple[int, int] = (720, 460),
) -> Path | None:
    """Show the "no replay loaded" screen and let the user pick a replay.

    Returns the chosen ``.jsonl`` path, or ``None`` if the user closed the
    window without picking one (a normal, non-error outcome). ``pg`` is an
    already-``import``ed ``pygame`` module -- this function does not import
    it itself, matching every other renderer entry point's lazy-import
    convention (see ``PygameRenderer.run``).

    ``message`` seeds the empty state with a one-line status (for example,
    why the caller's previous pick could not be opened) -- a Windows user
    launched from the Start Menu has no terminal to read a stderr message
    from, so any "that pick did not work" feedback must show up in the
    window itself.
    """
    if not pg.get_init():
        pg.init()
    screen = pg.display.set_mode(window_size, pg.RESIZABLE)
    pg.display.set_caption(title)
    font = pg.font.SysFont("consolas", 18)
    small_font = pg.font.SysFont("consolas", 14)
    row_font = pg.font.SysFont("consolas", 15)

    picker = ReplayPicker(initial_directory)
    mode = "empty"
    button_rect = pg.Rect(0, 0, 0, 0)
    row_rects: list[Any] = []
    clock = pg.time.Clock()

    while True:
        clock.tick(30)
        mouse_pos = pg.mouse.get_pos()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return None
            if event.type == pg.VIDEORESIZE:
                screen = pg.display.set_mode((event.w, event.h), pg.RESIZABLE)
            elif mode == "empty":
                if event.type == pg.KEYDOWN and event.key in (
                    pg.K_RETURN,
                    pg.K_o,
                    pg.K_SPACE,
                ):
                    mode = "browse"
                    message = ""
                elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    return None
                elif (
                    event.type == pg.MOUSEBUTTONDOWN
                    and event.button == 1
                    and button_rect.collidepoint(event.pos)
                ):
                    mode = "browse"
                    message = ""
            else:  # mode == "browse"
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        mode = "empty"
                    elif event.key == pg.K_UP:
                        picker.move(-1)
                    elif event.key == pg.K_DOWN:
                        picker.move(1)
                    elif event.key == pg.K_BACKSPACE:
                        picker.go_up()
                    elif event.key == pg.K_RETURN:
                        chosen = picker.activate()
                        if chosen is not None:
                            return chosen
                elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    for index, rect in enumerate(row_rects):
                        if rect.collidepoint(event.pos):
                            chosen = picker.activate(index)
                            if chosen is not None:
                                return chosen
                            break

        screen.fill(_BACKGROUND)
        if mode == "empty":
            button_rect = _draw_empty_state(pg, screen, font, small_font, message, mouse_pos)
        else:
            row_rects = _draw_browser(pg, screen, font, row_font, small_font, picker, mouse_pos)
        pg.display.flip()


def _draw_empty_state(pg: Any, screen: Any, font: Any, small_font: Any, message: str, mouse_pos: tuple[int, int]) -> Any:
    width, height = screen.get_size()
    heading = font.render("No replay loaded", True, _TEXT)
    screen.blit(heading, (width // 2 - heading.get_width() // 2, height // 2 - 90))

    lines = [
        "Open a saved Bytefray replay to view a completed match.",
        "Agent Designer creates one automatically each time you run a match.",
    ]
    for offset, line in enumerate(lines):
        rendered = small_font.render(line, True, _MUTED)
        screen.blit(
            rendered,
            (width // 2 - rendered.get_width() // 2, height // 2 - 40 + offset * 22),
        )

    button_w, button_h = 200, 44
    button_rect = pg.Rect(
        width // 2 - button_w // 2, height // 2 + 30, button_w, button_h
    )
    hovered = button_rect.collidepoint(mouse_pos)
    pg.draw.rect(screen, _BUTTON_HOVER if hovered else _BUTTON, button_rect, border_radius=6)
    pg.draw.rect(screen, _ACCENT, button_rect, 1, border_radius=6)
    label = font.render("Open Replay...", True, _TEXT)
    screen.blit(
        label,
        (
            button_rect.centerx - label.get_width() // 2,
            button_rect.centery - label.get_height() // 2,
        ),
    )

    if message:
        error_rendered = small_font.render(message, True, _ERROR)
        screen.blit(
            error_rendered,
            (width // 2 - error_rendered.get_width() // 2, height // 2 + 90),
        )
    return button_rect


def _draw_browser(
    pg: Any,
    screen: Any,
    font: Any,
    row_font: Any,
    small_font: Any,
    picker: ReplayPicker,
    mouse_pos: tuple[int, int],
) -> list[Any]:
    width, _height = screen.get_size()
    padding = 16
    heading_text = "Choose a drive" if picker.at_roots else str(picker.directory)
    heading = small_font.render(heading_text, True, _MUTED)
    screen.blit(heading, (padding, padding))

    hint = small_font.render(
        "Up/Down: move  Enter: open  Backspace: up a level  Esc: cancel", True, _MUTED
    )
    screen.blit(hint, (padding, padding + 22))

    row_top = padding + 52
    row_height = 26
    row_rects: list[Any] = []
    if not picker.entries:
        empty_label = row_font.render("(no folders or replays here)", True, _MUTED)
        screen.blit(empty_label, (padding, row_top))
    for index, entry in enumerate(picker.entries):
        rect = pg.Rect(padding, row_top + index * row_height, width - 2 * padding, row_height)
        is_selected = index == picker.selected
        if is_selected or rect.collidepoint(mouse_pos):
            pg.draw.rect(screen, _ROW_SELECTED, rect, border_radius=4)
        color = _ACCENT if entry.is_dir else _TEXT
        label = row_font.render(entry.label, True, color)
        screen.blit(label, (rect.x + 8, rect.y + 4))
        row_rects.append(rect)
    return row_rects
