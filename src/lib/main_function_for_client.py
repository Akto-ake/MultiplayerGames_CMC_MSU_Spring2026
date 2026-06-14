"""Основные функции клиентских игр."""

import asyncio

try:
    from .frontend import Manager
    from .server import ClientServerError
except ImportError:
    from frontend import Manager
    from server import ClientServerError


X_O_EMPTY = ""
PONG_TICK = 0.02
PONG_STATE_INTERVAL = 0.04
PONG_PADDLE_SIZE = 0.26
PONG_PADDLE_OFFSET = 0.08
PONG_BALL_RADIUS = 0.025


def x_o_win(board):
    """Возвращает победителя в крестиках-ноликах или None."""

    lines = (
        board
        + [[board[0][i], board[1][i], board[2][i]] for i in range(3)]
        + [[board[0][0], board[1][1], board[2][2]]]
        + [[board[0][2], board[1][1], board[2][0]]]
    )

    for line in lines:
        if line[0] != X_O_EMPTY and line[0] == line[1] == line[2]:
            return line[0]

    return None


def x_o_parse_move(message):
    """Возвращает ход в крестиках-ноликах в виде пары координат."""

    if isinstance(message, dict):
        return message.get("row"), message.get("col")

    if isinstance(message, tuple) or isinstance(message, list):
        if len(message) == 2:
            return message

        if len(message) > 1:
            return x_o_parse_move(message[1])

    return None


def x_o_push(
    manager,
    game,
    board,
    symbol,
    turn,
    status,
    move_pending=False,
):
    """Отправляет состояние крестиков-ноликов во фронтенд."""

    manager.push_status(
        {
            "game": "X_O",
            "board": [row.copy() for row in board],
            "nicks": list(game.nicks),
            "lobby_id": game.get_id(),
            "symbol": symbol,
            "turn": turn,
            "status": status,
            "move_pending": move_pending,
        }
    )


async def x_o_run(game):
    """Локальная логика крестиков-ноликов."""

    manager = Manager()

    board = [[X_O_EMPTY] * 3 for _ in range(3)]
    symbols = {}
    turn = None
    symbol = None
    move_pending = False
    finished = False

    await game.get_nicks()
    x_o_push(manager, game, board, symbol, turn, "waiting")

    task = asyncio.create_task(game.pop_message())

    try:
        while True:
            await asyncio.sleep(0.01)

            user_message = manager.pop_message()

            if (
                isinstance(user_message, dict)
                and user_message.get("action") == "leave_game"
            ):
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                await game.leave()
                return

            if (
                isinstance(user_message, tuple)
                and len(user_message) > 0
                and user_message[0] == 0
            ):
                manager.push_message(user_message)
                return

            if user_message == "start" and (turn is None or finished):
                await game.push_message({"status": "start"})

            move = x_o_parse_move(user_message)

            if (
                move is not None
                and symbol is not None
                and not move_pending
                and not finished
            ):
                row, col = move

                if turn != game.client.nick:
                    x_o_push(manager, game, board, symbol, turn, "not your turn")
                    continue

                if row not in range(3) or col not in range(3):
                    x_o_push(manager, game, board, symbol, turn, "bad move")
                    continue

                if board[row][col] != X_O_EMPTY:
                    continue

                board[row][col] = symbol
                move_pending = True
                x_o_push(
                    manager,
                    game,
                    board,
                    symbol,
                    turn,
                    "move",
                    move_pending=True,
                )
                await game.push_message(
                    {
                        "status": "move",
                        "message": {
                            "nick": game.client.nick,
                            "row": row,
                            "col": col,
                            "symbol": symbol,
                        },
                    }
                )

            if not task.done():
                continue

            message = task.result()
            task = asyncio.create_task(game.pop_message())

            match message.get("status"):
                case "joined":
                    status = "joined" if len(game.nicks) >= 2 else "waiting"
                    x_o_push(manager, game, board, symbol, turn, status)

                case "leave":
                    board = [[X_O_EMPTY] * 3 for _ in range(3)]
                    symbols = {}
                    turn = None
                    symbol = None
                    move_pending = False
                    finished = False
                    x_o_push(manager, game, board, symbol, turn, "leave")

                case "start":
                    first = message["message"]
                    second = [nick for nick in game.nicks if nick != first][0]

                    board = [[X_O_EMPTY] * 3 for _ in range(3)]
                    symbols = {
                        first: "X",
                        second: "O",
                    }

                    turn = first
                    symbol = symbols[game.client.nick]
                    move_pending = False
                    finished = False

                    x_o_push(manager, game, board, symbol, turn, "start")

                case "move":
                    data = message["message"]
                    nick = data["nick"]
                    row = data["row"]
                    col = data["col"]
                    move_pending = False

                    if nick != turn:
                        raise ClientServerError("wrong turn")

                    if data["symbol"] != symbols[nick]:
                        raise ClientServerError("wrong symbol")

                    if board[row][col] not in (X_O_EMPTY, data["symbol"]):
                        raise ClientServerError("cell is busy")

                    board[row][col] = data["symbol"]

                    if x_o_win(board):
                        finished = True
                        x_o_push(manager, game, board, symbol, turn, "win")
                        await game.push_message({"status": "round_finished"})
                        continue

                    if all(X_O_EMPTY not in row for row in board):
                        finished = True
                        x_o_push(manager, game, board, symbol, turn, "draw")
                        await game.push_message({"status": "round_finished"})
                        continue

                    turn = [nick for nick in game.nicks if nick != turn][0]
                    x_o_push(manager, game, board, symbol, turn, "move")

                case "error":
                    raise ClientServerError(message.get("message"))

    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


