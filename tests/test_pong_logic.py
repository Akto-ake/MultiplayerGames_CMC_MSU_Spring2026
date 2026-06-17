"""Модульные тесты игровой логики Pong."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_client import (
    PONG_BALL_SPEED_X,
    PONG_BALL_SPEED_Y,
    PONG_PADDLE_OFFSET,
    PONG_WIN_SCORE,
    pong_initial_state,
    pong_process_ball,
    pong_reset_ball,
)


class PongLogicTest(unittest.TestCase):
    """Тесты переходов состояния Pong."""

    def test_initial_state_has_centered_objects(self) -> None:
        """Начальное состояние Pong содержит центрированные объекты."""

        state = pong_initial_state(["alice", "bob"], round_id=3)

        self.assertEqual(state["round"], 3)
        self.assertEqual(state["paddles"], {"alice": 0.5, "bob": 0.5})
        self.assertEqual(state["score"], {"alice": 0, "bob": 0})
        self.assertEqual(state["winner"], None)
        self.assertEqual(state["ball"]["vx"], PONG_BALL_SPEED_X)
        self.assertEqual(state["ball"]["vy"], PONG_BALL_SPEED_Y)

    def test_ball_bounces_from_right_paddle_and_accelerates(self) -> None:
        """Мяч меняет направление и ускоряется после правой ракетки."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["ball"]["x"] = 1 - PONG_PADDLE_OFFSET - 0.01
        state["ball"]["y"] = state["paddles"]["bob"]
        state["ball"]["vx"] = 1.0
        state["ball"]["vy"] = 0.2

        pong_process_ball(state, 0.02)

        self.assertLess(state["ball"]["vx"], 0)
        self.assertGreater(abs(state["ball"]["vx"]), 1.0)
        self.assertEqual(state["score"], {"alice": 0, "bob": 0})

    def test_right_side_goal_gives_left_player_win(self) -> None:
        """Выход за правый край начисляет очко левому игроку."""

        state = pong_initial_state(["alice", "bob"], round_id=1)
        state["score"]["alice"] = PONG_WIN_SCORE - 1
        state["ball"]["x"] = 0.99
        state["ball"]["vx"] = 1.0

        pong_process_ball(state, 0.02)

        self.assertEqual(state["score"]["alice"], PONG_WIN_SCORE)
        self.assertEqual(state["winner"], "alice")
        self.assertEqual(state["paddles"], {"alice": 0.5, "bob": 0.5})

    def test_reset_ball_restores_base_speed(self) -> None:
        """Сброс мяча возвращает его в центр с базовой скоростью."""

        ball = {
            "x": 0.2,
            "y": 0.9,
            "vx": 1.2,
            "vy": 0.7,
        }

        pong_reset_ball(ball, direction=-1)

        self.assertEqual(ball["x"], 0.5)
        self.assertEqual(ball["y"], 0.5)
        self.assertEqual(ball["vx"], -PONG_BALL_SPEED_X)
        self.assertEqual(ball["vy"], -PONG_BALL_SPEED_Y)


if __name__ == "__main__":
    unittest.main()
