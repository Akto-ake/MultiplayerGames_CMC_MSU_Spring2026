class Server():
    """Отвечает за серверную часть проекта."""

    class lobby():
        """Игровое лобби"""

        async def pop_message(self):
            """Получает сообщение, предназначенное для конкретного лобби.
            Returns:
                tuple: кортеж, содержащий:
                    - nick (str): ник отправителя.
                    - message (object): объект сообщения.
            """
            pass

        def push_message(self, message: object, groop: list = None):
            """Отправляет сообщение message всем или только groop

            Args:
                message (object): сообщение
                groop (List, optional): список ников (str) кому необходимо \
                    отправить сообщение. По умолчанию None = отправить всем.
            """
            pass

        def get_list_nicks(self):
            """Возвращает список (list) ников

            Returns:
                list: список ников(str):
            """
            pass

        async def main_lobby(self):
            """Логика лобби. На сервере должно выполняться"""
            pass


class Client():
    """Отвечает за локальную часть"""

    class Game():
        """Игра"""

        async def pop_message(self):
            """Получает сообщение.
            Returns:
                object: объект сообщения.
            """
            pass

        def push_message(self, message: object, groop: list = None):
            """Отправляет сообщение message всем или только groop

            Args:
                message (object): сообщение
                groop (List, optional): список ников (str) кому необходимо \
                    отправить сообщение. По умолчанию None = отправить всем.
            """
            pass

        def get_id(self):
            """Возвращает id

            Returns:
                int: id
            """

    def init_game(self, game: str):
        """Создание игры

        Args:
            game (str): название игры
        Returns:
            Game: игра
        """

        pass

    def connect_game(self, lobby_id: int):
        """Подключение к игре

        Args:
            lobby_id (int): id игры
        Returns:
            Game: игра
        """
        pass
