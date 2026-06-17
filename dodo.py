import ast
import json
from pathlib import Path
import shutil
import sys

from doit.task import clean_targets


DOIT_CONFIG = {"default_tasks": ["html"]}
PYTHON = sys.executable
POT_FILE = Path("src/lib/locale/messages.pot")
IGNORED_SOURCE_PARTS = {"venv", ".venv", "new", "new_new", "__pycache__"}
TRANSLATION_KEY_PREFIXES = (
    "lang.",
    "menu.",
    "startup.",
    "server_unavailable.",
    "registration.",
    "join.",
    "create.",
    "main.",
    "games.",
    "game.",
    "pong.",
    "snake.",
    "quiz.",
    "x_o.",
    "error.",
)


def project_py_files():
    """Return project Python files, excluding local environments."""

    return [
        path
        for path in Path("src").glob("**/*.py")
        if not IGNORED_SOURCE_PARTS.intersection(path.parts)
    ]


def is_translation_key(value):
    """Return True when a string literal looks like an interface key."""

    return value.startswith(TRANSLATION_KEY_PREFIXES)


def literal_message_ids():
    """Collect literal translation ids stored outside direct tr(...) calls."""

    keys = set()

    for path in project_py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if is_translation_key(node.value):
                    keys.add(node.value)

    return keys


def pot_message_ids():
    """Collect message ids already present in the generated POT file."""

    if not POT_FILE.exists():
        return set()

    ids = set()
    for line in POT_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("msgid "):
            value = ast.literal_eval(stripped[6:])
            if value:
                ids.add(value)

    return ids


def po_quote(value):
    """Quote a string for a PO/POT file."""

    return json.dumps(value, ensure_ascii=False)


def append_literal_keys_to_pot():
    """Append literal interface keys that Babel cannot infer semantically."""

    missing = sorted(literal_message_ids() - pot_message_ids())

    if not missing:
        return

    with POT_FILE.open("a", encoding="utf-8") as pot:
        pot.write("\n")
        for key in missing:
            pot.write("#: literal translation key\n")
            pot.write(f"msgid {po_quote(key)}\n")
            pot.write('msgstr ""\n\n')


def task_pot():
    """Построение переводов."""
    py_files = project_py_files()
    return {
        "file_dep": py_files + [Path("babel.cfg")],
        "actions": [
            f"{PYTHON} -m babel.messages.frontend extract "
            "-F babel.cfg -k tr -o src/lib/locale/messages.pot src",
            append_literal_keys_to_pot,
        ],
        "targets": ["src/lib/locale/messages.pot"],
        "clean": [clean_targets],
    }


def task_po():
    """Обновление переводов."""
    return {
        "file_dep": ["src/lib/locale/messages.pot"],
        "actions": [
            f"{PYTHON} -m babel.messages.frontend update "
            "-D messages -i src/lib/locale/messages.pot "
            "-d src/lib/locale -l ru --init-missing --ignore-obsolete",
            f"{PYTHON} -m babel.messages.frontend update "
            "-D messages -i src/lib/locale/messages.pot "
            "-d src/lib/locale -l en --init-missing --ignore-obsolete",
        ],
        "targets": [
            "src/lib/locale/ru/LC_MESSAGES/messages.po",
            "src/lib/locale/en/LC_MESSAGES/messages.po",
        ],
        "task_dep": ["pot"],
        "clean": [clean_targets],
    }


def task_mo():
    """Компиляция переводов."""
    po_files = [
        "src/lib/locale/ru/LC_MESSAGES/messages.po",
        "src/lib/locale/en/LC_MESSAGES/messages.po",
    ]
    return {
        "file_dep": po_files,
        "actions": [
            f"{PYTHON} -m babel.messages.frontend compile "
            "-D messages -d src/lib/locale",
        ],
        "targets": [
            "src/lib/locale/ru/LC_MESSAGES/messages.mo",
            "src/lib/locale/en/LC_MESSAGES/messages.mo",
        ],
        "clean": [clean_targets],
    }


def task_i18n():
    """Создание i18n."""
    return {
        "actions": ["touch .i18n"],
        "targets": [".i18n"],
        "task_dep": ["pot", "mo"],
        "clean": [clean_targets],
    }


def task_html():
    """Создание html документации."""
    rstpy = list(Path("docs").glob("**/*.rst")) + project_py_files() + [
        Path("docs/conf.py"),
    ]
    return {
        "actions": ["sphinx-build -M html docs docs/_build"],
        "targets": ["docs/_build/html/index.html"],
        "file_dep": rstpy,
        "clean": [(shutil.rmtree, ["docs/_build"], {"ignore_errors": True})],
    }


def task_test():
    """Прогон тестов."""
    test_files = list(Path("tests").glob("test_*.py"))
    py_files = list(Path("src").glob("**/*.py"))
    return {
        "file_dep": [
            "src/lib/locale/ru/LC_MESSAGES/messages.mo",
            "src/lib/locale/en/LC_MESSAGES/messages.mo",
        ] + test_files + py_files,
        "actions": [
            f"PYTHONPATH=src {PYTHON} -m coverage run -m unittest discover -s tests",
            f"{PYTHON} -m coverage report",
            "touch .test",
        ],
        "targets": [".test"],
        "task_dep": ["i18n"],
        "uptodate": [False],
        "verbosity": 2,
        "clean": [clean_targets],
    }
