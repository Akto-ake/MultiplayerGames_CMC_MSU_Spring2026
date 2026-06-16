"""Frontend screen for network Pong."""

from __future__ import annotations

from typing import Callable

import arcade
import arcade.gui

try:
    from .frontend import Manager
    from .localization import tr, tr_error
    from .menu import (
        CYAN,
        PURPLE,
        NeonBaseView,
        build_menu_button_style,
        build_primary_button_style,
    )
except ImportError:
    from frontend import Manager
    from localization import tr, tr_error
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
PADDLE_SEND_INTERVAL = 0.02
LOCAL_PADDLE_HOLD_TIME = 0.15
STATE_SMOOTHING = 12.0


class PongView(NeonBaseView):
    """Экран сетевой игры Pong."""

    def __init__(self, player_name: str, on_back: Callable[[], None]):
        super().__init__()
        self.player_name = player_name
        self.on_back = on_back
        self.manager = Manager()

        self.state = None
        self.display_state = None
        self.nicks: list[str] = []
        self.lobby_id: int | None = None
        self.side: str | None = None
        self.status = "waiting"
        self.error_text = ""
        self.local_paddles = {
            "left": 0.5,
            "right": 0.5,
        }
        self.move_directions = {
            "left": 0,
            "right": 0,
        }
        self.paddle_send_timers = {
            "left": 0.0,
            "right": 0.0,
        }
        self.local_hold_timers = {
            "left": 0.0,
            "right": 0.0,
        }

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
            self._preview_restart()
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
            self.manager.push_message({"action": "leave_game"})
            self.on_back()

        controls.add(self.start_button)
        controls.add(self.back_button)
        self._add_centered_widget(controls, align_y=-300)
        self._add_locale_toggle()

    def on_update(self, delta_time: float) -> None:
        """Обновляет локальный ввод и состояние от backend."""

        self._consume_statuses()
        self._update_local_paddle(delta_time)
        self._smooth_display_state(delta_time)

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

        if key == arcade.key.W:
            self.move_directions["left"] = 1
            return

        if key == arcade.key.S:
            self.move_directions["left"] = -1
            return

        if key == arcade.key.UP:
            self.move_directions["right"] = 1
            return

        if key == arcade.key.DOWN:
            self.move_directions["right"] = -1
            return

        super().on_key_press(key, modifiers)

    def on_key_release(self, key: int, _modifiers: int) -> None:
        """Останавливает движение ракетки при отпускании клавиш."""

        if key in (arcade.key.W, arcade.key.S):
            self.move_directions["left"] = 0
            self.local_hold_timers["left"] = LOCAL_PADDLE_HOLD_TIME
            self._apply_local_paddle("left")
            self._send_paddle_position("left")

        if key in (arcade.key.UP, arcade.key.DOWN):
            self.move_directions["right"] = 0
            self.local_hold_timers["right"] = LOCAL_PADDLE_HOLD_TIME
            self._apply_local_paddle("right")
            self._send_paddle_position("right")

    def on_hide_view(self) -> None:
        """Сбрасывает ввод при уходе с экрана или потере активной игры."""

        self._reset_local_input()
        super().on_hide_view()

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
            self.error_text = tr_error(latest_error)

        if latest_status is None:
            return

        self.state = latest_status.get("state", self.state)
        self.nicks = latest_status.get("nicks", self.nicks)
        self.lobby_id = latest_status.get("lobby_id", self.lobby_id)
        self.side = latest_status.get("side", self.side)
        self.status = latest_status.get("status", self.status)
        self.error_text = ""

        if self.state is not None and self.status in ("start", "finished"):
            self._reset_local_input()
            self.display_state = self._copy_state(self.state)
            self._sync_local_paddles()
        elif self.display_state is None and self.state is not None:
            self.display_state = self._copy_state(self.state)
            self._sync_local_paddles()
        elif self.state is not None:
            self._sync_idle_local_paddles()

    def _update_local_paddle(self, delta_time: float) -> None:
        self._update_local_hold(delta_time)

        if self.state is None:
            return

        if self.state.get("winner") is not None:
            return

        for side_name, direction in self.move_directions.items():
            if direction == 0:
                self.paddle_send_timers[side_name] = PADDLE_SEND_INTERVAL
                continue

            self.local_paddles[side_name] += direction * PADDLE_SPEED * delta_time
            self.local_paddles[side_name] = min(
                max(self.local_paddles[side_name], 0.13),
                0.87,
            )
            self._apply_local_paddle(side_name)

            self.paddle_send_timers[side_name] += delta_time
            if self.paddle_send_timers[side_name] < PADDLE_SEND_INTERVAL:
                continue

            self.paddle_send_timers[side_name] = 0.0
            self._send_paddle_position(side_name)

    def _update_local_hold(self, delta_time: float) -> None:
        for side_name, time_left in self.local_hold_timers.items():
            if time_left <= 0.0:
                continue

            self.local_hold_timers[side_name] = max(0.0, time_left - delta_time)

    def _send_paddle_position(self, side_name: str) -> None:
        self.manager.push_message(
            {
                "game": "PONG",
                "action": "paddle",
                "round": self.state.get("round") if self.state else None,
                "side": side_name,
                "position": float(self.local_paddles[side_name]),
            }
        )

    def _apply_local_paddle(self, side_name: str) -> None:
        nick = self._side_nick(side_name)
        if self.state is None or nick is None:
            return

        self.state["paddles"][nick] = self.local_paddles[side_name]
        if self.display_state is not None:
            self.display_state["paddles"][nick] = self.local_paddles[side_name]

    def _sync_local_paddles(self) -> None:
        if self.state is None:
            return

        for side_name in ("left", "right"):
            nick = self._side_nick(side_name)
            if nick in self.state["paddles"]:
                self.local_paddles[side_name] = self.state["paddles"][nick]

    def _sync_idle_local_paddles(self) -> None:
        if self.state is None:
            return

        for side_name in ("left", "right"):
            if self.move_directions[side_name] != 0:
                continue

            if self.local_hold_timers[side_name] > 0.0:
                continue

            nick = self._side_nick(side_name)
            if nick in self.state["paddles"]:
                self.local_paddles[side_name] = self.state["paddles"][nick]

    def _smooth_display_state(self, delta_time: float) -> None:
        if self.state is None:
            return

        if self.display_state is None:
            self.display_state = self._copy_state(self.state)
            return

        amount = min(1.0, STATE_SMOOTHING * delta_time)
        for nick, position in self.state["paddles"].items():
            side_name = self._nick_side(nick)
            if side_name is not None and self._uses_local_paddle(side_name):
                self.display_state["paddles"][nick] = self.local_paddles[side_name]
                continue

            current = self.display_state["paddles"].get(nick, position)
            self.display_state["paddles"][nick] = self._lerp(
                current, position, amount
            )

        for axis in ("x", "y"):
            current = self.display_state["ball"][axis]
            target = self.state["ball"][axis]
            self.display_state["ball"][axis] = self._lerp(current, target, amount)

        self.display_state["score"] = self.state["score"].copy()
        self.display_state["winner"] = self.state.get("winner")

    def _uses_local_paddle(self, side_name: str) -> bool:
        if self.state is not None and self.state.get("winner") is not None:
            return False

        return (
            self.move_directions[side_name] != 0
            or self.local_hold_timers[side_name] > 0.0
        )

    def _reset_local_input(self) -> None:
        for side_name in ("left", "right"):
            self.move_directions[side_name] = 0
            self.local_hold_timers[side_name] = 0.0
            self.paddle_send_timers[side_name] = 0.0

    def _preview_restart(self) -> None:
        if self.state is None:
            return

        self._reset_local_input()
        players = self.state["players"]
        self.state = {
            "round": self.state.get("round", 0) + 1,
            "players": list(players),
            "paddles": {
                players[0]: 0.5,
                players[1]: 0.5,
            },
            "ball": {
                "x": 0.5,
                "y": 0.5,
                "vx": 0.0,
                "vy": 0.0,
            },
            "score": {
                players[0]: 0,
                players[1]: 0,
            },
            "winner": None,
        }
        self.display_state = self._copy_state(self.state)
        self._sync_local_paddles()

    @staticmethod
    def _copy_state(state: dict) -> dict:
        return {
            "players": list(state["players"]),
            "paddles": state["paddles"].copy(),
            "ball": state["ball"].copy(),
            "score": state["score"].copy(),
            "winner": state.get("winner"),
        }

    @staticmethod
    def _lerp(start: float, end: float, amount: float) -> float:
        return start + (end - start) * amount

    def _side_nick(self, side_name: str) -> str | None:
        state = self.state or self.display_state
        if not state:
            return None

        players = state["players"]
        if side_name == "left" and len(players) > 0:
            return players[0]
        if side_name == "right" and len(players) > 1:
            return players[1]
        return None

    def _nick_side(self, nick: str) -> str | None:
        state = self.state or self.display_state
        if not state:
            return None

        players = state["players"]
        if len(players) > 0 and nick == players[0]:
            return "left"
        if len(players) > 1 and nick == players[1]:
            return "right"
        return None

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
        state = self.display_state or self.state
        if not state:
            return 0.5, 0.5

        players = state["players"]
        paddles = state["paddles"]
        return paddles[players[0]], paddles[players[1]]

    def _ball(self) -> tuple[float, float]:
        state = self.display_state or self.state
        if not state:
            return 0.5, 0.5

        ball = state["ball"]
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

        winner = self.state.get("winner") if self.state is not None else None
        if winner is not None:
            return tr("pong.finished", winner=winner)

        if self.state is None:
            return tr("pong.waiting")

        return tr("pong.playing")

    def _refresh_texts(self) -> None:
        super()._refresh_texts()
        self.status_label.text = self._status_text()
        self.start_button.text = tr("pong.start")
        self.back_button.text = tr("pong.back")
