"""Интеграционные тесты сервера и игровых лобби."""

from __future__ import annotations

import asyncio
import io
import socket
import sys
import unittest
from contextlib import redirect_stdout, suppress
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.server import Client, ClientServerError, Server


def free_port() -> int:
    """Возвращает свободный локальный порт для тестового сервера."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class ServerLobbyTest(unittest.IsolatedAsyncioTestCase):
    """Тесты создания, подключения и освобождения лобби."""

    async def asyncSetUp(self) -> None:
        """Запускает тестовый сервер на отдельном порту."""

        self.port = free_port()
        self.server = Server()
        self.stdout = io.StringIO()
        self.stdout_redirect = redirect_stdout(self.stdout)
        self.stdout_redirect.__enter__()
        self.server_task = asyncio.create_task(
            self.server.run(host="127.0.0.1", port=self.port)
        )
        self.clients: list[Client] = []

        for _ in range(100):
            if self.server.server is not None:
                break

            await asyncio.sleep(0.01)

        self.assertIsNotNone(self.server.server)

    async def asyncTearDown(self) -> None:
        """Закрывает клиентов и останавливает тестовый сервер."""

        for client in self.clients:
            await client.close()

        await self.server.close()
        self.server_task.cancel()

        with suppress(asyncio.CancelledError):
            await self.server_task

        self.stdout_redirect.__exit__(None, None, None)

    async def connect_client(self, nick: str | None = None) -> Client:
        """Создаёт клиента и при необходимости регистрирует ник."""

        client = Client(port=self.port)
        await asyncio.wait_for(client.connect(), timeout=2)
        self.clients.append(client)

        if nick is not None:
            await asyncio.wait_for(client.login(nick), timeout=2)

        return client

    async def test_create_lobby_requires_login(self) -> None:
        """Создание лобби без ника возвращает серверную ошибку."""

        client = await self.connect_client()

        with self.assertRaisesRegex(ClientServerError, "first login"):
            await asyncio.wait_for(client.init_game("PONG", 4101), timeout=2)

    async def test_create_and_join_lobby_updates_nicks(self) -> None:
        """Создание и подключение к лобби возвращает общий список игроков."""

        first = await self.connect_client("alice")
        second = await self.connect_client("bob")

        first_game = await asyncio.wait_for(first.init_game("PONG", 4102), 2)
        second_game = await asyncio.wait_for(second.connect_game(4102), 2)

        self.assertEqual(first_game.get_id(), 4102)
        self.assertEqual(second_game.get_id(), 4102)
        self.assertEqual(first_game.game_name, "PONG")
        self.assertEqual(second_game.game_name, "PONG")
        self.assertEqual(
            await asyncio.wait_for(first_game.get_nicks(), 2),
            ["alice", "bob"],
        )
        self.assertEqual(
            await asyncio.wait_for(second_game.get_nicks(), 2),
            ["alice", "bob"],
        )

    async def test_busy_lobby_id_is_rejected(self) -> None:
        """Повторное создание лобби с тем же ID запрещено."""

        first = await self.connect_client("alice")
        second = await self.connect_client("bob")

        await asyncio.wait_for(first.init_game("PONG", 4103), 2)

        with self.assertRaisesRegex(ClientServerError, "lobby id is busy"):
            await asyncio.wait_for(second.init_game("SNAKE", 4103), timeout=2)

    async def test_full_lobby_rejects_third_player(self) -> None:
        """Заполненное лобби не принимает третьего игрока."""

        first = await self.connect_client("alice")
        second = await self.connect_client("bob")
        third = await self.connect_client("carol")

        await asyncio.wait_for(first.init_game("SNAKE", 4104), 2)
        await asyncio.wait_for(second.connect_game(4104), 2)

        with self.assertRaisesRegex(ClientServerError, "lobby is full"):
            await asyncio.wait_for(third.connect_game(4104), timeout=2)

    async def test_leave_lobby_frees_lobby_id(self) -> None:
        """После выхода последнего игрока ID лобби снова доступен."""

        first = await self.connect_client("alice")
        second = await self.connect_client("bob")

        await asyncio.wait_for(first.init_game("PONG", 4105), 2)
        await asyncio.wait_for(first.leave_game(), 2)
        second_game = await asyncio.wait_for(second.init_game("SNAKE", 4105), 2)

        self.assertEqual(second_game.get_id(), 4105)
        self.assertEqual(second_game.game_name, "SNAKE")


if __name__ == "__main__":
    unittest.main()
