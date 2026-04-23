"""Server skeleton for multiplayer games."""

import asyncio
import shlex


AVAILABLE_GAMES = ["Xand0", "quiz"]


class Client:
    """Клиент сервера."""

    def __init__(self, nickname, score=0):
        """Инициализация клиента."""
        self.nickname = nickname
        self.score = score
        self.current_game = None
        self.queue = asyncio.Queue()

    async def push_message(self, message):
        """Положить сообщение в очередь клиента."""
        await self.queue.put(message)

    async def pop_message(self):
        """Взять сообщение из очереди клиента."""
        return await self.queue.get()

    def add_score(self, points):
        """Изменить количество очков клиента."""
        self.score += points


class Game:
    """Игровой сеанс."""

    def __init__(self, game_name):
        """Инициализация игры."""
        self.game_name = game_name
        self.players = {}
        self.messages = asyncio.Queue()

    def add_player(self, client):
        """Добавить игрока в игру."""
        if client.nickname in self.players:
            # клиент с таким ником уже есть
            return False
        self.players[client.nickname] = client
        return True

    def remove_player(self, nickname):
        """Удалить игрока из игры."""
        return self.players.pop(nickname, None)

    def get_player(self, nickname):
        """Получить игрока по нику."""
        return self.players.get(nickname)

    def get_list_nicks(self):
        """Возвращает список (list) ников

            Returns:
                list: список ников(str):
        """
        return list(self.players.keys())

    async def push_message(self, nickname, message):
        """Отправить сообщение message игроку nickname."""
        await self.messages.put((nickname, message))

    async def pop_message(self):
        """Получить сообщение."""
        return await self.messages.get()

    async def broadcast(self, message):
        """Разослать сообщение всем игрокам этой игры."""
        for client in self.players.values():
            await client.push_message(message)


class Server:
    """Сервер приложения."""

    def __init__(self):
        """Инициализация сервера."""
        self.available_games = AVAILABLE_GAMES[:]
        self.clients = {}
        self.games = {name: Game(name) for name in self.available_games}

    def add_client(self, nickname, score=0):
        """Зарегистрировать игрока."""
        if nickname in self.clients:
            raise ValueError("Nickname is already taken")

        client = Client(nickname, score)
        self.clients[nickname] = client
        return client

    def remove_client(self, nickname):
        """Удалить клиента с сервера."""
        client = self.clients.pop(nickname, None)

        if client.current_game:
            self.disconnect_from_game(nickname)

        return client

    def connect_to_game(self, nickname, game_name):
        """Подключить клиента к выбранной игре."""
        client = self.clients.get(nickname)

        game = self.games[game_name]
        game.add_player(client)
        client.current_game = game_name
        return game

    def disconnect_from_game(self, nickname):
        """Отключить клиента от текущей игры."""
        client = self.clients.get(nickname)

        game = self.games[client.current_game]
        removed = game.remove_player(nickname)
        client.current_game = None
        return removed

    async def echo_client(self, nickname, message):
        """Обработать сообщение от клиента.

        Поддерживаемые команды:
            1) connect <game_name>
            2) ...
        """
        client = self.clients.get(nickname)
        if client is None:
            return "Unknown client"

        args = shlex.split(message)
        if not args:
            return "Empty command"

        cmd = args[0]

        if cmd == "connect":
            if len(args) != 2:
                return "Invalid arguments"

            game_name = args[1]


            if game_name not in self.available_games:
                return f"Unknown game. Available games: {', '.join(self.available_games)}"

            self.connect_to_game(nickname, game_name)

            return f"{nickname} connected to {game_name}"

        return "Invalid command"
