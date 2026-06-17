"""Дополнительные тесты клиентской логики игр."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.frontend import Manager  # noqa: E402
from lib.main_function_for_client import (  # noqa: E402
    PONG_WIN_SCORE,
    SNAKE_COLS,
    SNAKE_ROWS,
    pong_initial_state,
    pong_process_ball,
    pong_push,
    pong_run,
    snake_initial_state,
    snake_push,
    snake_run,
    snake_side_nick,
    snake_spawn_food,
    snake_step,
    snake_taken_cells,
)
from lib.server import ClientServerError  # noqa: E402


async def wait_until(predicate, timeout=1.0) -> None:
    """Ждёт выполнения условия в асинхронном игровом цикле."""

    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


def clear_manager() -> None:
    """Очищает общие очереди frontend/backend между тестами."""

    Manager.queue_message.clear()
    Manager.queue_status.clear()


class FakeRunGame:
    """Минимальная реализация Game для run-функций клиента."""

    def __init__(self, nick: str = "first"):
        """Создаёт fake-game с очередью серверных сообщений."""

        self.client = SimpleNamespace(nick=nick)
        self.lobby_id = 9001
        self.nicks = ["first", "second"]
        self.incoming = asyncio.Queue()
        self.sent = []
        self.left = False

    async def get_nicks(self):
        """Возвращает игроков лобби."""

        return self.nicks

    async def pop_message(self):
        """Возвращает следующее сообщение сервера."""

        message = await self.incoming.get()
        status = message.get("status")
        nick = message.get("message")

        if status == "joined" and nick not in self.nicks:
            self.nicks.append(nick)
            self.nicks.sort()

        if status == "leave" and nick in self.nicks:
            self.nicks.remove(nick)

        return message

    async def push_message(self, message):
        """Сохраняет сообщение, которое клиент отправил серверу."""

        self.sent.append(message)

    async def leave(self):
        """Отмечает выход из игры."""

        self.left = True

    def get_id(self):
        """Возвращает ID лобби."""

        return self.lobby_id


class ClientPushAndPureLogicTest(unittest.TestCase):
    """Тесты push-функций и недостающих чистых веток."""

    def setUp(self) -> None:
        """Очищает очереди перед тестом."""

        clear_manager()

    def tearDown(self) -> None:
        """Очищает очереди после теста."""

        clear_manager()

    def test_pong_push_sends_frontend_payload(self) -> None:
        """pong_push отправляет состояние Pong во frontend."""

        manager = Manager()
        game = SimpleNamespace(nicks=["first", "second"], get_id=lambda: 1234)
        state = pong_initial_state(["first", "second"], round_id=1)

        pong_push(manager, game, state, "left", "move")
        status, error = manager.pop_status()

        self.assertIsNone(error)
        self.assertEqual(status["game"], "PONG")
        self.assertEqual(status["state"], state)
        self.assertEqual(status["nicks"], ["first", "second"])
        self.assertEqual(status["lobby_id"], 1234)
        self.assertEqual(status["side"], "left")
        self.assertEqual(status["status"], "move")

    def test_snake_push_sends_frontend_payload(self) -> None:
        """snake_push отправляет состояние Snake во frontend."""

        manager = Manager()
        game = SimpleNamespace(nicks=["first", "second"], get_id=lambda: 4321)
        state = snake_initial_state(["first", "second"], round_id=2)

        snake_push(manager, game, state, "right", "start")
        status, error = manager.pop_status()

        self.assertIsNone(error)
        self.assertEqual(status["game"], "SNAKE")
        self.assertEqual(status["state"], state)
        self.assertEqual(status["nicks"], ["first", "second"])
        self.assertEqual(status["lobby_id"], 4321)
        self.assertEqual(status["side"], "right")
        self.assertEqual(status["status"], "start")

    def test_pong_left_side_goal_can_finish_right_player(self) -> None:
        """Гол в левую сторону может завершить Pong победой правого игрока."""

        state = pong_initial_state(["first", "second"], round_id=1)
        state["score"]["second"] = PONG_WIN_SCORE - 1
        state["ball"]["x"] = 0.01
        state["ball"]["vx"] = -1.0
        state["paddles"]["first"] = 0.95

        pong_process_ball(state, 0.02)

        self.assertEqual(state["score"]["second"], PONG_WIN_SCORE)
        self.assertEqual(state["winner"], "second")
        self.assertEqual(state["paddles"], {"first": 0.5, "second": 0.5})

    def test_snake_helpers_cover_right_side_and_exclusions(self) -> None:
        """Snake helpers возвращают правую сторону и умеют исключать игрока."""

        state = snake_initial_state(["first", "second"], round_id=1)

        self.assertEqual(snake_side_nick(state, "right"), "second")

        taken_without_first = snake_taken_cells(state, excluded_nick="first")
        self.assertNotIn(
            tuple(state["snakes"]["first"]["body"][0]),
            taken_without_first,
        )
        self.assertIn(tuple(state["snakes"]["second"]["body"][0]), taken_without_first)

    def test_snake_spawn_food_returns_zero_when_board_is_full(self) -> None:
        """Еда Snake возвращается в [0, 0], если свободных клеток нет."""

        state = snake_initial_state(["first", "second"], round_id=1)
        state["snakes"]["first"]["body"] = [
            [col, row]
            for col in range(SNAKE_COLS)
            for row in range(SNAKE_ROWS)
        ]
        state["snakes"]["second"]["body"] = []

        self.assertEqual(snake_spawn_food(state, "first"), [0, 0])

    def test_snake_finished_state_does_not_move(self) -> None:
        """Завершённая Snake-партия не двигает змейку."""

        state = snake_initial_state(["first", "second"], round_id=1)
        state["winner"] = "first"
        head = state["snakes"]["first"]["body"][0][:]

        snake_step(state)

        self.assertEqual(state["snakes"]["first"]["body"][0], head)


class ClientRunLoopTest(unittest.IsolatedAsyncioTestCase):
    """Тесты коротких сценариев async run-функций клиента."""

    async def asyncSetUp(self) -> None:
        """Очищает очереди перед async-тестом."""

        clear_manager()

    async def asyncTearDown(self) -> None:
        """Очищает очереди после async-теста."""

        clear_manager()

    async def test_pong_run_processes_start_and_paddle_messages(self) -> None:
        """pong_run обрабатывает старт и перемещение ракетки."""

        game = FakeRunGame()
        manager = Manager()
        run_task = asyncio.create_task(pong_run(game))

        try:
            await wait_until(lambda: len(Manager.queue_status) > 0)
            Manager.queue_status.clear()

            await game.incoming.put(
                {
                    "status": "start",
                    "message": {
                        "players": ["first", "second"],
                        "host": "first",
                        "round": 1,
                    },
                }
            )
            await wait_until(
                lambda: any(
                    status and status.get("status") == "start"
                    for status, _error in Manager.queue_status
                )
            )
            Manager.queue_status.clear()

            manager.push_message(
                {
                    "game": "PONG",
                    "action": "paddle",
                    "round": 1,
                    "side": "right",
                    "position": 2.0,
                }
            )
            await wait_until(
                lambda: any(message.get("status") == "paddle" for message in game.sent)
            )

            await game.incoming.put(
                {
                    "status": "paddle",
                    "message": {
                        "round": 1,
                        "side": "right",
                        "position": 2.0,
                    },
                }
            )
            await wait_until(
                lambda: any(
                    status
                    and status.get("state")
                    and status["state"]["paddles"]["second"] == 0.87
                    for status, _error in Manager.queue_status
                )
            )
        finally:
            manager.push_message({"action": "leave_game"})
            await asyncio.wait_for(run_task, timeout=1.0)

        self.assertTrue(game.left)

    async def test_pong_run_raises_server_error(self) -> None:
        """pong_run пробрасывает ошибку сервера."""

        game = FakeRunGame()
        run_task = asyncio.create_task(pong_run(game))

        await wait_until(lambda: len(Manager.queue_status) > 0)
        Manager.queue_status.clear()
        await game.incoming.put({"status": "error", "message": "boom"})

        with self.assertRaisesRegex(ClientServerError, "boom"):
            await asyncio.wait_for(run_task, timeout=1.0)

    async def test_snake_run_processes_start_pause_and_direction(self) -> None:
        """snake_run обрабатывает старт, паузу и направление."""

        game = FakeRunGame()
        manager = Manager()
        run_task = asyncio.create_task(snake_run(game))

        try:
            await wait_until(lambda: len(Manager.queue_status) > 0)
            Manager.queue_status.clear()

            await game.incoming.put(
                {
                    "status": "start",
                    "message": {
                        "players": ["first", "second"],
                        "host": "first",
                        "round": 1,
                    },
                }
            )
            await wait_until(
                lambda: any(
                    status and status.get("status") == "start"
                    for status, _error in Manager.queue_status
                )
            )

            manager.push_message(
                {
                    "game": "SNAKE",
                    "action": "direction",
                    "round": 1,
                    "side": "left",
                    "direction": "up",
                }
            )
            await wait_until(
                lambda: any(
                    message.get("status") == "direction" for message in game.sent
                )
            )

            await game.incoming.put(
                {
                    "status": "direction",
                    "message": {
                        "round": 1,
                        "side": "left",
                        "direction": "up",
                    },
                }
            )
            await asyncio.sleep(0.03)

            manager.push_message({"game": "SNAKE", "action": "pause", "round": 1})
            await wait_until(
                lambda: any(message.get("status") == "pause" for message in game.sent)
            )
            await game.incoming.put({"status": "pause", "message": {"round": 1}})
            await wait_until(
                lambda: any(
                    status
                    and status.get("state")
                    and status["state"].get("paused")
                    for status, _error in Manager.queue_status
                )
            )
        finally:
            manager.push_message({"action": "leave_game"})
            await asyncio.wait_for(run_task, timeout=1.0)

        self.assertTrue(game.left)

    async def test_snake_run_raises_server_error(self) -> None:
        """snake_run пробрасывает ошибку сервера."""

        game = FakeRunGame()
        run_task = asyncio.create_task(snake_run(game))

        await wait_until(lambda: len(Manager.queue_status) > 0)
        Manager.queue_status.clear()
        await game.incoming.put({"status": "error", "message": "snake boom"})

        with self.assertRaisesRegex(ClientServerError, "snake boom"):
            await asyncio.wait_for(run_task, timeout=1.0)


if __name__ == "__main__":
    unittest.main()
