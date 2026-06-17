"""Углублённые модульные тесты игровой логики Quiz."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.frontend import Manager
from lib.main_function_for_client import quiz_run
from lib.main_function_for_server import quiz_main_lobby
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


class FakeQuizLobby:
    """Минимальная реализация lobby для серверной логики викторины."""

    def __init__(self, players=None):
        self.players = sorted(players or ["first", "second"])
        self.max_players = 2
        self.incoming = asyncio.Queue()
        self.outgoing = []

    async def pop_message(self):
        return await self.incoming.get()

    def push_message(self, message, group=None):
        self.outgoing.append((message, group))

    def get_list_nicks(self):
        return list(self.players)

    async def send(self, nick, status, message=None):
        payload = {
            "target": "client",
            "status": status,
        }
        if message is not None:
            payload["message"] = message
        await self.incoming.put((nick, payload))

    def last_message(self):
        return self.outgoing[-1][0]


class FakeQuizGame:
    """Минимальная реализация Game для клиентской логики Quiz."""

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


class QuizDeepLogicTest(unittest.IsolatedAsyncioTestCase):
    """Тесты серверной и клиентской логики Quiz."""

    async def asyncSetUp(self):
        clear_manager()

    async def asyncTearDown(self):
        clear_manager()

    async def start_server_round(self):
        """Запускает серверную корутину и стартует раунд."""

        lobby = FakeQuizLobby()
        lobby_task = asyncio.create_task(quiz_main_lobby(lobby))
        await lobby.send("first", "start")
        await wait_until(lambda: len(lobby.outgoing) == 1)
        return lobby, lobby_task

    async def stop_lobby(self, lobby_task) -> None:
        """Останавливает бесконечную серверную корутину."""

        lobby_task.cancel()
        try:
            await lobby_task
        except asyncio.CancelledError:
            pass

    async def test_start_without_second_player_keeps_waiting(self) -> None:
        """Старт без второго игрока возвращает waiting только инициатору."""

        lobby = FakeQuizLobby(players=["first"])
        lobby_task = asyncio.create_task(quiz_main_lobby(lobby))

        try:
            await lobby.send("first", "start")
            await wait_until(lambda: len(lobby.outgoing) == 1)

            message, group = lobby.outgoing[-1]
            self.assertEqual(message["status"], "waiting")
            self.assertEqual(group, ["first"])
        finally:
            await self.stop_lobby(lobby_task)

    async def test_both_answers_finish_question_and_next_moves_forward(self) -> None:
        """Два ответа завершают вопрос, а next открывает следующий."""

        lobby, lobby_task = await self.start_server_round()

        try:
            first_question = lobby.last_message()["message"]["question"]
            await lobby.send("first", "answer", 0)
            await wait_until(lambda: lobby.last_message()["status"] == "answer")

            await lobby.send("second", "answer", 1)
            await wait_until(lambda: lobby.last_message()["status"] == "answered")

            answered_payload = lobby.last_message()["message"]
            self.assertEqual(answered_payload["answers"], {"first": 0, "second": 1})
            self.assertEqual(len(answered_payload["correct_answers"]), 1)

            await lobby.send("first", "next")
            await wait_until(
                lambda: lobby.last_message()["status"] == "question"
                and lobby.last_message()["message"]["question_index"] == 1
            )

            next_payload = lobby.last_message()["message"]
            self.assertEqual(next_payload["answers"], {})
            self.assertNotEqual(next_payload["question"], first_question)
        finally:
            await self.stop_lobby(lobby_task)

    async def test_revote_after_both_answers_recalculates_scores(self) -> None:
        """Переголосование после двух ответов обновляет ответы и счёт."""

        lobby, lobby_task = await self.start_server_round()

        try:
            options = lobby.last_message()["message"]["options"]

            await lobby.send("first", "answer", 0)
            await wait_until(lambda: lobby.last_message()["status"] == "answer")
            await lobby.send("second", "answer", 1)
            await wait_until(lambda: lobby.last_message()["status"] == "answered")

            answered_payload = lobby.last_message()["message"]
            correct = answered_payload["correct_answers"][0]["correct"]
            correct_index = options.index(correct)
            await lobby.send("first", "answer", correct_index)
            await wait_until(
                lambda: lobby.last_message()["status"] == "answered"
                and lobby.last_message()["message"]["answers"]["first"] == correct_index
            )

            payload = lobby.last_message()["message"]
            self.assertEqual(payload["answers"]["first"], correct_index)
            self.assertEqual(payload["scores"]["first"], 1)
        finally:
            await self.stop_lobby(lobby_task)

    async def test_next_after_last_question_finishes_game(self) -> None:
        """После последнего вопроса next переводит игру в finished."""

        lobby, lobby_task = await self.start_server_round()

        try:
            total = lobby.last_message()["message"]["total_questions"]
            for question_index in range(total):
                await lobby.send("first", "answer", 0)
                await wait_until(lambda: lobby.last_message()["status"] == "answer")
                await lobby.send("second", "answer", 1)
                await wait_until(lambda: lobby.last_message()["status"] == "answered")

                await lobby.send("first", "next")
                expected_status = (
                    "finished" if question_index == total - 1 else "question"
                )
                await wait_until(
                    lambda: lobby.last_message()["status"] == expected_status
                )

            final_payload = lobby.last_message()["message"]
            self.assertEqual(lobby.last_message()["status"], "finished")
            self.assertEqual(len(final_payload["correct_answers"]), total)
        finally:
            await self.stop_lobby(lobby_task)

    async def test_client_sends_start_answer_next_and_leave(self) -> None:
        """Клиентская прокладка отправляет команды Quiz в Game."""

        game = FakeQuizGame()
        manager = Manager()
        run_task = asyncio.create_task(quiz_run(game))

        await wait_until(lambda: len(Manager.queue_status) > 0)
        Manager.queue_status.clear()

        manager.push_message("start")
        await wait_until(lambda: game.sent == [{"status": "start"}])

        payload = {
            "players": ["first", "second"],
            "question_index": 0,
            "total_questions": 5,
            "question": "quiz.question.test",
            "options": ["a", "b", "c", "d"],
            "answers": {},
            "scores": {"first": 0, "second": 0},
            "correct_answers": [],
        }
        await game.incoming.put({"status": "question", "message": payload})
        await wait_until(
            lambda: any(
                status and status.get("status") == "question"
                for status, _error in Manager.queue_status
            )
        )

        manager.push_message({"action": "answer", "answer": 2})
        await wait_until(lambda: game.sent[-1] == {"status": "answer", "message": 2})

        manager.push_message({"action": "next"})
        await wait_until(lambda: game.sent[-1] == {"status": "next"})

        manager.push_message({"action": "leave_game"})
        await asyncio.wait_for(run_task, timeout=1.0)
        self.assertTrue(game.left)

    async def test_client_error_message_raises_client_server_error(self) -> None:
        """Ошибка от сервера пробрасывается из клиентской логики."""

        game = FakeQuizGame()
        run_task = asyncio.create_task(quiz_run(game))

        await wait_until(lambda: len(Manager.queue_status) > 0)
        Manager.queue_status.clear()

        await game.incoming.put({"status": "error", "message": "boom"})

        with self.assertRaisesRegex(ClientServerError, "boom"):
            await asyncio.wait_for(run_task, timeout=1.0)


if __name__ == "__main__":
    unittest.main()
