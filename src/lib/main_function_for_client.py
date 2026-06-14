"""Основные функции клиентских игр."""

import asyncio
import random

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
PONG_BALL_SPEED_X = 0.68
PONG_BALL_SPEED_Y = 0.46
PONG_BALL_ACCELERATION = 1.07
PONG_BALL_MAX_SPEED_X = 1.15
PONG_BALL_MAX_SPEED_Y = 0.82
PONG_WIN_SCORE = 5
SNAKE_COLS = 16
SNAKE_ROWS = 14
SNAKE_TICK = 0.22
SNAKE_WIN_SCORE = 5
SNAKE_DIRECTIONS = {
    "up": (0, 1),
    "down": (0, -1),
    "left": (-1, 0),
    "right": (1, 0),
}
SNAKE_OPPOSITE_DIRECTIONS = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


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


def pong_initial_state(players, round_id):
    """Возвращает начальное состояние Pong."""

    return {
        "round": round_id,
        "players": players,
        "paddles": {
            players[0]: 0.5,
            players[1]: 0.5,
        },
        "ball": {
            "x": 0.5,
            "y": 0.5,
            "vx": PONG_BALL_SPEED_X,
            "vy": PONG_BALL_SPEED_Y,
        },
        "score": {
            players[0]: 0,
            players[1]: 0,
        },
        "winner": None,
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

    if state.get("winner") is not None:
        return

    players = state["players"]
    ball = state["ball"]
    previous_x = ball["x"]
    ball["x"] += ball["vx"] * delta_time
    ball["y"] += ball["vy"] * delta_time

    if ball["y"] <= PONG_BALL_RADIUS or ball["y"] >= 1 - PONG_BALL_RADIUS:
        ball["vy"] *= -1
        ball["y"] = min(max(ball["y"], PONG_BALL_RADIUS), 1 - PONG_BALL_RADIUS)

    left_y = state["paddles"][players[0]]
    right_y = state["paddles"][players[1]]
    hit_tolerance = PONG_PADDLE_SIZE / 2 + PONG_BALL_RADIUS * 1.5
    left_paddle_x = PONG_PADDLE_OFFSET
    right_paddle_x = 1 - PONG_PADDLE_OFFSET

    if (
        ball["vx"] < 0
        and previous_x >= left_paddle_x >= ball["x"]
        and abs(ball["y"] - left_y) <= hit_tolerance
    ):
        ball["x"] = left_paddle_x
        ball["vx"] = abs(ball["vx"])
        pong_accelerate_ball(ball)

    if (
        ball["vx"] > 0
        and previous_x <= right_paddle_x <= ball["x"]
        and abs(ball["y"] - right_y) <= hit_tolerance
    ):
        ball["x"] = right_paddle_x
        ball["vx"] = -abs(ball["vx"])
        pong_accelerate_ball(ball)

    if ball["x"] < 0:
        state["score"][players[1]] += 1
        if state["score"][players[1]] >= PONG_WIN_SCORE:
            state["winner"] = players[1]
            pong_reset_paddles(state)
        pong_reset_ball(ball, direction=1)

    if ball["x"] > 1:
        state["score"][players[0]] += 1
        if state["score"][players[0]] >= PONG_WIN_SCORE:
            state["winner"] = players[0]
            pong_reset_paddles(state)
        pong_reset_ball(ball, direction=-1)


def pong_accelerate_ball(ball):
    """Постепенно ускоряет мяч после удара ракеткой."""

    ball["vx"] = pong_speed_with_limit(ball["vx"], PONG_BALL_MAX_SPEED_X)
    ball["vy"] = pong_speed_with_limit(ball["vy"], PONG_BALL_MAX_SPEED_Y)


def pong_speed_with_limit(value, limit):
    """Возвращает ускоренную скорость с сохранением направления."""

    direction = 1 if value >= 0 else -1
    return direction * min(abs(value) * PONG_BALL_ACCELERATION, limit)


def pong_reset_paddles(state):
    """Возвращает ракетки в центр поля."""

    for player in state["players"]:
        state["paddles"][player] = 0.5


def pong_reset_ball(ball, direction):
    """Возвращает мяч в центр поля."""

    ball["x"] = 0.5
    ball["y"] = 0.5
    vertical_direction = -1 if ball.get("vy", PONG_BALL_SPEED_Y) > 0 else 1
    ball["vx"] = PONG_BALL_SPEED_X * direction
    ball["vy"] = PONG_BALL_SPEED_Y * vertical_direction


async def pong_run(game):
    """Локальная логика Pong."""

    manager = Manager()
    state = None
    side = None
    host = None
    round_id = 0
    last_state_send = 0.0
    finish_reported = False
    restart_pending = False

    await game.get_nicks()
    pong_push(manager, game, state, side, "waiting")

    task = asyncio.create_task(game.pop_message())

    try:
        while True:
            await asyncio.sleep(PONG_TICK)

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

            if user_message == "start":
                restart_pending = True
                await game.push_message(
                    {
                        "status": "start",
                        "message": {
                            "round": round_id,
                            "finished": (
                                state is not None
                                and state.get("winner") is not None
                            ),
                        },
                    }
                )

            if (
                isinstance(user_message, dict)
                and user_message.get("game") == "PONG"
                and user_message.get("action") == "paddle"
            ):
                await game.push_message(
                    {
                        "status": "paddle",
                        "message": {
                            "round": user_message.get("round", round_id),
                            "side": user_message.get("side"),
                            "position": user_message.get("position"),
                        },
                    }
                )

            if (
                state is not None
                and game.client.nick == host
                and state.get("winner") is None
            ):
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

            if (
                state is not None
                and state.get("winner") is not None
                and not finish_reported
            ):
                if game.client.nick == host:
                    await game.push_message(
                        {
                            "status": "state",
                            "message": state,
                        }
                    )
                    await game.push_message({"status": "round_finished"})

                pong_push(manager, game, state, side, "finished")
                finish_reported = True

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
                    new_round_id = data.get("round", round_id + 1)
                    if new_round_id < round_id:
                        continue

                    round_id = new_round_id
                    players = data["players"]
                    host = data["host"]
                    side = "left" if game.client.nick == players[0] else "right"
                    state = pong_initial_state(players, round_id)
                    last_state_send = 0.0
                    finish_reported = False
                    restart_pending = False
                    pong_push(manager, game, state, side, "start")

                case "paddle":
                    if state is None:
                        continue

                    data = message["message"]
                    message_round = data.get("round")
                    if message_round is not None and message_round != round_id:
                        continue

                    side_name = data.get("side")
                    position = data.get("position")

                    if side_name == "left":
                        nick = state["players"][0]
                    elif side_name == "right":
                        nick = state["players"][1]
                    else:
                        nick = data.get("nick")

                    if nick in state["paddles"] and isinstance(position, float):
                        state["paddles"][nick] = min(max(position, 0.13), 0.87)
                        pong_push(manager, game, state, side, "move")

                case "state":
                    message_round = message["message"].get("round")
                    if message_round is not None and message_round < round_id:
                        continue

                    if restart_pending and message["message"].get("winner"):
                        continue

                    state = message["message"]
                    round_id = state.get("round", round_id)
                    status = "finished" if state.get("winner") else "move"
                    pong_push(manager, game, state, side, status)

                case "error":
                    raise ClientServerError(message.get("message"))

    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


def snake_side_nick(state, side_name):
    """Возвращает ник игрока Snake по стороне поля."""

    players = state["players"]
    if side_name == "left" and len(players) > 0:
        return players[0]
    if side_name == "right" and len(players) > 1:
        return players[1]
    return None


def snake_initial_body(side_name):
    """Возвращает начальное тело змейки."""

    if side_name == "left":
        return [[7, 7], [6, 7], [5, 7], [4, 7]]
    return [[8, 6], [9, 6], [10, 6], [11, 6]]


def snake_initial_direction(side_name):
    """Возвращает начальное направление змейки."""

    return "right" if side_name == "left" else "left"


def snake_taken_cells(state, excluded_nick=None):
    """Возвращает клетки, занятые змейками."""

    taken = set()
    for nick, snake in state["snakes"].items():
        if nick == excluded_nick:
            continue

        for cell in snake["body"]:
            taken.add(tuple(cell))

    return taken


def snake_spawn_food(state, nick):
    """Создаёт еду в свободной клетке поля."""

    taken = snake_taken_cells(state)
    free_cells = [
        [col, row]
        for col in range(SNAKE_COLS)
        for row in range(SNAKE_ROWS)
        if (col, row) not in taken
    ]

    if not free_cells:
        return [0, 0]

    return random.choice(free_cells)


def snake_reset_player(state, nick):
    """Возвращает змейку игрока в стартовое положение."""

    side_name = state["sides"][nick]
    direction = snake_initial_direction(side_name)
    state["snakes"][nick]["body"] = snake_initial_body(side_name)
    state["snakes"][nick]["direction"] = direction
    state["snakes"][nick]["pending_direction"] = direction
    state["snakes"][nick]["food"] = snake_spawn_food(state, nick)


def snake_initial_state(players, round_id):
    """Возвращает начальное состояние Snake."""

    state = {
        "round": round_id,
        "players": players,
        "sides": {
            players[0]: "left",
            players[1]: "right",
        },
        "snakes": {},
        "score": {
            players[0]: 0,
            players[1]: 0,
        },
        "paused": False,
        "winner": None,
    }

    for player in players:
        side_name = state["sides"][player]
        direction = snake_initial_direction(side_name)
        state["snakes"][player] = {
            "body": snake_initial_body(side_name),
            "direction": direction,
            "pending_direction": direction,
            "food": [0, 0],
        }

    for player in players:
        state["snakes"][player]["food"] = snake_spawn_food(state, player)

    return state


def snake_process_direction(state, side_name, direction):
    """Обновляет ожидаемое направление змейки."""

    if direction not in SNAKE_DIRECTIONS:
        return

    nick = snake_side_nick(state, side_name)
    if nick is None:
        return

    snake = state["snakes"][nick]
    if SNAKE_OPPOSITE_DIRECTIONS[snake["direction"]] == direction:
        return

    snake["pending_direction"] = direction


def snake_step(state):
    """Выполняет один игровой шаг Snake."""

    if state.get("winner") is not None:
        return

    if state.get("paused"):
        return

    for nick in state["players"]:
        snake = state["snakes"][nick]
        direction = snake["pending_direction"]
        vector = SNAKE_DIRECTIONS[direction]
        head_col, head_row = snake["body"][0]
        new_head = [head_col + vector[0], head_row + vector[1]]

        hit_wall = not (
            0 <= new_head[0] < SNAKE_COLS
            and 0 <= new_head[1] < SNAKE_ROWS
        )
        hit_self = new_head in snake["body"]

        if hit_wall or hit_self:
            snake_reset_player(state, nick)
            continue

        snake["direction"] = direction
        snake["body"].insert(0, new_head)

        if new_head == snake["food"]:
            state["score"][nick] += 1
            snake["food"] = snake_spawn_food(state, nick)
            if state["score"][nick] >= SNAKE_WIN_SCORE:
                state["winner"] = nick
        else:
            snake["body"].pop()


def snake_push(manager, game, state, side, status):
    """Отправляет состояние Snake во фронтенд."""

    manager.push_status(
        {
            "game": "SNAKE",
            "state": state,
            "nicks": list(game.nicks),
            "lobby_id": game.get_id(),
            "side": side,
            "status": status,
        }
    )


async def snake_run(game):
    """Локальная логика Snake."""

    manager = Manager()
    state = None
    side = None
    host = None
    round_id = 0
    tick_timer = 0.0
    finish_reported = False

    await game.get_nicks()
    snake_push(manager, game, state, side, "waiting")

    task = asyncio.create_task(game.pop_message())

    try:
        while True:
            await asyncio.sleep(0.02)

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

            if user_message == "start":
                await game.push_message({"status": "start"})

            if (
                isinstance(user_message, dict)
                and user_message.get("game") == "SNAKE"
                and user_message.get("action") == "pause"
            ):
                await game.push_message(
                    {
                        "status": "pause",
                        "message": {
                            "round": user_message.get("round", round_id),
                        },
                    }
                )

            if (
                isinstance(user_message, dict)
                and user_message.get("game") == "SNAKE"
                and user_message.get("action") == "direction"
            ):
                await game.push_message(
                    {
                        "status": "direction",
                        "message": {
                            "round": user_message.get("round", round_id),
                            "side": user_message.get("side"),
                            "direction": user_message.get("direction"),
                        },
                    }
                )

            if (
                state is not None
                and game.client.nick == host
                and state.get("winner") is None
                and not state.get("paused")
            ):
                tick_timer += 0.02
                if tick_timer >= SNAKE_TICK:
                    snake_step(state)
                    await game.push_message(
                        {
                            "status": "state",
                            "message": state,
                        }
                    )
                    status = "finished" if state.get("winner") else "move"
                    snake_push(manager, game, state, side, status)
                    tick_timer = 0.0

            if (
                state is not None
                and state.get("winner") is not None
                and not finish_reported
            ):
                if game.client.nick == host:
                    await game.push_message({"status": "round_finished"})

                snake_push(manager, game, state, side, "finished")
                finish_reported = True

            if not task.done():
                continue

            message = task.result()
            task = asyncio.create_task(game.pop_message())

            match message.get("status"):
                case "joined":
                    status = "joined" if len(game.nicks) >= 2 else "waiting"
                    snake_push(manager, game, state, side, status)

                case "leave":
                    snake_push(manager, game, state, side, "leave")
                    return

                case "start":
                    data = message["message"]
                    round_id = data.get("round", round_id + 1)
                    players = data["players"]
                    host = data["host"]
                    side = "left" if game.client.nick == players[0] else "right"
                    state = snake_initial_state(players, round_id)
                    tick_timer = 0.0
                    finish_reported = False
                    snake_push(manager, game, state, side, "start")

                case "direction":
                    if state is None:
                        continue

                    data = message["message"]
                    message_round = data.get("round")
                    if message_round is not None and message_round != round_id:
                        continue

                    snake_process_direction(
                        state,
                        data.get("side"),
                        data.get("direction"),
                    )

                case "pause":
                    if state is None:
                        continue

                    data = message.get("message") or {}
                    message_round = data.get("round")
                    if message_round is not None and message_round != round_id:
                        continue

                    state["paused"] = not state.get("paused", False)
                    tick_timer = 0.0
                    snake_push(manager, game, state, side, "move")

                    if game.client.nick == host:
                        await game.push_message(
                            {
                                "status": "state",
                                "message": state,
                            }
                        )

                case "state":
                    state = message["message"]
                    round_id = state.get("round", round_id)
                    status = "finished" if state.get("winner") else "move"
                    snake_push(manager, game, state, side, status)

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
    "SNAKE": snake_run,
}
