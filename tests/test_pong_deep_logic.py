"""Углублённые модульные тесты игровой логики Pong."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_client import (
    PONG_BALL_MAX_SPEED_X,
    PONG_BALL_MAX_SPEED_Y,
    PONG_BALL_RADIUS,
    PONG_BALL_SPEED_X,
    PONG_PADDLE_OFFSET,
    pong_accelerate_ball,
    pong_initial_state,
    pong_process_ball,
    pong_speed_with_limit,
)


class PongDeepLogicTest(unittest.TestCase):
    """Тесты граничных случаев и физики Pong."""

    def test_ball_bounces_from_top_wall(self) -> None:
        """Мяч отскакивает от верхней границы поля."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["ball"]["y"] = 1 - PONG_BALL_RADIUS / 2
        state["ball"]["vy"] = 0.5

        pong_process_ball(state, 0.02)

        self.assertLess(state["ball"]["vy"], 0)
        self.assertLessEqual(state["ball"]["y"], 1 - PONG_BALL_RADIUS)

    def test_ball_bounces_from_bottom_wall(self) -> None:
        """Мяч отскакивает от нижней границы поля."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["ball"]["y"] = PONG_BALL_RADIUS / 2
        state["ball"]["vy"] = -0.5

        pong_process_ball(state, 0.02)

        self.assertGreater(state["ball"]["vy"], 0)
        self.assertGreaterEqual(state["ball"]["y"], PONG_BALL_RADIUS)

    def test_ball_bounces_from_left_paddle(self) -> None:
        """Мяч отскакивает от левой ракетки без изменения счёта."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["ball"]["x"] = PONG_PADDLE_OFFSET + 0.01
        state["ball"]["y"] = state["paddles"]["alice"]
        state["ball"]["vx"] = -1.0

        pong_process_ball(state, 0.02)

        self.assertGreater(state["ball"]["vx"], 0)
        self.assertEqual(state["score"], {"alice": 0, "bob": 0})

    def test_missing_left_paddle_gives_right_player_point(self) -> None:
        """Промах мимо левой ракетки начисляет очко правому игроку."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["ball"]["x"] = 0.01
        state["ball"]["y"] = 0.05
        state["ball"]["vx"] = -1.0
        state["paddles"]["alice"] = 0.95

        pong_process_ball(state, 0.02)

        self.assertEqual(state["score"]["bob"], 1)
        self.assertEqual(state["ball"]["x"], 0.5)
        self.assertEqual(state["ball"]["vx"], PONG_BALL_SPEED_X)

    def test_finished_game_does_not_move_ball(self) -> None:
        """Завершённая партия не обновляет положение мяча."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["winner"] = "alice"
        ball_before = state["ball"].copy()

        pong_process_ball(state, 1.0)

        self.assertEqual(state["ball"], ball_before)

    def test_speed_limit_keeps_direction_and_caps_value(self) -> None:
        """Ограничение скорости сохраняет направление и максимум."""

        self.assertEqual(
            pong_speed_with_limit(999.0, PONG_BALL_MAX_SPEED_X),
            PONG_BALL_MAX_SPEED_X,
        )
        self.assertEqual(
            pong_speed_with_limit(-999.0, PONG_BALL_MAX_SPEED_Y),
            -PONG_BALL_MAX_SPEED_Y,
        )

    def test_acceleration_caps_both_axes(self) -> None:
        """Ускорение мяча не превышает лимиты по обеим осям."""

        ball = {
            "x": 0.5,
            "y": 0.5,
            "vx": PONG_BALL_MAX_SPEED_X * 0.99,
            "vy": -PONG_BALL_MAX_SPEED_Y * 0.99,
        }

        pong_accelerate_ball(ball)

        self.assertEqual(ball["vx"], PONG_BALL_MAX_SPEED_X)
        self.assertEqual(ball["vy"], -PONG_BALL_MAX_SPEED_Y)


if __name__ == "__main__":
    unittest.main()
