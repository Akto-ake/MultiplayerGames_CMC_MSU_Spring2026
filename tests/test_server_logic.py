"""Модульные тесты серверной логики лобби."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_server import (  # noqa: E402
    QUIZ_ROUND_SIZE,
    pong_main_lobby,
    quiz_build_round,
    quiz_main_lobby,
    snake_main_lobby,
)
from lib.server import Client, ClientServerError  # noqa: E402


class FakeLobby:
    """Минимальная замена серверного лобби для тестов."""

    def __init__(self, players: list[str], max_players: int = 2):
        """Создаёт fake-lobby с очередью входящих сообщений."""

        self.players = players
        self.max_players = max_players
        self.messages: asyncio.Queue = asyncio.Queue()
        self.sent: list[tuple[dict, list[str] | None]] = []

    async def pop_message(self):
        """Возвращает следующее сообщение для серверной логики."""

        return await self.messages.get()

    def push_message(self, message: dict, group: list[str] | None = None) -> None:
        """Сохраняет исходящее сообщение вместо отправки клиентам."""

        self.sent.append((message, group))

    def get_list_nicks(self) -> list[str]:
        """Возвращает отсортированный список игроков."""

        return sorted(self.players)

    async def send(self, nick: str, target: str, status: str, message=None) -> None:
        """Кладёт входящее сообщение в очередь лобби."""

        payload = {
            "target": target,
            "status": status,
        }
        if message is not None:
            payload["message"] = message

        await self.messages.put((nick, payload))


async def wait_for_sent(
    lobby: FakeLobby,
    count: int,
) -> list[tuple[dict, list[str] | None]]:
    """Ждёт, пока лобби накопит нужное число исходящих сообщений."""

    for _ in range(100):
        if len(lobby.sent) >= count:
            return lobby.sent

        await asyncio.sleep(0.01)

    raise AssertionError(f"expected {count} sent messages, got {len(lobby.sent)}")


class ServerMainFunctionTest(unittest.IsolatedAsyncioTestCase):
    """Тесты серверных функций игровых лобби."""

    async def run_lobby(self, lobby_func, lobby: FakeLobby):
        """Запускает лобби и возвращает задачу для последующей отмены."""

        task = asyncio.create_task(lobby_func(lobby))
        await asyncio.sleep(0)
        return task

    async def stop_lobby(self, task: asyncio.Task) -> None:
        """Останавливает бесконечную серверную функцию лобби."""

        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_pong_start_requires_two_players(self) -> None:
        """Pong не стартует, пока в лобби нет двух игроков."""

        lobby = FakeLobby(["alice"])
        task = await self.run_lobby(pong_main_lobby, lobby)

        try:
            await lobby.send("alice", "client", "start")
            sent = await wait_for_sent(lobby, 1)
        finally:
            await self.stop_lobby(task)

        message, group = sent[0]
        self.assertEqual(message["status"], "error")
        self.assertEqual(message["message"], "not enough players")
        self.assertEqual(group, ["alice"])

    async def test_pong_starts_next_round_after_finish(self) -> None:
        """Pong запускает новую партию после завершения предыдущей."""

        lobby = FakeLobby(["alice", "bob"])
        task = await self.run_lobby(pong_main_lobby, lobby)

        try:
            await lobby.send("alice", "client", "start")
            await wait_for_sent(lobby, 1)
            await lobby.send("alice", "client", "round_finished")
            await asyncio.sleep(0.01)
            await lobby.send("alice", "client", "start")
            sent = await wait_for_sent(lobby, 2)
        finally:
            await self.stop_lobby(task)

        starts = [message for message, _group in sent if message["status"] == "start"]
        self.assertEqual([start["message"]["round"] for start in starts], [1, 2])
        self.assertEqual(starts[0]["message"]["host"], "alice")

    async def test_snake_forwards_client_messages_during_game(self) -> None:
        """Змейка пересылает игровые сообщения после старта партии."""

        lobby = FakeLobby(["alice", "bob"])
        task = await self.run_lobby(snake_main_lobby, lobby)
        direction = {
            "target": "client",
            "status": "direction",
            "message": {"side": "left", "direction": "up"},
        }

        try:
            await lobby.send("alice", "client", "start")
            await wait_for_sent(lobby, 1)
            await lobby.messages.put(("alice", direction))
            sent = await wait_for_sent(lobby, 2)
        finally:
            await self.stop_lobby(task)

        self.assertEqual(sent[1], (direction, None))

    async def test_quiz_scores_answers_and_finishes_round(self) -> None:
        """Quiz считает ответы игроков и завершает раунд."""

        lobby = FakeLobby(["alice", "bob"])
        question = {
            "question": "quiz.question.test",
            "correct": "quiz.answer.correct",
            "options": [
                "quiz.answer.correct",
                "quiz.answer.wrong_one",
                "quiz.answer.wrong_two",
                "quiz.answer.wrong_three",
            ],
        }

        with patch(
            "lib.main_function_for_server.quiz_build_round",
            return_value=[question],
        ):
            task = await self.run_lobby(quiz_main_lobby, lobby)

            try:
                await lobby.send("alice", "client", "start")
                await wait_for_sent(lobby, 1)
                await lobby.send("alice", "client", "answer", 0)
                await wait_for_sent(lobby, 2)
                await lobby.send("bob", "client", "answer", 1)
                await wait_for_sent(lobby, 4)
                await lobby.send("alice", "client", "next")
                sent = await wait_for_sent(lobby, 5)
            finally:
                await self.stop_lobby(task)

        answered = sent[3][0]
        finished = sent[4][0]
        self.assertEqual(answered["status"], "answered")
        self.assertEqual(answered["message"]["scores"], {"alice": 1, "bob": 0})
        self.assertEqual(
            answered["message"]["correct_answers"][0]["correct"],
            "quiz.answer.correct",
        )
        self.assertEqual(finished["status"], "finished")

    def test_quiz_build_round_uses_translation_keys(self) -> None:
        """Раунд Quiz состоит из ключей локализации."""

        questions = quiz_build_round()

        self.assertLessEqual(len(questions), QUIZ_ROUND_SIZE)
        self.assertGreater(len(questions), 0)

        for question in questions:
            self.assertTrue(question["question"].startswith("quiz.question."))
            self.assertTrue(question["correct"].startswith("quiz.answer."))
            self.assertIn(question["correct"], question["options"])
            self.assertEqual(len(question["options"]), 4)
            for option in question["options"]:
                self.assertTrue(option.startswith("quiz.answer."))


class ClientGameTest(unittest.IsolatedAsyncioTestCase):
    """Тесты локального объекта игры клиента."""

    async def test_game_without_run_func_raises_error(self) -> None:
        """Игра без локальной функции запуска возвращает ошибку."""

        game = Client.Game(Client(), lobby_id=1234, game_name="PONG")

        with self.assertRaisesRegex(
            ClientServerError,
            "game run function is not set",
        ):
            await game.run()

    def test_game_process_message_updates_nicks(self) -> None:
        """Служебные сообщения joined/leave обновляют список игроков."""

        game = Client.Game(Client(), lobby_id=1234, game_name="PONG")

        game.process_message({"status": "joined", "message": "bob"})
        game.process_message({"status": "joined", "message": "alice"})
        game.process_message({"status": "joined", "message": "alice"})
        game.process_message({"status": "leave", "message": "bob"})

        self.assertEqual(game.nicks, ["alice"])


if __name__ == "__main__":
    unittest.main()
