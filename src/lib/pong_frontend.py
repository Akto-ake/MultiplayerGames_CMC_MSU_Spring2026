"""Frontend screen for network Pong."""

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


PADDLE_H_RATIO = 0.26
PADDLE_W = 16
BALL_R = 12
PADDLE_SPEED = 0.85


class PongView(NeonBaseView):
    """Экран сетевой игры Pong."""

    def __init__(self, player_name: str, on_back: Callable[[], None]):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self.manager = Manager()

        self.state = None
        self.nicks: list[str] = []
        self.lobby_id: int | None = None
        self.side: str | None = None
        self.status = "waiting"
        self.error_text = ""
        self.local_paddle = 0.5
        self.move_direction = 0

        self.title_label = arcade.Text(
            "PONG",
            x=0,
            y=0,
            color=(228, 243, 255),
            font_size=58,
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
            font_size=21,
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
            font_size=42,
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
            text=tr("pong.start"),
            width=190,
            height=64,
            style=build_primary_button_style(),
        )

        @self.start_button.event("on_click")
        def on_start(_event):
            self.manager.push_message("start")
            self.status = "waiting"

        self.back_button = arcade.gui.UIFlatButton(
            text=tr("pong.back"),
            width=220,
            height=64,
            style=build_menu_button_style(exit_button=True),
        )

        @self.back_button.event("on_click")
        def on_back(_event):
            self.on_back()

        controls.add(self.start_button)
        controls.add(self.back_button)
        self._add_centered_widget(controls, align_y=-300)
        self._add_locale_toggle()

    def on_update(self, delta_time: float) -> None:
        """Обновляет локальный ввод и состояние от backend."""

        self._consume_statuses()
        self._update_local_paddle(delta_time)

    def on_draw(self) -> None:
        """Отрисовывает экран Pong."""

        self.clear()
        self._draw_neon_background()
        self._draw_game_shell()
        self._draw_playfield()
        self._draw_text_layer()
        self.ui.draw()

    def on_key_press(self, key: int, modifiers: int) -> None:
        """Обрабатывает клавиши движения ракетки."""

        if key in (arcade.key.W, arcade.key.UP):
            self.move_direction = 1
            return

        if key in (arcade.key.S, arcade.key.DOWN):
            self.move_direction = -1
            return

        super().on_key_press(key, modifiers)

    def on_key_release(self, key: int, _modifiers: int) -> None:
        """Останавливает движение ракетки при отпускании клавиш."""

        if key in (arcade.key.W, arcade.key.UP, arcade.key.S, arcade.key.DOWN):
            self.move_direction = 0

    def _consume_statuses(self) -> None:
        latest_status = None
        latest_error = None

        while True:
            status, error = self.manager.pop_status()

            if status is None and error is None:
                break

            if error is not None:
                latest_error = error

            if isinstance(status, dict) and status.get("game") == "PONG":
                latest_status = status

        if latest_error is not None:
            self.error_text = str(latest_error)

        if latest_status is None:
            return

        self.state = latest_status.get("state", self.state)
        self.nicks = latest_status.get("nicks", self.nicks)
        self.lobby_id = latest_status.get("lobby_id", self.lobby_id)
        self.side = latest_status.get("side", self.side)
        self.status = latest_status.get("status", self.status)
        self.error_text = ""

        if self.state and self.player_name in self.state["paddles"]:
            self.local_paddle = self.state["paddles"][self.player_name]

    def _update_local_paddle(self, delta_time: float) -> None:
        if self.side is None or self.move_direction == 0:
            return

        self.local_paddle += self.move_direction * PADDLE_SPEED * delta_time
        self.local_paddle = min(max(self.local_paddle, 0.13), 0.87)
        self.manager.push_message(
            {
                "game": "PONG",
                "action": "paddle",
                "position": float(self.local_paddle),
            }
        )

    def _draw_game_shell(self) -> None:
        width = self.window.width
        height = self.window.height

        self._draw_filled_rect(
            width * 0.14,
            width * 0.86,
            height * 0.12,
            height * 0.80,
            (5, 12, 30, 112),
        )
        self._draw_outlined_rect(
            width * 0.14,
            width * 0.86,
            height * 0.12,
            height * 0.80,
            (66, 188, 255, 90),
            border_width=2,
        )

    def _draw_playfield(self) -> None:
        left, right, bottom, top = self._field_bounds()

        self._draw_filled_rect(left, right, bottom, top, (2, 10, 25, 220))
        self._draw_outlined_rect(left, right, bottom, top, (98, 220, 255, 170), 3)
        self._draw_center_line(left, right, bottom, top)
        self._draw_paddles(left, right, bottom, top)
        self._draw_ball(left, right, bottom, top)

    def _draw_center_line(self, left, right, bottom, top) -> None:
        center_x = (left + right) / 2
        dash_count = 14
        dash_height = (top - bottom) / (dash_count * 1.9)

        for index in range(dash_count):
            y_top = top - index * dash_height * 1.9
            self._draw_filled_rect(
                center_x - 2,
                center_x + 2,
                y_top - dash_height,
                y_top,
                (140, 230, 255, 135),
            )

    def _draw_paddles(self, left, right, bottom, top) -> None:
        paddles = self._paddles()
        field_h = top - bottom
        paddle_h = field_h * PADDLE_H_RATIO

        left_y = bottom + field_h * paddles[0]
        right_y = bottom + field_h * paddles[1]

        self._draw_filled_rect(
            left + 34,
            left + 34 + PADDLE_W,
            left_y - paddle_h / 2,
            left_y + paddle_h / 2,
            CYAN + (230,),
        )
        self._draw_filled_rect(
            right - 34 - PADDLE_W,
            right - 34,
            right_y - paddle_h / 2,
            right_y + paddle_h / 2,
            PURPLE + (230,),
        )

    def _draw_ball(self, left, right, bottom, top) -> None:
        ball = self._ball()
        ball_x = left + (right - left) * ball[0]
        ball_y = bottom + (top - bottom) * ball[1]
        arcade.draw_circle_filled(ball_x, ball_y, BALL_R, (240, 250, 255, 245))
        arcade.draw_circle_outline(ball_x, ball_y, BALL_R + 6, (115, 233, 255, 110), 2)

    def _draw_text_layer(self) -> None:
        self._refresh_texts()

        self.title_label.x = self.window.width / 2
        self.title_label.y = self.window.height * 0.88
        self.title_label.draw()

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

    def _field_bounds(self) -> tuple[float, float, float, float]:
        width = self.window.width
        height = self.window.height
        return (
            width * 0.22,
            width * 0.78,
            height * 0.25,
            height * 0.64,
        )

    def _paddles(self) -> tuple[float, float]:
        if not self.state:
            return 0.5, 0.5

        players = self.state["players"]
        paddles = self.state["paddles"]
        return paddles[players[0]], paddles[players[1]]

    def _ball(self) -> tuple[float, float]:
        if not self.state:
            return 0.5, 0.5

        ball = self.state["ball"]
        return ball["x"], ball["y"]

    def _score_text(self) -> str:
        if not self.state:
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

    def _status_text(self) -> str:
        if self.error_text:
            return self.error_text

        if self.status == "leave":
            return tr("pong.leave")

        if self.state is None:
            return tr("pong.waiting")

        return tr("pong.playing")

    def _refresh_texts(self) -> None:
        super()._refresh_texts()
        self.status_label.text = self._status_text()
        self.start_button.text = tr("pong.start")
        self.back_button.text = tr("pong.back")
