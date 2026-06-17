"""Модульные тесты игровой логики Quiz."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.main_function_for_server import (
    QUIZ_QUESTION_BANK,
    QUIZ_ROUND_SIZE,
    quiz_build_round,
)


class QuizLogicTest(unittest.TestCase):
    """Тесты построения раунда викторины."""

    def test_round_contains_five_unique_questions(self) -> None:
        """Раунд состоит из пяти разных вопросов из банка."""

        random.seed(2026)

        round_questions = quiz_build_round()
        question_keys = [question["question"] for question in round_questions]

        self.assertEqual(len(round_questions), QUIZ_ROUND_SIZE)
        self.assertEqual(len(set(question_keys)), QUIZ_ROUND_SIZE)
        self.assertTrue(
            set(question_keys).issubset(
                {question["question"] for question in QUIZ_QUESTION_BANK}
            )
        )

    def test_each_round_question_has_four_options_and_correct_answer(self) -> None:
        """Каждый вопрос содержит четыре варианта и один правильный ответ."""

        random.seed(2026)

        for question in quiz_build_round():
            self.assertEqual(len(question["options"]), 4)
            self.assertEqual(len(set(question["options"])), 4)
            self.assertIn(question["correct"], question["options"])

    def test_round_does_not_mutate_question_bank_answers(self) -> None:
        """Перемешивание вариантов не меняет исходный банк вопросов."""

        before = [question["answers"].copy() for question in QUIZ_QUESTION_BANK]

        random.seed(2026)
        quiz_build_round()

        after = [question["answers"] for question in QUIZ_QUESTION_BANK]
        self.assertEqual(after, before)

    def test_question_bank_uses_localization_keys(self) -> None:
        """Вопросы и ответы хранятся ключами локализации."""

        for question in QUIZ_QUESTION_BANK:
            self.assertTrue(question["question"].startswith("quiz.question."))
            self.assertTrue(question["correct"].startswith("quiz.answer."))
            self.assertTrue(
                all(answer.startswith("quiz.answer.") for answer in question["answers"])
            )


if __name__ == "__main__":
    unittest.main()
