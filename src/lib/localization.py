"""Runtime gettext/Babel localization helpers for GUI texts."""

from __future__ import annotations

import ast
import gettext
from pathlib import Path

DEFAULT_LOCALE = "ru"
SUPPORTED_LOCALES = ("ru", "en")
DOMAIN = "messages"
LOCALE_DIR = Path(__file__).resolve().parent / "locale"

_current_locale = DEFAULT_LOCALE
_catalog_cache: dict[str, gettext.NullTranslations] = {}
_po_cache: dict[str, dict[str, str]] = {}


def get_locale() -> str:
    """Return the active locale code."""

    return _current_locale


def set_locale(locale: str) -> None:
    """Set the active locale."""

    global _current_locale

    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"unsupported locale: {locale}")

    _current_locale = locale


def toggle_locale() -> str:
    """Switch between Russian and English locales."""

    next_locale = "en" if _current_locale == "ru" else "ru"
    set_locale(next_locale)
    return next_locale


def tr(message_id: str, **kwargs: object) -> str:
    """Translate a GUI message id for the active locale."""

    text = _translate(message_id)

    if kwargs:
        return text.format(**kwargs)

    return text


def tr_error(message: object) -> str:
    """Translate a server/client error message when a catalog key exists."""

    message_text = str(message or "")
    message_key = "error." + message_text.replace(" ", "_")
    translated = tr(message_key)

    if translated != message_key:
        return translated

    return message_text


def _translate(message_id: str) -> str:
    """Translate through compiled gettext catalog or source PO fallback."""

    catalog = _load_catalog(_current_locale)
    text = catalog.gettext(message_id)

    if text != message_id:
        return text

    return _load_po_messages(_current_locale).get(message_id, message_id)


def _load_catalog(locale: str) -> gettext.NullTranslations:
    """Load compiled gettext catalog for locale."""

    if locale not in _catalog_cache:
        _catalog_cache[locale] = gettext.translation(
            DOMAIN,
            localedir=LOCALE_DIR,
            languages=[locale],
            fallback=True,
        )

    return _catalog_cache[locale]


def _load_po_messages(locale: str) -> dict[str, str]:
    """Load untranslated source PO catalog when MO files are not built yet."""

    if locale in _po_cache:
        return _po_cache[locale]

    po_path = LOCALE_DIR / locale / "LC_MESSAGES" / f"{DOMAIN}.po"
    messages: dict[str, str] = {}

    if po_path.exists():
        messages = _parse_po(po_path)

    _po_cache[locale] = messages
    return messages


def _parse_po(path: Path) -> dict[str, str]:
    """Parse the simple Babel-generated PO shape used by this project."""

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
    """Decode a quoted PO string literal."""

    return ast.literal_eval(value)
