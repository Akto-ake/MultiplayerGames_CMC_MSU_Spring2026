"""Frontend screen for the Snake visual prototype."""

from __future__ import annotations

from typing import Callable

import arcade
import arcade.gui

try:
    from .frontend import Manager
    from .localization import tr
    from .menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )
except ImportError:
    from frontend import Manager
    from localization import tr
    from menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )


GRID_COLS = 16
GRID_ROWS = 14


class SnakeView(NeonBaseView):
    """Экран визуального прототипа Snake."""

    def __init__(self, player_name: str, on_back: Callable[[], None]):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self.manager = Manager()

        self.nicks: list[str] = []
        self.lobby_id: int | None = None
        self.side: str | None = None
        self.state = None
        self.status = "waiting"
        self.start_requested = False

        self.title_label = arcade.Text(
            "SNAKE",
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=56,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.status_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(154, 220, 255),
            font_size=20,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.score_label = arcade.Text(
            "0 : 0",
            x=0,
            y=0,
            color=(236, 247, 255),
            font_size=40,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.meta_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(196, 219, 240),
            font_size=18,
            font_name=("Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
        )

        self._build_ui()

    def _build_ui(self) -> None:
        controls = arcade.gui.UIBoxLayout(vertical=False, space_between=14)

        self.start_button = arcade.gui.UIFlatButton(
            text=tr("snake.start"),
            width=190,
            height=64,
            style=build_primary_button_style(),
        )

        @self.start_button.event("on_click")
        def on_start(_event):
            self.start_requested = True
            self.manager.push_message("start")
            self.status = "starting"

        self.pause_button = arcade.gui.UIFlatButton(
            text=tr("snake.pause"),
            width=260,
            height=64,
            style=build_primary_button_style(),
        )

        @self.pause_button.event("on_click")
        def on_pause(_event):
            self._toggle_pause()

        self.back_button = arcade.gui.UIFlatButton(
            text=tr("snake.back"),
            width=220,
            height=64,
            style=build_menu_button_style(exit_button=True),
        )

        @self.back_button.event("on_click")
        def on_back(_event):
            self.manager.push_message({"action": "leave_game"})
            self.on_back()

        controls.add(self.start_button)
        controls.add(self.pause_button)
        controls.add(self.back_button)
        self._add_centered_widget(controls, align_y=-300)
        self._add_locale_toggle()

    def on_update(self, _delta_time: float) -> None:
        """Считывает статусы Snake от backend."""

        while True:
            status, error = self.manager.pop_status()

            if status is None and error is None:
                return

            if isinstance(status, dict) and status.get("game") == "SNAKE":
                self.state = status.get("state", self.state)
                self.nicks = status.get("nicks", self.nicks)
                self.lobby_id = status.get("lobby_id", self.lobby_id)
                self.side = status.get("side", self.side)
                self.status = status.get("status", self.status)
                if self.state is not None:
                    self.start_requested = False

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Отправляет направление змейки."""

        direction = None
        side_name = None

        if key == arcade.key.W:
            side_name = "left"
            direction = "up"
        elif key == arcade.key.S:
            side_name = "left"
            direction = "down"
        elif key == arcade.key.A:
            side_name = "left"
            direction = "left"
        elif key == arcade.key.D:
            side_name = "left"
            direction = "right"
        elif key == arcade.key.UP:
            side_name = "right"
            direction = "up"
        elif key == arcade.key.DOWN:
            side_name = "right"
            direction = "down"
        elif key == arcade.key.LEFT:
            side_name = "right"
            direction = "left"
        elif key == arcade.key.RIGHT:
            side_name = "right"
            direction = "right"

        if side_name is not None and direction is not None:
            self._send_direction(side_name, direction)
            return

        super().on_key_press(key, modifiers)

    def on_draw(self) -> None:
        """Отрисовывает визуальный прототип Snake."""

        self.clear()
        self._draw_neon_background()
        self._draw_shell()
        self._draw_boards()
        self._draw_text_layer()
        self.ui.draw()

    def _draw_shell(self) -> None:
        width = self.window.width
        height = self.window.height

        self._draw_filled_rect(
            width * 0.08,
            width * 0.92,
            height * 0.12,
            height * 0.80,
            (5, 12, 30, 112),
        )
        self._draw_outlined_rect(
            width * 0.08,
            width * 0.92,
            height * 0.12,
            height * 0.80,
            (66, 188, 255, 90),
            border_width=2,
        )

    def _draw_boards(self) -> None:
        left_board, right_board = self._board_bounds()

        self._draw_board(left_board, CYAN, "left")
        self._draw_board(right_board, PURPLE, "right")
        self._draw_separator()

    def _draw_board(self, bounds, accent, side_name) -> None:
        left, right, bottom, top = bounds
        self._draw_filled_rect(left, right, bottom, top, (2, 10, 25, 225))
        self._draw_outlined_rect(left, right, bottom, top, accent + (170,), 3)
        self._draw_grid(bounds)
        self._draw_food(bounds, self._food(side_name))
        self._draw_snake(bounds, self._snake(side_name), accent)

    def _draw_grid(self, bounds) -> None:
        left, right, bottom, top = bounds
        cell_w = (right - left) / GRID_COLS
        cell_h = (top - bottom) / GRID_ROWS

        for col in range(1, GRID_COLS):
            x = left + col * cell_w
            arcade.draw_line(x, bottom, x, top, (82, 120, 150, 55), 1)

        for row in range(1, GRID_ROWS):
            y = bottom + row * cell_h
            arcade.draw_line(left, y, right, y, (82, 120, 150, 55), 1)

    def _draw_food(self, bounds, food) -> None:
        center_x, center_y, cell_size = self._cell_center(bounds, food)
        arcade.draw_circle_filled(
            center_x,
            center_y,
            cell_size * 0.32,
            (255, 94, 146, 245),
        )
        arcade.draw_circle_outline(
            center_x,
            center_y,
            cell_size * 0.46,
            (255, 176, 208, 150),
            2,
        )

    def _draw_snake(self, bounds, snake, accent) -> None:
        for index, cell in enumerate(snake):
            center_x, center_y, cell_size = self._cell_center(bounds, cell)
            radius = cell_size * (0.42 if index == 0 else 0.36)
            color = (230, 252, 255, 255) if index == 0 else accent + (230,)
            arcade.draw_circle_filled(center_x, center_y, radius, color)
            arcade.draw_circle_outline(
                center_x,
                center_y,
                radius + 2,
                accent + (120,),
                2,
            )

    def _draw_separator(self) -> None:
        center_x = self.window.width / 2
        bottom = self.window.height * 0.24
        top = self.window.height * 0.64
        dash_count = 11
        dash_h = (top - bottom) / (dash_count * 1.7)

        for index in range(dash_count):
            y_top = top - index * dash_h * 1.7
            self._draw_filled_rect(
                center_x - 2,
                center_x + 2,
                y_top - dash_h,
                y_top,
                (140, 230, 255, 135),
            )

    def _draw_text_layer(self) -> None:
        self._refresh_texts()

        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.88
        self.title_label.draw()

        self.status_label.text = self._status_text()
        self.status_label.x = self.window.width / 2
        self.status_label.y = self.window.height * 0.765
        self.status_label.draw()

        self.score_label.text = self._score_text()
        self.score_label.x = self.window.width / 2
        self.score_label.y = self.window.height * 0.69
        self.score_label.draw()

        self.meta_label.text = self._meta_text()
        self.meta_label.x = self.window.width / 2
        self.meta_label.y = self.window.height * 0.18
        self.meta_label.draw()

    def _board_bounds(self):
        width = self.window.width
        height = self.window.height
        return (
            (width * 0.12, width * 0.46, height * 0.25, height * 0.64),
            (width * 0.54, width * 0.88, height * 0.25, height * 0.64),
        )

    def _cell_center(self, bounds, cell):
        left, right, bottom, top = bounds
        col, row = cell
        cell_w = (right - left) / GRID_COLS
        cell_h = (top - bottom) / GRID_ROWS
        cell_size = min(cell_w, cell_h)
        return (
            left + (col + 0.5) * cell_w,
            bottom + (row + 0.5) * cell_h,
            cell_size,
        )

    def _status_text(self) -> str:
        if self.status == "leave":
            return tr("snake.leave")

        winner = self.state.get("winner") if self.state is not None else None
        if winner is not None:
            return tr("snake.finished", winner=winner)

        if self.start_requested:
            return tr("snake.starting")

        if self.state is not None and self.state.get("paused"):
            return tr("snake.paused")

        if self.state is not None:
            return tr("snake.playing")

        if len(self.nicks) >= 2:
            return tr("snake.ready")

        return tr("snake.waiting")

    def _score_text(self) -> str:
        if self.state is None:
            return "0 : 0"

        players = self.state["players"]
        score = self.state["score"]
        return f"{score[players[0]]} : {score[players[1]]}"

    def _meta_text(self) -> str:
        if not self.nicks:
            return tr("x_o.empty_lobby")

        text = tr("x_o.lobby", players="  /  ".join(self.nicks))
        if self.lobby_id is not None:
            text = f"{text}  |  ID: {self.lobby_id}"
        return text

    def _refresh_texts(self) -> None:
        super()._refresh_texts()
        self.start_button.text = tr("snake.start")
        self.pause_button.text = (
            tr("snake.resume")
            if self.state is not None and self.state.get("paused")
            else tr("snake.pause")
        )
        self.back_button.text = tr("snake.back")

    def _toggle_pause(self) -> None:
        if self.state is None or self.state.get("winner") is not None:
            return

        self.manager.push_message(
            {
                "game": "SNAKE",
                "action": "pause",
                "round": self.state.get("round"),
            }
        )

    def _send_direction(self, side_name: str, direction: str) -> None:
        if (
            self.state is None
            or self.state.get("winner") is not None
            or self.state.get("paused")
        ):
            return

        self.manager.push_message(
            {
                "game": "SNAKE",
                "action": "direction",
                "round": self.state.get("round"),
                "side": side_name,
                "direction": direction,
            }
        )

    def _snake(self, side_name: str):
        if self.state is None:
            if side_name == "left":
                return [[7, 7], [6, 7], [5, 7], [4, 7]]
            return [[8, 6], [9, 6], [10, 6], [11, 6]]

        nick = self._side_nick(side_name)
        if nick is None:
            return []

        return self.state["snakes"][nick]["body"]

    def _food(self, side_name: str):
        if self.state is None:
            return [11, 8] if side_name == "left" else [4, 4]

        nick = self._side_nick(side_name)
        if nick is None:
            return [0, 0]

        return self.state["snakes"][nick]["food"]

    def _side_nick(self, side_name: str) -> str | None:
        if self.state is None:
            return None

        players = self.state["players"]
        if side_name == "left" and len(players) > 0:
            return players[0]
        if side_name == "right" and len(players) > 1:
            return players[1]
        return None
