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
                        stage = "waiting"
                        first_player = None

                    case "client", "round_finished":
                        stage = "finished"

                    case "client", _:
                        lobby.push_message(message)

            case "finished":
                match target, status:
                    case "main_lobby", "leave":
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "leave",
                                "message": nick,
                            }
                        )
                        stage = "waiting"
                        first_player = None

                    case "client", "start":
                        players = lobby.get_list_nicks()
                        if len(players) < lobby.max_players:
                            lobby.push_message(
                                {
                                    "target": "client",
                                    "status": "error",
                                    "message": "not enough players",
                                },
                                [nick],
                            )
                            continue

                        first_player = next(
                            player
                            for player in players
                            if player != first_player
                        )
                        stage = "game"
                        lobby.push_message(
                            {
                                "target": "client",
                                "status": "start",
                                "message": first_player,
                            }
                        )


async def pong_main_lobby(lobby):
    """Логика серверного лобби Pong."""

    stage = "waiting"
    round_id = 0
    pending_start = False

    def start_round():
        nonlocal pending_start, round_id, stage

        pending_start = False
        stage = "game"
        round_id += 1
        players = lobby.get_list_nicks()

        lobby.push_message(
            {
                "target": "client",
                "status": "start",
                "message": {
                    "players": players,
                    "host": players[0],
                    "round": round_id,
                },
            }
        )

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

                        start_round()

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

                    case "client", "round_finished":
                        if pending_start and len(lobby.get_list_nicks()) >= (
                            lobby.max_players
                        ):
                            start_round()
                        else:
                            stage = "finished"

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

                        start_round()
                        continue

                    case "client", _:
                        lobby.push_message(message)

            case "finished":
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

                        start_round()


async def snake_main_lobby(lobby):
    """Логика серверного лобби Snake."""

    stage = "waiting"
    round_id = 0

    def start_round():
        nonlocal round_id, stage

        stage = "game"
        round_id += 1
        players = lobby.get_list_nicks()

        lobby.push_message(
            {
                "target": "client",
                "status": "start",
                "message": {
                    "players": players,
                    "host": players[0],
                    "round": round_id,
                },
            }
        )

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
                        return

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

                        start_round()

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

                    case "client", "round_finished":
                        stage = "finished"

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

                        start_round()

                    case "client", _:
                        lobby.push_message(message)

            case "finished":
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

                        start_round()


GAMES = {
    "X_O": {
        "main_func": x_o_main_lobby,
        "max_players": 2,
    },
    "PONG": {
        "main_func": pong_main_lobby,
        "max_players": 2,
    },
    "SNAKE": {
        "main_func": snake_main_lobby,
        "max_players": 2,
    },
}