def pong_initial_state(players):
    """Возвращает начальное состояние Pong."""

    return {
        "players": players,
        "paddles": {
            players[0]: 0.5,
            players[1]: 0.5,
        },
        "ball": {
            "x": 0.5,
            "y": 0.5,
            "vx": 0.46,
            "vy": 0.34,
        },
        "score": {
            players[0]: 0,
            players[1]: 0,
        },
    }


def pong_push(manager, game, state, side, status):
    """Отправляет состояние Pong во фронтенд."""

    manager.push_status(
        {
            "game": "PONG",
            "state": state,
            "nicks": game.nicks,
            "lobby_id": game.get_id(),
            "side": side,
            "status": status,
        }
    )


def pong_process_ball(state, delta_time):
    """Обновляет положение мяча и счёт Pong."""

    players = state["players"]
    ball = state["ball"]
    ball["x"] += ball["vx"] * delta_time
    ball["y"] += ball["vy"] * delta_time

    if ball["y"] <= PONG_BALL_RADIUS or ball["y"] >= 1 - PONG_BALL_RADIUS:
        ball["vy"] *= -1
        ball["y"] = min(max(ball["y"], PONG_BALL_RADIUS), 1 - PONG_BALL_RADIUS)

    left_y = state["paddles"][players[0]]
    right_y = state["paddles"][players[1]]

    if (
        ball["x"] <= PONG_PADDLE_OFFSET
        and abs(ball["y"] - left_y) <= PONG_PADDLE_SIZE / 2
    ):
        ball["vx"] = abs(ball["vx"])

    if (
        ball["x"] >= 1 - PONG_PADDLE_OFFSET
        and abs(ball["y"] - right_y) <= PONG_PADDLE_SIZE / 2
    ):
        ball["vx"] = -abs(ball["vx"])

    if ball["x"] < 0:
        state["score"][players[1]] += 1
        pong_reset_ball(ball, direction=1)

    if ball["x"] > 1:
        state["score"][players[0]] += 1
        pong_reset_ball(ball, direction=-1)


def pong_reset_ball(ball, direction):
    """Возвращает мяч в центр поля."""

    ball["x"] = 0.5
    ball["y"] = 0.5
    ball["vx"] = 0.46 * direction
    ball["vy"] *= -1


async def pong_run(game):
    """Локальная логика Pong."""

    manager = Manager()
    state = None
    side = None
    host = None
    last_state_send = 0.0

    await game.get_nicks()
    pong_push(manager, game, state, side, "waiting")

    task = asyncio.create_task(game.pop_message())

    try:
        while True:
            await asyncio.sleep(PONG_TICK)

            user_message = manager.pop_message()

            if (
                isinstance(user_message, tuple)
                and len(user_message) > 0
                and user_message[0] == 0
            ):
                manager.push_message(user_message)
                return

            if user_message == "start" and state is None:
                await game.push_message({"status": "start"})

            if (
                isinstance(user_message, dict)
                and user_message.get("game") == "PONG"
                and user_message.get("action") == "paddle"
            ):
                await game.push_message(
                    {
                        "status": "paddle",
                        "message": {
                            "nick": game.client.nick,
                            "position": user_message.get("position"),
                        },
                    }
                )

            if state is not None and game.client.nick == host:
                pong_process_ball(state, PONG_TICK)
                last_state_send += PONG_TICK

                if last_state_send >= PONG_STATE_INTERVAL:
                    await game.push_message(
                        {
                            "status": "state",
                            "message": state,
                        }
                    )
                    last_state_send = 0.0
                    pong_push(manager, game, state, side, "move")

            if not task.done():
                continue

            message = task.result()
            task = asyncio.create_task(game.pop_message())

            match message.get("status"):
                case "joined":
                    pong_push(manager, game, state, side, "joined")

                case "leave":
                    pong_push(manager, game, state, side, "leave")
                    return

                case "start":
                    data = message["message"]
                    players = data["players"]
                    host = data["host"]
                    side = "left" if game.client.nick == players[0] else "right"
                    state = pong_initial_state(players)
                    pong_push(manager, game, state, side, "start")

                case "paddle":
                    if state is None:
                        continue

                    data = message["message"]
                    nick = data.get("nick")
                    position = data.get("position")

                    if nick in state["paddles"] and isinstance(position, float):
                        state["paddles"][nick] = min(max(position, 0.13), 0.87)
                        pong_push(manager, game, state, side, "move")

                case "state":
                    state = message["message"]
                    pong_push(manager, game, state, side, "move")

                case "error":
                    raise ClientServerError(message.get("message"))

    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


CLIENT_GAMES = {
    "X_O": x_o_run,
    "PONG": pong_run,
}
