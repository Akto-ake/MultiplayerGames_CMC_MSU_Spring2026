"""Помощники для перевода текстов интерфейса."""

from __future__ import annotations

import ast
import gettext
from pathlib import Path

DEFAULT_LOCALE = "ru"
SUPPORTED_LOCALES = ("ru", "en")
DOMAIN = "messages"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"
ERROR_TRANSLATION_KEYS = (
    "error.bad_json",
    "error.json_message_must_be_dict",
    "error.unknown_target",
    "error.unknown_message",
    "error.bad_nick",
    "error.leave_lobby_first",
    "error.first_login",
    "error.game_not_found",
    "error.bad_lobby_id",
    "error.lobby_id_is_busy",
    "error.no_free_lobby_ids",
    "error.lobby_not_found",
    "error.nick_is_busy_in_lobby",
    "error.lobby_is_full",
    "error.first_create_or_join_lobby",
    "error.not_in_this_lobby",
    "error.lobby_crashed",
    "error.not_enough_players",
    "error.game_is_not_started",
    "error.wrong_turn",
    "error.wrong_symbol",
    "error.cell_is_busy",
    "error.game_run_function_is_not_set",
    "error.client_is_not_connected",
    "error.server_unavailable",
)

_current_locale = DEFAULT_LOCALE
_catalog_cache: dict[str, gettext.NullTranslations] = {}
_po_cache: dict[str, dict[str, str]] = {}


def get_locale() -> str:
    """Вернуть текущий язык интерфейса."""

    return _current_locale


def set_locale(locale: str) -> None:
    """Поменять язык интерфейса."""

    global _current_locale

    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"unsupported locale: {locale}")

    _current_locale = locale


def toggle_locale() -> str:
    """Переключить язык между русским и английским."""

    next_locale = "en" if _current_locale == "ru" else "ru"
    set_locale(next_locale)
    return next_locale


def tr(message_id: str, **kwargs: object) -> str:
    """Вернуть перевод сообщения по его ключу."""

    text = _translate(message_id)

    if kwargs:
        return text.format(**kwargs)

    return text


def tr_error(message: object) -> str:
    """Перевести сообщение об ошибке, если для него есть перевод."""

    message_text = str(message or "")
    message_key = "error." + message_text.replace(" ", "_")
    translated = tr(message_key)

    if translated != message_key:
        return translated

    return message_text


def _translate(message_id: str) -> str:
    """Найти перевод сообщения в MO- или PO-файле."""

    catalog = _load_catalog(_current_locale)
    text = catalog.gettext(message_id)

    if text != message_id:
        return text

    return _load_po_messages(_current_locale).get(message_id, message_id)


def _load_catalog(locale: str) -> gettext.NullTranslations:
    """Загрузить MO-файл с переводами."""

    if locale not in _catalog_cache:
        _catalog_cache[locale] = gettext.translation(
            DOMAIN,
            localedir=LOCALE_DIR,
            languages=[locale],
            fallback=True,
        )

    return _catalog_cache[locale]


def _load_po_messages(locale: str) -> dict[str, str]:
    """Загрузить переводы из PO-файла, если MO-файла нет."""

    if locale in _po_cache:
        return _po_cache[locale]

    po_path = LOCALE_DIR / locale / "LC_MESSAGES" / f"{DOMAIN}.po"
    messages: dict[str, str] = {}

    if po_path.exists():
        messages = _parse_po(po_path)

    _po_cache[locale] = messages
    return messages


def _parse_po(path: Path) -> dict[str, str]:
    """Прочитать ключи и переводы из PO-файла."""

    messages: dict[str, str] = {}
    current_field = None
    current_id = ""
    current_str = ""

    def flush() -> None:
        nonlocal current_id, current_str

        if current_id and current_str:
            messages[current_id] = current_str

        current_id = ""
        current_str = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("msgid "):
            flush()
            current_field = "msgid"
            current_id = _po_string_value(line[6:])
            continue

        if line.startswith("msgstr "):
            current_field = "msgstr"
            current_str = _po_string_value(line[7:])
            continue

        if line.startswith('"') and current_field == "msgid":
            current_id += _po_string_value(line)
            continue

        if line.startswith('"') and current_field == "msgstr":
            current_str += _po_string_value(line)

    flush()
    return messages


def _po_string_value(value: str) -> str:
    """Прочитать строку из PO-файла."""

    return ast.literal_eval(value)
