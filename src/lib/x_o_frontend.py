"""Фронтенд для игры X and O."""

from __future__ import annotations

from typing import Callable, Optional

import arcade
import arcade.gui

try:
    from .frontend import Menager
    from .menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )
except ImportError:
    from frontend import Menager
    from menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )


BOARD_SIZE = 474
CELL_COUNT = 3
EMPTY_CELL = ""

STATUS_TEXT = {
    "idle": "Создайте лобби или подключитесь к игре",
    "waiting": "Ожидание второго игрока",
    "joined": "Игрок подключился",
    "start": "Игра началась",
    "move": "Ход принят",
    "not your turn": "Сейчас ход соперника",
    "bad move": "Некорректная клетка",
    "busy": "Эта клетка уже занята",
    "win": "Партия завершена",
    "draw": "Ничья",
    "leave": "Соперник покинул игру",
}


class TicTacToeView(NeonBaseView):
    """Экран крестиков-ноликов в стиле главного меню."""

    def __init__(
        self,
        player_name: str = "",
        on_back: Optional[Callable[[], None]] = None,
    ):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self.menager = Menager()

        self.board = [[EMPTY_CELL] * CELL_COUNT for _ in range(CELL_COUNT)]
        self.nicks: list[str] = []
        self.symbol: str | None = None
        self.turn: str | None = None
        self.status = "idle"
        self.error_text = ""

        self.title_label = arcade.Text(
            "X AND O",
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
            font_size=22,
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
        self.left_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(230, 241, 255),
            font_size=20,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.right_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(230, 241, 255),
            font_size=20,
            font_name=("Bahnschrift", "Calibri", "Arial"),
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        self._build_ui()

    def _build_ui(self) -> None:
        controls = arcade.gui.UIBoxLayout(vertical=False, space_between=14)

        start_button = arcade.gui.UIFlatButton(
            text="СТАРТ",
            width=190,
            height=64,
            style=build_primary_button_style(),
        )

        @start_button.event("on_click")
        def on_start(_event):
            self.menager.push_message("start")
            self.status = "waiting"

        controls.add(start_button)

        if self.on_back is not None:
            back_button = arcade.gui.UIFlatButton(
                text="В МЕНЮ",
                width=190,
                height=64,
                style=build_menu_button_style(exit_button=True),
            )

            @back_button.event("on_click")
            def on_back(_event):
                self.on_back()

            controls.add(back_button)

        self._add_centered_widget(controls, align_y=-300)

    def on_update(self, _delta_time: float) -> None:
        self._consume_statuses()

    def on_draw(self) -> None:
        self.clear()
        self._draw_neon_background()
        self._draw_game_shell()
        self._draw_text_layer()
        self._draw_board()
        self.ui.draw()

    def on_mouse_press(
        self,
        x: float,
        y: float,
        _button: int,
        _modifiers: int,
    ) -> None:
        cell = self._cell_at_point(x, y)

        if cell is None:
            return

        row, col = cell

        if self.status in ("win", "draw", "leave"):
            return

        if self.symbol is None:
            self.status = "waiting"
            return

        if self.board[row][col] != EMPTY_CELL:
            self.status = "busy"
            return

        if self.turn is not None and self.player_name and self.turn != self.player_name:
            self.status = "not your turn"
            return

        self.menager.push_message({"row": row, "col": col})

    def _consume_statuses(self) -> None:
        latest_status = None
        latest_error = None

        while True:
            status, error = self.menager.pop_status()

            if status is None and error is None:
                break

            if error is not None:
                latest_error = error

            if (
                isinstance(status, dict)
                and status.get("game") == "X_O"
            ):
                latest_status = status

        if latest_error is not None:
            self.error_text = str(latest_error)

        if latest_status is None:
            return

        self.board = latest_status.get("board", self.board)
        self.nicks = latest_status.get("nicks", self.nicks)
        self.symbol = latest_status.get("symbol")
        self.turn = latest_status.get("turn")
        self.status = latest_status.get("status", self.status)
        self.error_text = ""

    def _draw_game_shell(self) -> None:
        width = self.window.width
        height = self.window.height

        self._draw_filled_rect(
            width * 0.16,
            width * 0.84,
            height * 0.11,
            height * 0.80,
            (5, 12, 30, 105),
        )
        self._draw_outlined_rect(
            width * 0.16,
            width * 0.84,
            height * 0.11,
            height * 0.80,
            (66, 188, 255, 80),
            border_width=2,
        )

        self._draw_player_panel(
            left=24,
            right=330,
            bottom=height - 116,
            top=height - 24,
            caption="ИГРОК",
            value=self._player_text(),
            color=CYAN,
        )
        self._draw_player_panel(
            left=width - 330,
            right=width - 24,
            bottom=height - 116,
            top=height - 24,
            caption="ХОД",
            value=self._turn_text(),
            color=PURPLE,
        )

    def _draw_player_panel(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        caption: str,
        value: str,
        color: tuple[int, int, int],
    ) -> None:
        self._draw_filled_rect(left, right, bottom, top, (5, 20, 46, 195))
        self._draw_outlined_rect(left, right, bottom, top, color + (185,), 2)

        label = self.left_label if caption == "ИГРОК" else self.right_label
        label.text = f"{caption}: {value}"
        label.x = (left + right) / 2
        label.y = (bottom + top) / 2
        label.draw()

    def _draw_text_layer(self) -> None:
        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.875
        self.title_label.draw()

        self.status_label.text = self._status_text()
        self.status_label.x = self.window.width / 2
        self.status_label.y = self.window.height * 0.755
        self.status_label.draw()

        self.meta_label.text = self._meta_text()
        self.meta_label.x = self.window.width / 2
        self.meta_label.y = self.window.height * 0.185
        self.meta_label.draw()

    def _draw_board(self) -> None:
        left, right, bottom, top, cell_size = self._board_bounds()

        self._draw_filled_rect(left, right, bottom, top, (4, 14, 34, 210))
        self._draw_outlined_rect(left, right, bottom, top, (88, 212, 255, 190), 3)
        self._draw_outlined_rect(
            left - 7,
            right + 7,
            bottom - 7,
            top + 7,
            (130, 230, 255, 75),
            2,
        )

        for index in range(1, CELL_COUNT):
            x = left + cell_size * index
            y = bottom + cell_size * index
            arcade.draw_line(x, bottom, x, top, (74, 197, 255, 150), 3)
            arcade.draw_line(left, y, right, y, (74, 197, 255, 150), 3)

        for row in range(CELL_COUNT):
            for col in range(CELL_COUNT):
                symbol = self.board[row][col]

                if symbol == EMPTY_CELL:
                    continue

                center_x = left + cell_size * (col + 0.5)
                center_y = top - cell_size * (row + 0.5)
                self._draw_symbol(symbol, center_x, center_y, cell_size)

    def _draw_symbol(
        self,
        symbol: str,
        center_x: float,
        center_y: float,
        cell_size: float,
    ) -> None:
        pad = cell_size * 0.24

        if symbol == "X":
            color = (92, 230, 255, 235)
            arcade.draw_line(
                center_x - cell_size / 2 + pad,
                center_y - cell_size / 2 + pad,
                center_x + cell_size / 2 - pad,
                center_y + cell_size / 2 - pad,
                color,
                8,
            )
            arcade.draw_line(
                center_x - cell_size / 2 + pad,
                center_y + cell_size / 2 - pad,
                center_x + cell_size / 2 - pad,
                center_y - cell_size / 2 + pad,
                color,
                8,
            )
            return

        if symbol == "O":
            arcade.draw_circle_outline(
                center_x,
                center_y,
                cell_size * 0.28,
                (203, 143, 255, 235),
                8,
            )

    def _board_bounds(self) -> tuple[float, float, float, float, float]:
        size = min(
            BOARD_SIZE,
            self.window.width * 0.48,
            self.window.height * 0.58,
        )
        cell_size = size / CELL_COUNT
        center_x = self.window.width / 2
        center_y = self.window.height * 0.47
        left = center_x - size / 2
        right = center_x + size / 2
        bottom = center_y - size / 2
        top = center_y + size / 2

        return left, right, bottom, top, cell_size

    def _cell_at_point(self, x: float, y: float) -> tuple[int, int] | None:
        left, right, bottom, top, cell_size = self._board_bounds()

        if x < left or x > right or y < bottom or y > top:
            return None

        row = int((top - y) // cell_size)
        col = int((x - left) // cell_size)

        if row not in range(CELL_COUNT) or col not in range(CELL_COUNT):
            return None

        return row, col

    def _player_text(self) -> str:
        if self.symbol is None:
            return self.player_name or "ожидание"

        name = self.player_name or "вы"
        return f"{name} / {self.symbol}"

    def _turn_text(self) -> str:
        if self.status == "draw":
            return "ничья"

        if self.status == "win" and self.turn is not None:
            return f"победил {self.turn}"

        if self.turn is None:
            return "ожидание"

        return self.turn

    def _status_text(self) -> str:
        if self.error_text:
            return self.error_text

        return STATUS_TEXT.get(self.status, self.status)

    def _meta_text(self) -> str:
        if not self.nicks:
            return "Состав лобби появится после подключения к серверу"

        return "Лобби: " + "  /  ".join(self.nicks)
