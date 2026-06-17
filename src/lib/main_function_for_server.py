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


QUIZ_ROUND_SIZE = 5
QUIZ_QUESTION_BANK = [
    {
        "question": "Назовите второе имя Майкла Джексона?",
        "correct": "Джозеф",
        "answers": ["Джозеф", "Джон", "Джеймс", "Джим"],
    },
    {
        "question": (
            "Как назывался особый головной убор, который носили фараоны "
            "в Древнем Египте?"
        ),
        "correct": "Немес",
        "answers": ["Картуз", "Немес", "Корона", "Убрус"],
    },
    {
        "question": "Детинцем на Руси называли...",
        "correct": "Кремль",
        "answers": ["Кремль", "Школу", "Княжеский терем", "Монастырь"],
    },
    {
        "question": "Как называли строителя в старину?",
        "correct": "Зодчий",
        "answers": ["Бондарь", "Бортник", "Зодчий", "Кормчий"],
    },
    {
        "question": "Продолжите пословицу: «Знает кошка...»",
        "correct": "Чье мясо съела",
        "answers": [
            "Да мыши не знают",
            "Почем фунт лиха",
            "Где собака зарыта",
            "Чье мясо съела",
        ],
    },
    {
        "question": "Какое из этих растений - плотоядное?",
        "correct": "Росянка",
        "answers": ["Володушка", "Росянка", "Мытник", "Астрагал"],
    },
    {
        "question": "Как называется человек, покоряющий крыши многоэтажных домов?",
        "correct": "Руфер",
        "answers": ["Диггер", "Сталкер", "Руфер", "Байкер"],
    },
    {
        "question": "Сколько лет проходит между ситцевой и золотой свадьбой?",
        "correct": "49",
        "answers": ["11", "19", "25", "49"],
    },
]


def quiz_build_round():
    """Выбирает вопросы и перемешивает варианты ответов для раунда."""

    selected = random.sample(
        QUIZ_QUESTION_BANK,
        min(QUIZ_ROUND_SIZE, len(QUIZ_QUESTION_BANK)),
    )
    questions = []

    for item in selected:
        options = item["answers"].copy()
        random.shuffle(options)
        questions.append(
            {
                "question": item["question"],
                "correct": item["correct"],
                "options": options,
            }
        )

    return questions


async def quiz_main_lobby(lobby):
    """Минимальная серверная логика лобби викторины."""

    questions = []
    question_index = 0
    answers = {}
    scores = {}
    players = []
    correct_answers = []
    stage = "waiting"

    def current_result():
        if not questions:
            return None

        question = questions[question_index]
        correct = question["correct"]
        question_scores = {player: 0 for player in players}

        for player, answer_index in answers.items():
            if question["options"][answer_index] == correct:
                question_scores[player] = 1

        return {
            "question": question["question"],
            "correct": correct,
            "scores": question_scores,
        }

    def update_scores():
        scores.clear()
        scores.update({player: 0 for player in players})

        for result in correct_answers:
            for player, points in result.get("scores", {}).items():
                scores[player] = scores.get(player, 0) + points

    def start_round():
        nonlocal answers, correct_answers, players, question_index, questions
        nonlocal scores, stage

        players = lobby.get_list_nicks()
        questions = quiz_build_round()
        question_index = 0
        answers = {}
        scores = {player: 0 for player in players}
        correct_answers = []
        stage = "question"
        lobby.push_message(quiz_message("question"))

    def quiz_payload():
        payload = {
            "players": players,
            "question_index": question_index,
            "total_questions": len(questions),
            "answers": answers.copy(),
            "scores": scores.copy(),
            "correct_answers": correct_answers.copy(),
        }

        if questions:
            question = questions[question_index]
            payload.update(
                {
                    "question": question["question"],
                    "options": question["options"],
                }
            )

        return payload

    def quiz_message(status):
        return {
            "target": "client",
            "status": status,
            "message": quiz_payload(),
        }

    def finish_question():
        nonlocal stage

        result = current_result()
        if result is None:
            return

        if len(correct_answers) <= question_index:
            correct_answers.append(result)
        else:
            correct_answers[question_index] = result
        update_scores()

        stage = "answered"
        lobby.push_message(quiz_message("answered"))

    while True:
        nick, message = await lobby.pop_message()
        target = message.get("target")
        status = message.get("status")

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
                stage = "waiting"
                answers = {}
                questions = []
                players = lobby.get_list_nicks()
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
                            "status": "waiting",
                            "message": nick,
                        },
                        [nick],
                    )
                    continue

                start_round()

            case "client", "answer":
                if stage not in ("question", "answered") or nick not in players:
                    continue

                answer_index = message.get("message")
                if not isinstance(answer_index, int):
                    continue

                if answer_index not in range(4):
                    continue

                answers[nick] = answer_index
                if stage == "answered":
                    finish_question()
                    continue

                lobby.push_message(quiz_message("answer"))

                if len(answers) == len(players):
                    finish_question()

            case "client", "next":
                if stage != "answered":
                    continue

                if question_index == len(questions) - 1:
                    stage = "finished"
                    lobby.push_message(quiz_message("finished"))
                    continue

                question_index += 1
                answers = {}
                stage = "question"
                lobby.push_message(quiz_message("question"))

            case _:
                continue


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
    "QUIZ": {
        "main_func": quiz_main_lobby,
        "max_players": 2,
    },
}
