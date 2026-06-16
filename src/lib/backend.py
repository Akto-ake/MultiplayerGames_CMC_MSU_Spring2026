"""Бэкенд клиента."""

import asyncio

try:
    from . import status_client_support
    from .frontend import Manager
    from .localization import tr, tr_error
    from .main_function_for_client import CLIENT_GAMES
    from .server import Client, ClientServerError
except ImportError:
    import status_client_support
    from frontend import Manager
    from localization import tr, tr_error
    from main_function_for_client import CLIENT_GAMES
    from server import Client, ClientServerError


async def play_game(game: Client.Game):
    """Запускает игру.

    Args:
        game (Client.Game): игра клиента.
    """

    manager = Manager()

    try:
        await game.run()
    except status_client_support.Error_game as error:
        manager.push_status(None, error=error)
    except ClientServerError as error:
        manager.push_status(
            None,
            error=status_client_support.Error_game(tr_error(error), 1),
        )


def push_startup_connected(manager: Manager):
    """Сообщает фронтенду об успешном стартовом подключении."""

    manager.push_status(
        {
            "view": "startup_connected",
        }
    )


def push_server_unavailable(manager: Manager):
    """Сообщает фронтенду об отсутствии сервера на старте."""

    manager.push_status(
        {
            "view": "server_unavailable",
            "message": tr("server_unavailable.message"),
        }
    )


async def check_server_protocol(client: Client):
    """Проверяет, что на порту отвечает именно игровой сервер."""

    try:
        await asyncio.wait_for(
            client.request(
                {
                    "target": "server",
                    "message": "__startup_probe__",
                }
            ),
            timeout=0.5,
        )
    except ClientServerError as error:
        return str(error) == "unknown message"
    except Exception:
        return False

    return False


async def try_connect_client(client: Client, manager: Manager):
    """Пытается подключить клиента к серверу на старте."""

    try:
        await client.connect()
        if not await check_server_protocol(client):
            raise ClientServerError("server unavailable")
        push_startup_connected(manager)
        return True
    except (ClientServerError, OSError):
        await client.close()
        push_server_unavailable(manager)
        return False


async def _run_client_loop(client: Client):
    """Основной цикл бэкенда с уже подключённым клиентом."""

    manager = Manager()
    is_connected = await try_connect_client(client, manager)

    while True:
        await asyncio.sleep(0.01)

        message = manager.pop_message()

        if message is None:
            continue

        if not isinstance(message, tuple):
            manager.push_status(
                None,
                error=status_client_support.Error_game("", 1),
            )
            continue

        match message[0]:
            case 0:
                break

            case "retry_connect":
                if not is_connected:
                    is_connected = await try_connect_client(client, manager)
                continue

            case "login":
                if not is_connected:
                    continue
                await client.login(message[1])
                continue

            case "create_game":
                if not is_connected:
                    continue
                try:
                    lobby_id = message[2] if len(message) > 2 else None
                    game = await client.init_game(message[1], lobby_id)
                except ClientServerError as error:
                    manager.push_status(
                        {
                            "view": "create_error",
                            "message": tr_error(error),
                        }
                    )
                    continue
                if message[1] == "X_O":
                    manager.push_status({"view": "open_x_o"})
                if message[1] == "PONG":
                    manager.push_status({"view": "open_pong"})
                if message[1] == "SNAKE":
                    manager.push_status({"view": "open_snake"})
                game.set_run(CLIENT_GAMES[message[1]])

            case 1:
                if not is_connected:
                    continue
                try:
                    game = await client.connect_game(message[1])
                except ClientServerError as error:
                    manager.push_status(
                        {
                            "view": "join_error",
                            "message": tr_error(error),
                        }
                    )
                    continue
                if game.game_name == "PONG":
                    manager.push_status({"view": "open_pong"})
                elif game.game_name == "SNAKE":
                    manager.push_status({"view": "open_snake"})
                else:
                    manager.push_status({"view": "open_x_o"})
                game.set_run(CLIENT_GAMES[game.game_name or "X_O"])

            case code if 1 < code < len(status_client_support._STATUS_):
                if not is_connected:
                    continue
                game_name = message[1][22:]
                game = await client.init_game(game_name)
                game.set_run(CLIENT_GAMES[game_name])

            case _:
                manager.push_status(
                    None,
                    error=status_client_support.Error_game("", 1),
                )
                continue

        await play_game(game)


async def run():
    """Основной цикл бэкенда."""

    client = Client()

    try:
        await _run_client_loop(client)
    finally:
        await client.close()
