"""Серверная и локальная часть проекта."""

import asyncio
import json

from main_function_for_strver import GAMES


SERVER_HOST = "0.0.0.0"
CLIENT_HOST = "127.0.0.1"
SERVER_PORT = 1337
MIN_LOBBY_ID = 1000
MAX_LOBBY_ID = 9999


class ClientServerError(Exception):
    """Ошибка клиента, сервера или лобби."""


def create_message(target, status, message):
    """Создаёт стандартное сообщение.

    Args:
        target (str): цель сообщения.
        status (str): статус сообщения.
        message (object): сообщение.

    Returns:
        dict: сообщение.
    """

    return {
        "target": target,
        "status": status,
        "message": message,
    }


class Server():
    """Отвечает за серверную часть проекта."""

    class lobby():
        """Игровое лобби"""

        def __init__(self, lobby_id: int, game: str):
            """Создаёт игровое лобби.

            Args:
                lobby_id (int): id лобби.
                game (str): название игры.
            """

            self.lobby_id = lobby_id
            self.game = game
            self.main_func = GAMES[game]["main_func"]
            self.max_players = GAMES[game]["max_players"]
            self.nicks = {}
            self.messages = asyncio.Queue()

        async def pop_message(self):
            """Получает сообщение, предназначенное для конкретного лобби.

            Returns:
                tuple: кортеж, содержащий:
                    - nick (str): ник отправителя.
                    - message (object): объект сообщения.
            """

            return await self.messages.get()

        def push_message(self, message: object, groop: list = None):
            """Отправляет сообщение message всем или только groop

            Args:
                message (object): сообщение.
                groop (list, optional): список ников (str) кому необходимо \
                    отправить сообщение. По умолчанию None = отправить всем.
            """

            if groop is None:
                groop = list(self.nicks.keys())

            for nick in groop:
                if nick in self.nicks:
                    self.nicks[nick].put_nowait(message)

        def add_nick(self, nick: str, queue: asyncio.Queue):
            """Добавляет ник в лобби.

            Args:
                nick (str): ник игрока.
                queue (asyncio.Queue): очередь сообщений игрока.
            """

            self.nicks[nick] = queue
            self.messages.put_nowait(
                (nick, create_message("main_lobby", "joined", nick))
            )

        def remove_nick(self, nick: str):
            """Удаляет ник из лобби.

            Args:
                nick (str): ник игрока.
            """

            self.nicks.pop(nick, None)

        def get_list_nicks(self):
            """Возвращает список ников.

            Returns:
                list: список ников(str).
            """

            return sorted(list(self.nicks.keys()))

        async def main_lobby(self):
            """Логика лобби. На сервере должно выполняться"""

            await self.main_func(self)

    def __init__(self):
        """Создаёт сервер."""

        self.lobbies = {}
        self.lobby_tasks = {}
        self.free_lobby_ids = set(range(MIN_LOBBY_ID, MAX_LOBBY_ID + 1))
        self.games = GAMES.copy()

    async def client_connected(self, reader, writer):
        """Обрабатывает подключение клиента.

        Args:
            reader (asyncio.StreamReader): поток чтения от клиента.
            writer (asyncio.StreamWriter): поток записи клиенту.
        """

        client_id = "{}:{}".format(*writer.get_extra_info("peername"))

        print(client_id)

        nick = None
        lobby_id = None
        queue = asyncio.Queue()

        read_task = asyncio.create_task(reader.readline())
        write_task = asyncio.create_task(queue.get())

        try:
            while not reader.at_eof():
                done, _ = await asyncio.wait(
                    [read_task, write_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                result = await self._process_client_tasks(
                    done, reader, writer, queue, read_task, write_task,
                    nick, lobby_id,
                )

                read_task, write_task, nick, lobby_id, need_disconnect = result

                if need_disconnect:
                    return

        finally:
            read_task.cancel()
            write_task.cancel()

            await self.leave_lobby(queue, nick, lobby_id)

            print(client_id, "DONE")

            writer.close()
            await writer.wait_closed()

    async def _process_client_tasks(
        self,
        done,
        reader,
        writer,
        queue,
        read_task,
        write_task,
        nick,
        lobby_id,
    ):
        """Обрабатывает завершившиеся задачи клиента."""

        for task in done:
            if task is read_task:
                data = task.result()

                if not data:
                    return read_task, write_task, nick, lobby_id, True

                read_task = asyncio.create_task(reader.readline())

                message = await self.load_message(data, queue)

                if message is None:
                    continue

                result = await self.process_message(
                    message, queue, nick, lobby_id,
                )
                nick, lobby_id, need_disconnect = result

                if need_disconnect:
                    return read_task, write_task, nick, lobby_id, True

            elif task is write_task:
                message = task.result()
                text = json.dumps(message, ensure_ascii=False)

                writer.write(f"{text}\n".encode())
                await writer.drain()

                write_task = asyncio.create_task(queue.get())

        return read_task, write_task, nick, lobby_id, False

    async def load_message(self, data: bytes, queue: asyncio.Queue):
        """Загружает json-сообщение клиента.

        Args:
            data (bytes): сообщение клиента в байтах.
            queue (asyncio.Queue): очередь сообщений клиента.

        Returns:
            dict | None: сообщение клиента.
        """

        try:
            message = json.loads(data.decode())
        except json.JSONDecodeError:
            await queue.put(create_message("server", "error", "bad json"))
            return None

        if not isinstance(message, dict):
            await queue.put(
                create_message("server", "error", "json message must be dict")
            )
            return None

        return message

    async def _put_error(self, queue, request_id, message):
        """Отправляет ошибку клиенту."""

        answer = create_message("server", "error", message)

        if request_id is not None:
            answer["request_id"] = request_id

        await queue.put(answer)

    async def process_message(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Обрабатывает сообщение клиента.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.

        Returns:
            tuple: ник, id лобби, нужно ли отключить клиента.
        """

        target = message.get("target")

        match target:
            case "server":
                return await self.process_server_message(
                    message, queue, nick, lobby_id,
                )

            case "client":
                await self.send_to_lobby(message, queue, nick, lobby_id)
                return nick, lobby_id, False

            case _:
                await self._put_error(
                    queue, message.get("request_id"), "unknown target"
                )
                return nick, lobby_id, False

    async def process_server_message(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Обрабатывает сообщение серверу.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.

        Returns:
            tuple: ник, id лобби, нужно ли отключить клиента.
        """

        action = message.get("message")

        match action:
            case "login":
                nick = await self.login(message, queue, nick, lobby_id)

            case "create":
                new_lobby_id = await self.create_lobby(
                    message, queue, nick, lobby_id,
                )

                if new_lobby_id is not None:
                    lobby_id = new_lobby_id

            case "join":
                new_lobby_id = await self.join_lobby(
                    message, queue, nick, lobby_id,
                )

                if new_lobby_id is not None:
                    lobby_id = new_lobby_id

            case "who":
                await self.who(queue, nick, lobby_id, message.get("request_id"))

            case "disconnect":
                return nick, lobby_id, True

            case _:
                await self._put_error(
                    queue, message.get("request_id"), "unknown message"
                )

        return nick, lobby_id, False

    async def login(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Регистрирует или меняет ник клиента в меню.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): текущий ник клиента.
            lobby_id (int | None): id текущего лобби.

        Returns:
            str | None: новый ник или старый ник.
        """

        request_id = message.get("request_id")
        new_nick = message.get("nick")

        if not isinstance(new_nick, str) or not new_nick:
            await self._put_error(queue, request_id, "bad nick")
            return nick

        if lobby_id is not None and lobby_id in self.lobbies:
            await self._put_error(queue, request_id, "leave lobby first")
            return nick

        return new_nick

    async def create_lobby(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Создаёт новое лобби.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.

        Returns:
            int | None: id нового лобби.
        """

        request_id = message.get("request_id")

        if nick is None:
            await self._put_error(queue, request_id, "first login")
            return None

        game = message.get("game")

        if game not in self.games:
            await self._put_error(queue, request_id, "game not found")
            return None

        if not self.free_lobby_ids:
            await self._put_error(queue, request_id, "no free lobby ids")
            return None

        await self.leave_lobby(queue, nick, lobby_id)

        new_lobby_id = self.free_lobby_ids.pop()
        new_lobby = self.lobby(new_lobby_id, game)
        new_lobby.add_nick(nick, queue)

        self.lobbies[new_lobby_id] = new_lobby

        task = asyncio.create_task(new_lobby.main_lobby())
        task.add_done_callback(
            lambda done_task, current_id=new_lobby_id:
                self.lobby_done(current_id, done_task)
        )

        self.lobby_tasks[new_lobby_id] = task

        await queue.put(
            {
                "target": "server",
                "request_id": request_id,
                "lobby_id": new_lobby_id,
            }
        )

        return new_lobby_id

    async def join_lobby(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Подключает клиента к лобби.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.

        Returns:
            int | None: id лобби.
        """

        request_id = message.get("request_id")

        if nick is None:
            await self._put_error(queue, request_id, "first login")
            return None

        if lobby_id is not None and lobby_id in self.lobbies:
            await self._put_error(queue, request_id, "leave lobby first")
            return None

        new_lobby_id = message.get("lobby_id")

        if not isinstance(new_lobby_id, int):
            await self._put_error(queue, request_id, "bad lobby_id")
            return None

        if new_lobby_id not in self.lobbies:
            await self._put_error(queue, request_id, "lobby not found")
            return None

        current_lobby = self.lobbies[new_lobby_id]

        if nick in current_lobby.nicks:
            await self._put_error(queue, request_id, "nick is busy in lobby")
            return None

        if current_lobby.max_players is not None and \
                len(current_lobby.get_list_nicks()) >= current_lobby.max_players:
            await self._put_error(queue, request_id, "lobby is full")
            return None

        current_lobby.add_nick(nick, queue)

        await queue.put(
            {
                "target": "server",
                "request_id": request_id,
                "lobby_id": new_lobby_id,
            }
        )

        return new_lobby_id

    async def send_to_lobby(
        self,
        message: dict,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Передаёт сообщение в текущее лобби.

        Args:
            message (dict): сообщение клиента.
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.
        """

        request_id = message.get("request_id")

        if nick is None:
            await self._put_error(queue, request_id, "first login")
            return

        if lobby_id is None:
            await self._put_error(queue, request_id, "first create or join lobby")
            return

        current_lobby = self.lobbies.get(lobby_id)

        if current_lobby is None:
            await self._put_error(queue, request_id, "lobby not found")
            return

        payload = message.copy()

        await current_lobby.messages.put((nick, payload))

    async def who(
        self,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
        request_id: int | None,
    ):
        """Возвращает список ников текущего лобби.

        Args:
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.
            request_id (int | None): id запроса клиента.
        """

        if nick is None:
            await self._put_error(queue, request_id, "first login")
            return

        if lobby_id is None:
            await self._put_error(queue, request_id, "first create or join lobby")
            return

        current_lobby = self.lobbies.get(lobby_id)

        if current_lobby is None:
            await self._put_error(queue, request_id, "lobby not found")
            return

        if current_lobby.nicks.get(nick) is not queue:
            await self._put_error(queue, request_id, "not in this lobby")
            return

        await queue.put(
            {
                "target": "server",
                "request_id": request_id,
                "nicks": current_lobby.get_list_nicks(),
            }
        )

    async def leave_lobby(
        self,
        queue: asyncio.Queue,
        nick: str | None,
        lobby_id: int | None,
    ):
        """Удаляет клиента из текущего лобби.

        Args:
            queue (asyncio.Queue): очередь сообщений клиента.
            nick (str | None): ник клиента.
            lobby_id (int | None): id текущего лобби.
        """

        if nick is None or lobby_id is None:
            return

        current_lobby = self.lobbies.get(lobby_id)

        if current_lobby is None:
            return

        if current_lobby.nicks.get(nick) is not queue:
            return

        current_lobby.remove_nick(nick)

        if current_lobby.get_list_nicks():
            await current_lobby.messages.put(
                (nick, create_message("main_lobby", "leave", nick))
            )
            return

        self.stop_lobby(lobby_id)

    def lobby_done(self, lobby_id: int, task: asyncio.Task):
        """Обрабатывает завершение задачи лобби.

        Args:
            lobby_id (int): id лобби.
            task (asyncio.Task): задача лобби.
        """

        if task.cancelled():
            return

        error = task.exception()

        current_lobby = self.lobbies.pop(lobby_id, None)
        self.lobby_tasks.pop(lobby_id, None)
        self.free_lobby_ids.add(lobby_id)

        if current_lobby is None:
            return

        if error is None:
            return

        print(f"Lobby {lobby_id} crashed:", error)

        current_lobby.push_message(
            create_message("main_lobby", "error", "lobby crashed")
        )

    def stop_lobby(self, lobby_id: int):
        """Останавливает лобби.

        Args:
            lobby_id (int): id лобби.
        """

        task = self.lobby_tasks.pop(lobby_id, None)

        if task is not None:
            task.cancel()

        self.lobbies.pop(lobby_id, None)
        self.free_lobby_ids.add(lobby_id)

    async def run(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        """Запускает сервер.

        Args:
            host (str): адрес сервера.
            port (int): порт сервера.
        """

        server = await asyncio.start_server(self.client_connected, host, port)

        async with server:
            await server.serve_forever()


class Client():
    """Отвечает за локальную часть"""

    class Game():
        """Игра"""

        def __init__(self, client, lobby_id: int):
            """Создаёт игру.

            Args:
                client (Client): клиент.
                lobby_id (int): id лобби.
            """

            self.client = client
            self.lobby_id = lobby_id
            self.nicks = []
            self.run_func = None

        def set_run(self, run_func):
            """Задаёт функцию запуска игры.

            Args:
                run_func (function): функция запуска игры.
            """

            self.run_func = run_func

        async def run(self):
            """Запускает локальную часть игры."""

            if self.run_func is None:
                raise ClientServerError("game run function is not set")

            await self.run_func(self)

        async def pop_message(self):
            """Получает сообщение.

            Returns:
                object: объект сообщения.
            """

            message = await self.client.game_messages.get()
            self.process_message(message)

            return message

        def process_message(self, message: dict):
            """Обрабатывает служебную часть игрового сообщения.

            Args:
                message (dict): сообщение.
            """

            match message.get("status"):
                case "joined":
                    nick = message.get("message")

                    if nick not in self.nicks:
                        self.nicks.append(nick)
                        self.nicks.sort()

                case "leave":
                    nick = message.get("message")

                    if nick in self.nicks:
                        self.nicks.remove(nick)

                case _:
                    return

        async def push_message(self, message: dict):
            """Отправляет сообщение message.

            Args:
                message (dict): сообщение.
            """

            if not isinstance(message, dict):
                message = {"message": message}

            data = message.copy()
            data["target"] = "client"

            await self.client.send_json(data)

        async def get_nicks(self):
            """Возвращает список ников.

            Returns:
                list: список ников.
            """

            self.nicks = await self.client.get_nicks()

            return self.nicks

        def get_id(self):
            """Возвращает id.

            Returns:
                int: id.
            """

            return self.lobby_id

    def __init__(self, host: str = CLIENT_HOST, port: int = SERVER_PORT):
        """Создаёт клиента.

        Args:
            host (str): адрес сервера.
            port (int): порт сервера.
        """

        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.game_messages = asyncio.Queue()
        self.listen_task = None
        self.request_id = 0
        self.requests = {}
        self.nick = None

    async def connect(self):
        """Подключается к серверу."""

        self.reader, self.writer = await asyncio.open_connection(
            self.host,
            self.port,
        )

        self.listen_task = asyncio.create_task(self.listen_server())

    async def listen_server(self):
        """Слушает сообщения от сервера."""

        if self.reader is None:
            raise ClientServerError("client is not connected")

        while True:
            data = await self.reader.readline()

            if not data:
                break

            message = json.loads(data.decode())
            target = message.get("target")

            if target == "client":
                payload = message.copy()
                payload.pop("target", None)
                await self.game_messages.put(payload)
                continue

            self.process_server_message(message)

    def process_server_message(self, message: dict):
        """Обрабатывает служебное сообщение сервера."""

        request_id = message.get("request_id")

        if request_id in self.requests:
            future = self.requests.pop(request_id)

            if message.get("status") == "error":
                future.set_exception(ClientServerError(message.get("message")))
            else:
                future.set_result(message)

            return

        if message.get("status") == "error":
            raise ClientServerError(message.get("message"))

    async def request(self, message: dict):
        """Отправляет служебный запрос серверу и ждёт ответ."""

        self.request_id += 1
        request_id = self.request_id

        message = message.copy()
        message["request_id"] = request_id

        future = asyncio.get_running_loop().create_future()
        self.requests[request_id] = future

        try:
            await self.send_json(message)
            return await future
        except Exception:
            self.requests.pop(request_id, None)
            raise

    async def send_json(self, message: dict):
        """Отправляет json-сообщение серверу.

        Args:
            message (dict): сообщение.
        """

        if self.writer is None:
            raise ClientServerError("client is not connected")

        text = json.dumps(message, ensure_ascii=False)

        self.writer.write(f"{text}\n".encode())
        await self.writer.drain()

    async def login(self, nick: str):
        """Регистрирует ник.

        Args:
            nick (str): ник.
        """

        await self.send_json(
            {
                "target": "server",
                "message": "login",
                "nick": nick,
            }
        )

        self.nick = nick

    async def init_game(self, game: str):
        """Создание игры.

        Args:
            game (str): название игры.

        Returns:
            Game: игра.
        """

        answer = await self.request(
            {
                "target": "server",
                "message": "create",
                "game": game,
            }
        )

        return self.Game(self, answer["lobby_id"])

    async def connect_game(self, lobby_id: int):
        """Подключение к игре.

        Args:
            lobby_id (int): id игры.

        Returns:
            Game: игра.
        """

        answer = await self.request(
            {
                "target": "server",
                "message": "join",
                "lobby_id": lobby_id,
            }
        )

        return self.Game(self, answer["lobby_id"])

    async def get_nicks(self):
        """Возвращает список ников.

        Returns:
            list: список ников.
        """

        answer = await self.request(
            {
                "target": "server",
                "message": "who",
            }
        )

        return answer["nicks"]

    async def disconnect(self):
        """Отключается от сервера."""

        await self.send_json(
            {
                "target": "server",
                "message": "disconnect",
            }
        )

        await self.close()

    async def close(self):
        """Закрывает соединение."""

        if self.listen_task is not None:
            self.listen_task.cancel()

            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass

        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
