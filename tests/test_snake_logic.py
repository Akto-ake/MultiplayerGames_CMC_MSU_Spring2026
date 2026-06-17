"""Модульные тесты игровой логики Snake."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_client import (
    SNAKE_WIN_SCORE,
    snake_initial_body,
    snake_initial_state,
    snake_process_direction,
    snake_step,
)


class SnakeLogicTest(unittest.TestCase):
    """Тесты чистых переходов состояния Snake."""

    def test_initial_state_places_two_snakes(self) -> None:
        """Начальное состояние Snake создаёт двух игроков, счёт и еду."""

        state = snake_initial_state(["alice", "bob"], round_id=4)

        self.assertEqual(state["round"], 4)
        self.assertEqual(state["players"], ["alice", "bob"])
        self.assertEqual(state["score"], {"alice": 0, "bob": 0})
        self.assertFalse(state["paused"])
        self.assertIsNone(state["winner"])
        self.assertEqual(state["snakes"]["alice"]["body"], snake_initial_body("left"))
        self.assertEqual(state["snakes"]["bob"]["body"], snake_initial_body("right"))

    def test_opposite_direction_is_ignored(self) -> None:
        """Змейка не может сразу развернуться в обратную сторону."""

        state = snake_initial_state(["alice", "bob"], round_id=1)

        snake_process_direction(state, "left", "left")

        self.assertEqual(state["snakes"]["alice"]["pending_direction"], "right")

    def test_eating_food_increases_score_and_length(self) -> None:
        """Поедание еды увеличивает счёт и длину змейки."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        head = state["snakes"]["alice"]["body"][0]
        state["snakes"]["alice"]["food"] = [head[0] + 1, head[1]]
        old_length = len(state["snakes"]["alice"]["body"])

        snake_step(state)

        self.assertEqual(state["score"]["alice"], 1)
        self.assertEqual(len(state["snakes"]["alice"]["body"]), old_length + 1)

    def test_fifth_point_finishes_game(self) -> None:
        """Игра завершается, когда змейка набирает победный счёт."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        state["score"]["alice"] = SNAKE_WIN_SCORE - 1
        head = state["snakes"]["alice"]["body"][0]
        state["snakes"]["alice"]["food"] = [head[0] + 1, head[1]]

        snake_step(state)

        self.assertEqual(state["score"]["alice"], SNAKE_WIN_SCORE)
        self.assertEqual(state["winner"], "alice")

    def test_pause_blocks_movement(self) -> None:
        """Пауза останавливает движение змейки."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        state["paused"] = True
        head = state["snakes"]["alice"]["body"][0][:]

        snake_step(state)

        self.assertEqual(state["snakes"]["alice"]["body"][0], head)


if __name__ == "__main__":
    unittest.main()
