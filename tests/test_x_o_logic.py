"""Модульные тесты игровой логики X/O."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.frontend import Manager
from lib.main_function_for_client import X_O_EMPTY, x_o_parse_move, x_o_push, x_o_win


def clear_manager() -> None:
    """Очищает общие очереди frontend/backend между тестами."""

    Manager.queue_message.clear()
    Manager.queue_status.clear()


class XoLogicTest(unittest.TestCase):
    """Тесты функций крестиков-ноликов."""

    def setUp(self) -> None:
        clear_manager()

    def tearDown(self) -> None:
        clear_manager()

    def test_row_column_and_diagonal_wins_are_detected(self) -> None:
        """Победа определяется по строке, столбцу и диагоналям."""

        self.assertEqual(
            x_o_win(
                [
                    ["X", "X", "X"],
                    [X_O_EMPTY, "O", X_O_EMPTY],
                    ["O", X_O_EMPTY, X_O_EMPTY],
                ]
            ),
            "X",
        )
        self.assertEqual(
            x_o_win(
                [
                    ["O", "X", X_O_EMPTY],
                    ["O", "X", X_O_EMPTY],
                    ["O", X_O_EMPTY, "X"],
                ]
            ),
            "O",
        )
        self.assertEqual(
            x_o_win(
                [
                    ["X", "O", X_O_EMPTY],
                    ["O", "X", X_O_EMPTY],
                    [X_O_EMPTY, "O", "X"],
                ]
            ),
            "X",
        )
        self.assertEqual(
            x_o_win(
                [
                    ["O", "X", "X"],
                    ["O", "X", X_O_EMPTY],
                    ["X", X_O_EMPTY, "O"],
                ]
            ),
            "X",
        )

    def test_empty_and_mixed_lines_do_not_win(self) -> None:
        """Пустая или смешанная линия не считается победой."""

        self.assertIsNone(
            x_o_win(
                [
                    [X_O_EMPTY, X_O_EMPTY, X_O_EMPTY],
                    ["X", "O", "X"],
                    ["O", "X", "O"],
                ]
            )
        )

    def test_parse_move_accepts_dict_pair_and_nested_message(self) -> None:
        """Ход разбирается из dict, пары и вложенного сообщения."""

        self.assertEqual(x_o_parse_move({"row": 1, "col": 2}), (1, 2))
        self.assertEqual(x_o_parse_move([0, 1]), [0, 1])
        self.assertEqual(
            x_o_parse_move(("move", {"row": 2, "col": 0}, "meta")),
            (2, 0),
        )
        self.assertIsNone(x_o_parse_move("bad move"))

    def test_push_copies_board_and_sends_common_payload(self) -> None:
        """Отправка статуса копирует поле и добавляет служебные данные."""

        manager = Manager()
        game = SimpleNamespace(nicks=["alice", "bob"], get_id=lambda: 4321)
        board = [
            ["X", X_O_EMPTY, X_O_EMPTY],
            [X_O_EMPTY, "O", X_O_EMPTY],
            [X_O_EMPTY, X_O_EMPTY, X_O_EMPTY],
        ]

        x_o_push(manager, game, board, "X", "alice", "move")
        board[0][0] = "O"

        status, error = manager.pop_status()

        self.assertIsNone(error)
        self.assertEqual(status["game"], "X_O")
        self.assertEqual(status["board"][0][0], "X")
        self.assertEqual(status["nicks"], ["alice", "bob"])
        self.assertEqual(status["lobby_id"], 4321)
        self.assertEqual(status["symbol"], "X")
        self.assertEqual(status["turn"], "alice")
        self.assertEqual(status["status"], "move")


if __name__ == "__main__":
    unittest.main()
