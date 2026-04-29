"""Основные функции клиентских игр."""

import asyncio

from frontend import Menager
from server import ClientServerError


X_O_EMPTY = ""


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


def x_o_push(menager, game, board, symbol, turn, status):
    """Отправляет состояние крестиков-ноликов во фронтенд."""

    menager.push_status(
        {
            "game": "X_O",
            "board": board,
            "nicks": game.nicks,
            "symbol": symbol,
            "turn": turn,
            "status": status,
        }
    )


async def x_o_run(game):
    """Локальная логика крестиков-ноликов."""

    menager = Menager()

    board = [[X_O_EMPTY] * 3 for _ in range(3)]
    symbols = {}
    turn = None
    symbol = None

    await game.get_nicks()
    x_o_push(menager, game, board, symbol, turn, "waiting")

    task = asyncio.create_task(game.pop_message())

    try:
        while True:
            await asyncio.sleep(0.01)

            user_message = menager.pop_message()

            if user_message == "start":
                await game.push_message({"status": "start"})

            move = x_o_parse_move(user_message)

            if move is not None and symbol is not None:
                row, col = move

                if turn != game.client.nick:
                    x_o_push(menager, game, board, symbol, turn, "not your turn")
                    continue

                if row not in range(3) or col not in range(3):
                    x_o_push(menager, game, board, symbol, turn, "bad move")
                    continue

                if board[row][col] != X_O_EMPTY:
                    x_o_push(menager, game, board, symbol, turn, "busy")
                    continue

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
                    x_o_push(menager, game, board, symbol, turn, "joined")

                case "leave":
                    x_o_push(menager, game, board, symbol, turn, "leave")
                    return

                case "start":
                    first = message["message"]
                    second = [nick for nick in game.nicks if nick != first][0]

                    symbols = {
                        first: "X",
                        second: "O",
                    }

                    turn = first
                    symbol = symbols[game.client.nick]

                    x_o_push(menager, game, board, symbol, turn, "start")

                case "move":
                    data = message["message"]
                    nick = data["nick"]
                    row = data["row"]
                    col = data["col"]

                    if nick != turn:
                        raise ClientServerError("wrong turn")

                    if data["symbol"] != symbols[nick]:
                        raise ClientServerError("wrong symbol")

                    board[row][col] = data["symbol"]

                    if x_o_win(board):
                        x_o_push(menager, game, board, symbol, turn, "win")
                        return

                    if all(X_O_EMPTY not in row for row in board):
                        x_o_push(menager, game, board, symbol, turn, "draw")
                        return

                    turn = [nick for nick in game.nicks if nick != turn][0]
                    x_o_push(menager, game, board, symbol, turn, "move")

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
}
