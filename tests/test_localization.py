"""Модульные тесты локализации интерфейса."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lib.localization import (
    get_locale,
    set_locale,
    toggle_locale,
    tr,
    tr_error,
)


class LocalizationTest(unittest.TestCase):
    """Тесты переключения языка и перевода сообщений."""

    def setUp(self) -> None:
        """Запоминает активный язык перед тестом."""

        self.locale = get_locale()
        set_locale("ru")

    def tearDown(self) -> None:
        """Возвращает язык, который был активен до теста."""

        set_locale(self.locale)

    def test_game_titles_are_translated_to_russian(self) -> None:
        """Названия игр переводятся на русский язык."""

        self.assertEqual(tr("game.pong.title"), "Пинг-понг")
        self.assertEqual(tr("game.snake.title"), "Змейка")
        self.assertEqual(tr("game.x_o.title"), "Крестики-нолики")

    def test_game_titles_are_translated_to_english(self) -> None:
        """Названия игр переводятся на английский язык."""

        set_locale("en")

        self.assertEqual(tr("game.pong.title"), "Pong")
        self.assertEqual(tr("game.snake.title"), "Snake")
        self.assertEqual(tr("game.x_o.title"), "X and O")

    def test_toggle_locale_switches_language(self) -> None:
        """Переключатель языка меняет ru на en и обратно."""

        self.assertEqual(toggle_locale(), "en")
        self.assertEqual(get_locale(), "en")
        self.assertEqual(toggle_locale(), "ru")
        self.assertEqual(get_locale(), "ru")

    def test_translation_formats_named_values(self) -> None:
        """Перевод подставляет именованные значения в шаблон."""

        text = tr("create.id_prompt", min_id=1000, max_id=9999)

        self.assertEqual(text, "Введите ID лобби от 1000 до 9999")

    def test_unknown_message_id_returns_key(self) -> None:
        """Неизвестный ключ возвращается без изменений."""

        self.assertEqual(tr("missing.translation.key"), "missing.translation.key")

    def test_server_error_is_translated(self) -> None:
        """Серверная ошибка переводится по ключу error."""

        self.assertEqual(tr_error("lobby is full"), "Лобби уже заполнено.")

        set_locale("en")

        self.assertEqual(tr_error("lobby is full"), "Lobby is full.")

    def test_unknown_server_error_returns_original_text(self) -> None:
        """Неизвестная серверная ошибка возвращается исходным текстом."""

        self.assertEqual(tr_error("custom backend error"), "custom backend error")

    def test_unsupported_locale_is_rejected(self) -> None:
        """Неподдерживаемый язык вызывает ошибку и не меняет текущий язык."""

        with self.assertRaises(ValueError):
            set_locale("de")

        self.assertEqual(get_locale(), "ru")


if __name__ == "__main__":
    unittest.main()
