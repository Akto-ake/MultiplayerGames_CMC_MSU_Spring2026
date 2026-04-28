"""Бэкенд клиента."""

import asyncio

import status_client_support
from frontend import Menager
from main_function_for_client import CLIENT_GAMES
from server import Client, ClientServerError


async def play_game(game: Client.Game):
    """Запускает игру.

    Args:
        game (Client.Game): игра клиента.
    """

    menager = Menager()

    try:
        await game.run()
    except status_client_support.Errors_game as error:
        menager.push_status(None, error=error)
    except ClientServerError as error:
        menager.push_status(
            None,
            error=status_client_support.Errors_game(str(error), 1),
        )


async def run():
    """Основной цикл бэкенда."""

    client = Client()
    menager = Menager()

    try:
        await client.connect()

        while True:
            await asyncio.sleep(0.01)

            message = menager.pop_messange()

            if message is None:
                continue

            if not isinstance(message, tuple):
                menager.push_status(
                    None,
                    error=status_client_support.Errors_game("", 1),
                )
                continue

            match message[0]:
                case 0:
                    break

                case 1:
                    game = await client.connect_game(message[1])
                    game.set_run(CLIENT_GAMES["X_O"])

                case code if 1 < code < len(status_client_support._STATUS_):
                    game_name = message[1][22:]
                    game = await client.init_game(game_name)
                    game.set_run(CLIENT_GAMES[game_name])

                case _:
                    menager.push_status(
                        None,
                        error=status_client_support.Errors_game("", 1),
                    )
                    continue

            await play_game(game)

    finally:
        await client.close()
