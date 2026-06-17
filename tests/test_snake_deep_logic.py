"""Углублённые модульные тесты игровой логики Snake."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_client import (
    SNAKE_COLS,
    SNAKE_ROWS,
    snake_initial_body,
    snake_initial_direction,
    snake_initial_state,
    snake_process_direction,
    snake_spawn_food,
    snake_step,
    snake_taken_cells,
)


class SnakeDeepLogicTest(unittest.TestCase):
    """Тесты граничных случаев и вспомогательной логики Snake."""

    def test_invalid_direction_is_ignored(self) -> None:
        """Некорректное направление не меняет ожидаемый ход змейки."""

        state = snake_initial_state(["alice", "bob"], round_id=1)

        snake_process_direction(state, "left", "diagonal")

        self.assertEqual(state["snakes"]["alice"]["pending_direction"], "right")

    def test_unknown_side_is_ignored(self) -> None:
        """Неизвестная сторона поля не меняет направления игроков."""

        state = snake_initial_state(["alice", "bob"], round_id=1)

        snake_process_direction(state, "center", "up")

        self.assertEqual(state["snakes"]["alice"]["pending_direction"], "right")
        self.assertEqual(state["snakes"]["bob"]["pending_direction"], "left")

    def test_wall_collision_resets_snake_without_score_loss(self) -> None:
        """Столкновение со стеной возвращает змейку на старт."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        state["score"]["alice"] = 2
        state["snakes"]["alice"]["body"] = [[SNAKE_COLS - 1, 7], [SNAKE_COLS - 2, 7]]
        state["snakes"]["alice"]["direction"] = "right"
        state["snakes"]["alice"]["pending_direction"] = "right"

        snake_step(state)

        self.assertEqual(state["score"]["alice"], 2)
        self.assertEqual(state["snakes"]["alice"]["body"], snake_initial_body("left"))
        self.assertEqual(
            state["snakes"]["alice"]["direction"],
            snake_initial_direction("left"),
        )

    def test_self_collision_resets_snake(self) -> None:
        """Столкновение с собой возвращает змейку на старт."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        state["snakes"]["alice"]["body"] = [[5, 5], [5, 6], [4, 6], [4, 5]]
        state["snakes"]["alice"]["direction"] = "left"
        state["snakes"]["alice"]["pending_direction"] = "up"

        snake_step(state)

        self.assertEqual(state["snakes"]["alice"]["body"], snake_initial_body("left"))
        self.assertEqual(state["snakes"]["alice"]["pending_direction"], "right")

    def test_spawn_food_uses_free_cell(self) -> None:
        """Еда создаётся только на свободной клетке поля."""

        state = snake_initial_state(["alice", "bob"], round_id=1)
        state["snakes"]["alice"]["body"] = [
            [col, row]
            for col in range(SNAKE_COLS)
            for row in range(SNAKE_ROWS)
            if [col, row] != [SNAKE_COLS - 1, SNAKE_ROWS - 1]
        ]
        state["snakes"]["bob"]["body"] = []

        food = snake_spawn_food(state, "alice")

        self.assertEqual(food, [SNAKE_COLS - 1, SNAKE_ROWS - 1])
        self.assertNotIn(tuple(food), snake_taken_cells(state))


if __name__ == "__main__":
    unittest.main()
