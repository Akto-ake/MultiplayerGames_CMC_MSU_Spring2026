"""Фронтенд для игры X and O."""

from __future__ import annotations

from typing import Callable, Optional

import arcade
import arcade.gui

try:
    from .frontend import Manager
    from .menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )
    from .localization import tr, tr_error
except ImportError:
    from frontend import Manager
    from menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )
    from localization import tr, tr_error


BOARD_SIZE = 474
CELL_COUNT = 3
EMPTY_CELL = ""

STATUS_TEXT = {
    "idle": "x_o.idle",
    "waiting": "x_o.waiting",
    "joined": "x_o.joined",
    "start": "x_o.start",
    "move": "x_o.move",
    "not your turn": "x_o.not_your_turn",
    "bad move": "x_o.bad_move",
    "busy": "x_o.busy",
    "win": "x_o.win",
    "draw": "x_o.draw",
    "leave": "x_o.leave",
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
        self.manager = Manager()

        self.board = [[EMPTY_CELL] * CELL_COUNT for _ in range(CELL_COUNT)]
        self.nicks: list[str] = []
        self.lobby_id: int | None = None
        self.symbol: str | None = None
        self.turn: str | None = None
        self.status = "idle"
        self.error_text = ""
        self.move_pending = False

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
            font_size=17,
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
        self.lobby_label = arcade.Text(
            "",
            x=0,
            y=0,
            color=(165, 188, 214),
            font_size=14,
            font_name=("Calibri", "Arial"),
            anchor_x="right",
            anchor_y="top",
        )

        self._build_ui()

    def _build_ui(self) -> None:
        self.start_button = arcade.gui.UIFlatButton(
            text=tr("x_o.start_button"),
            width=190,
            height=64,
            style=build_primary_button_style(),
        )

        @self.start_button.event("on_click")
        def on_start(_event):
            self.manager.push_message("start")

        self.ui.add(self.start_button)

        if self.on_back is not None:
            self.back_button = arcade.gui.UIFlatButton(
                text=tr("x_o.back"),
                width=190,
                height=56,
                style=build_menu_button_style(exit_button=True),
            )

            @self.back_button.event("on_click")
            def on_back(_event):
                self.manager.push_message({"action": "leave_game"})
                self.on_back()

            self.ui.add(self.back_button)
        else:
            self.back_button = None

        self._add_locale_toggle()
        self._register_responsive_text(self.title_label, 56, 20, 0.42)
        self._register_responsive_text(self.status_label, 17, 10, 0.54)
        self._register_responsive_text(self.meta_label, 18, 10, 0.56)
        self._register_responsive_text(self.left_label, 20, 10, 0.24)
        self._register_responsive_text(self.right_label, 20, 10, 0.24)
        self._register_responsive_widget(
            self.start_button, 190, 64, 110, 38
        )
        self._register_responsive_button(self.start_button)
        if self.back_button is not None:
            self._register_responsive_widget(
                self.back_button, 190, 56, 110, 42
            )
            self._register_responsive_button(self.back_button)

    def on_update(self, _delta_time: float) -> None:
        """Считывает новые статусы игры от менеджера."""

        self._consume_statuses()

    def on_draw(self) -> None:
        """Отрисовывает экран игры и элементы интерфейса."""

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
        """Обрабатывает клик по клетке и отправляет ход."""

        cell = self._cell_at_point(x, y)

        if cell is None:
            return

        row, col = cell

        if self.status in ("win", "draw", "leave") or self.move_pending:
            return

        if self.symbol is None:
            return

        if self.board[row][col] != EMPTY_CELL:
            return

        if self.turn is not None and self.player_name and self.turn != self.player_name:
            self.status = "not your turn"
            return

        self.manager.push_message({"row": row, "col": col})
        self.board[row][col] = self.symbol
        self.status = "move"
        self.move_pending = True

    def _consume_statuses(self) -> None:
        latest_status = None
        latest_error = None

        while True:
            status, error = self.manager.pop_status()

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
            self.error_text = tr_error(latest_error)

        if latest_status is None:
            return

        self.board = latest_status.get("board", self.board)
        self.nicks = latest_status.get("nicks", self.nicks)
        self.lobby_id = latest_status.get("lobby_id", self.lobby_id)
        self.symbol = latest_status.get("symbol")
        self.turn = latest_status.get("turn")
        self.status = latest_status.get("status", self.status)
        self.error_text = ""
        self.move_pending = latest_status.get("move_pending", False)
        self._sync_start_button()

    def _sync_start_button(self) -> None:
        """Показывает старт только до раунда и после его завершения."""

        self.start_button.visible = self.status in (
            "idle",
            "waiting",
            "joined",
            "leave",
            "win",
            "draw",
        )

    def _draw_game_shell(self) -> None:
        width = self.window.width
        height = self.window.height
        scale = min(width / 1280, height / 720, 1.0)
        panel_margin = max(14, 24 * scale)
        info_panel_width = max(170, 250 * scale)
        lobby_panel_width = max(190, 306 * scale)
        panel_height = max(50, 72 * scale)
        panel_gap = max(10, 16 * scale)
        panel_top = height - panel_margin
        panel_bottom = panel_top - panel_height
        turn_left = width - panel_margin - info_panel_width
        player_top = panel_bottom - panel_gap
        player_bottom = player_top - panel_height

        self._draw_filled_rect(
            width * 0.26,
            width * 0.74,
            height * 0.14,
            height * 0.78,
            (5, 12, 30, 105),
        )
        self._draw_outlined_rect(
            width * 0.26,
            width * 0.74,
            height * 0.14,
            height * 0.78,
            (66, 188, 255, 80),
            border_width=2,
        )

        self._draw_player_panel(
            left=turn_left,
            right=width - panel_margin,
            bottom=player_bottom,
            top=player_top,
            caption=tr("x_o.player"),
            value=self._player_text(),
            color=CYAN,
        )
        self._draw_player_panel(
            left=turn_left,
            right=width - panel_margin,
            bottom=panel_bottom,
            top=panel_top,
            caption=tr("x_o.turn"),
            value=self._turn_text(),
            color=PURPLE,
        )

        if self.lobby_id is not None:
            self._draw_player_panel(
                left=panel_margin,
                right=panel_margin + lobby_panel_width,
                bottom=panel_margin,
                top=panel_margin + max(42, 56 * scale),
                caption=tr("x_o.lobby_id"),
                value=str(self.lobby_id),
                color=CYAN,
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

        label = (
            self.left_label
            if caption in (tr("x_o.player"), tr("x_o.lobby_id"))
            else self.right_label
        )
        label.text = f"{caption}: {value}"
        label.x = (left + right) / 2
        label.y = (bottom + top) / 2
        label.draw()

    def _draw_text_layer(self) -> None:
        self._update_responsive_layout()
        self._position_control_buttons()
        _left, _right, board_bottom, board_top, _cell_size = (
            self._board_bounds()
        )
        scale = min(
            self.window.width / 1280,
            self.window.height / 720,
            1.0,
        )
        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.86
        self.title_label.draw()

        self.status_label.text = self._status_text()
        self.status_label.x = self.window.width / 2
        self.status_label.y = board_top + max(14, 18 * scale)
        self.status_label.draw()

        self.meta_label.text = self._meta_text()
        self.meta_label.x = self.window.width / 2
        self.meta_label.y = board_bottom - max(12, 18 * scale)
        self.meta_label.draw()

    def _position_control_buttons(self) -> None:
        width = self.window.width
        height = self.window.height
        scale = min(width / 1280, height / 720, 1.0)
        panel_margin = max(14, 24 * scale)
        panel_width = max(190, 306 * scale)
        button_gap = max(8, 14 * scale)

        start_left = (width - self.start_button.width) / 2
        self.start_button.move(
            dx=start_left - self.start_button.left,
            dy=panel_margin - self.start_button.bottom,
        )

        if self.back_button is not None:
            back_left = panel_margin + panel_width + button_gap
            self.back_button.move(
                dx=back_left - self.back_button.left,
                dy=panel_margin - self.back_button.bottom,
            )

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

                cell_left = left + cell_size * col
                cell_right = cell_left + cell_size
                cell_top = top - cell_size * row
                cell_bottom = cell_top - cell_size
                fill_color = (
                    (16, 112, 150, 80)
                    if symbol == "X"
                    else (103, 48, 150, 80)
                )
                self._draw_filled_rect(
                    cell_left + 5,
                    cell_right - 5,
                    cell_bottom + 5,
                    cell_top - 5,
                    fill_color,
                )

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
            return self.player_name or tr("x_o.waiting_short")

        name = self.player_name or tr("x_o.you")
        return f"{name} / {self.symbol}"

    def _turn_text(self) -> str:
        if self.status == "draw":
            return tr("x_o.draw_short")

        if self.status == "win" and self.turn is not None:
            return tr("x_o.winner", player=self.turn)

        if self.turn is None:
            return tr("x_o.waiting_short")

        return self.turn

    def _status_text(self) -> str:
        if self.error_text:
            return self.error_text

        status_key = STATUS_TEXT.get(self.status)
        return tr(status_key) if status_key else self.status

    def _meta_text(self) -> str:
        if not self.nicks:
            return tr("x_o.empty_lobby")

        return tr("x_o.lobby", players="  /  ".join(self.nicks))

    def _refresh_texts(self) -> None:
        super()._refresh_texts()
        self.start_button.text = tr("x_o.start_button")
        if self.back_button is not None:
            self.back_button.text = tr("x_o.back")
