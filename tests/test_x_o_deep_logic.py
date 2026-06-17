"""Углублённые модульные тесты игровой логики X/O."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.frontend import Manager
from lib.main_function_for_client import x_o_run
from lib.server import ClientServerError


async def wait_until(predicate, timeout=1.0) -> None:
    """Ждёт выполнения условия в асинхронном игровом цикле."""

    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


def clear_manager() -> None:
    """Очищает общие очереди frontend/backend между тестами."""

    Manager.queue_message.clear()
    Manager.queue_status.clear()


class FakeGame:
    """Минимальная реализация Game для проверки клиентской логики X/O."""

    def __init__(self):
        self.client = SimpleNamespace(nick="first")
        self.lobby_id = 1234
        self.nicks = ["first", "second"]
        self.incoming = asyncio.Queue()
        self.sent = []
        self.left = False

    async def get_nicks(self):
        return self.nicks

    async def pop_message(self):
        message = await self.incoming.get()
        if message.get("status") == "joined":
            nick = message["message"]
            if nick not in self.nicks:
                self.nicks.append(nick)
                self.nicks.sort()
        elif message.get("status") == "leave":
            self.nicks.remove(message["message"])
        return message

    async def push_message(self, message):
        self.sent.append(message)

    async def leave(self):
        self.left = True

    def get_id(self):
        return self.lobby_id


class XoDeepLogicTest(unittest.IsolatedAsyncioTestCase):
    """Тесты граничных случаев клиентской логики X/O."""

    async def asyncSetUp(self):
        clear_manager()

    async def asyncTearDown(self):
        clear_manager()

    async def start_round(self):
        """Запускает клиентскую X/O партию с первым игроком в роли X."""

        game = FakeGame()
        run_task = asyncio.create_task(x_o_run(game))

        await wait_until(lambda: len(Manager.queue_status) > 0)
        Manager.queue_status.clear()

        await game.incoming.put({"status": "start", "message": "first"})
        await wait_until(
            lambda: any(
                status and status.get("status") == "start"
                for status, _error in Manager.queue_status
            )
        )
        Manager.queue_status.clear()

        return game, run_task

    async def test_wrong_turn_message_raises_protocol_error(self) -> None:
        """Сообщение хода не от текущего игрока считается ошибкой протокола."""

        game, run_task = await self.start_round()

        await game.incoming.put(
            {
                "status": "move",
                "message": {
                    "nick": "second",
                    "row": 0,
                    "col": 0,
                    "symbol": "O",
                },
            }
        )

        with self.assertRaisesRegex(ClientServerError, "wrong turn"):
            await asyncio.wait_for(run_task, timeout=1.0)

    async def test_wrong_symbol_message_raises_protocol_error(self) -> None:
        """Сообщение с неверным символом игрока считается ошибкой протокола."""

        game, run_task = await self.start_round()

        await game.incoming.put(
            {
                "status": "move",
                "message": {
                    "nick": "first",
                    "row": 0,
                    "col": 0,
                    "symbol": "O",
                },
            }
        )

        with self.assertRaisesRegex(ClientServerError, "wrong symbol"):
            await asyncio.wait_for(run_task, timeout=1.0)

    async def test_remote_move_to_busy_cell_raises_protocol_error(self) -> None:
        """Серверный ход в занятую клетку с другим символом отклоняется."""

        game, run_task = await self.start_round()

        await game.incoming.put(
            {
                "status": "move",
                "message": {
                    "nick": "first",
                    "row": 0,
                    "col": 0,
                    "symbol": "X",
                },
            }
        )
        await wait_until(
            lambda: any(
                status
                and status.get("board", [[""]])[0][0] == "X"
                and status.get("turn") == "second"
                for status, _error in Manager.queue_status
            )
        )
        Manager.queue_status.clear()

        await game.incoming.put(
            {
                "status": "move",
                "message": {
                    "nick": "second",
                    "row": 0,
                    "col": 0,
                    "symbol": "O",
                },
            }
        )

        with self.assertRaisesRegex(ClientServerError, "cell is busy"):
            await asyncio.wait_for(run_task, timeout=1.0)

    async def test_full_board_without_winner_finishes_as_draw(self) -> None:
        """Заполненное поле без победителя завершает раунд ничьей."""

        game, run_task = await self.start_round()
        moves = [
            ("first", 0, 0, "X"),
            ("second", 0, 1, "O"),
            ("first", 0, 2, "X"),
            ("second", 1, 1, "O"),
            ("first", 1, 0, "X"),
            ("second", 1, 2, "O"),
            ("first", 2, 1, "X"),
            ("second", 2, 0, "O"),
            ("first", 2, 2, "X"),
        ]

        for nick, row, col, symbol in moves:
            await game.incoming.put(
                {
                    "status": "move",
                    "message": {
                        "nick": nick,
                        "row": row,
                        "col": col,
                        "symbol": symbol,
                    },
                }
            )

        await wait_until(
            lambda: any(
                status and status.get("status") == "draw"
                for status, _error in Manager.queue_status
            )
        )

        self.assertEqual(game.sent[-1], {"status": "round_finished"})

        Manager().push_message({"action": "leave_game"})
        await asyncio.wait_for(run_task, timeout=1.0)


if __name__ == "__main__":
    unittest.main()
