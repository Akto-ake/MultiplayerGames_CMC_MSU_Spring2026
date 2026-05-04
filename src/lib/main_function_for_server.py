"""Основные функции для серверных лобби."""

import random


async def x_o_main_lobby(lobby):
    """Логика игры крестики-нолики."""

    stage = "waiting"
    first_player = None

    while True:
        nick, message = await lobby.pop_message()

        target = message.get("target")
        status = message.get("status")

        match stage:
            case "waiting":
                match target, status:
                    case "main_lobby", "joined":
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "joined",
                                "message": nick,
                            }
                        )

                    case "main_lobby", "leave":
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "leave",
                                "message": nick,
                            }
                        )

                    case "client", "start":
                        if len(lobby.get_list_nicks()) < lobby.max_players:
                            lobby.push_message(
                                {
                                    "target": "client",
                                    "status": "error",
                                    "message": "not enough players",
                                },
                                [nick],
                            )
                            continue

                        stage = "game"
                        first_player = random.choice(lobby.get_list_nicks())

                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "start",
                                "message": first_player,
                            }
                        )

                    case _:
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "error",
                                "message": "game is not started",
                            },
                            [nick],
                        )

            case "game":
                match target, status:
                    case "main_lobby", "leave":
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "leave",
                                "message": nick,
                            }
                        )
                        return

                    case "client", _:
                        lobby.push_message(message)


GAMES = {
    "X_O": {
        "main_func": x_o_main_lobby,
        "max_players": 2,
    },
}
