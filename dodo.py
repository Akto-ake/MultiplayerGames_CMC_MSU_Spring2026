"""Автоматизация задач для переводов, документации и тестов."""

import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from doit.task import clean_targets


DOIT_CONFIG = {"default_tasks": ["html"]}
PYTHON = sys.executable
POT_FILE = Path("src/lib/locale/messages.pot")
BUILD_DIRS = [
    Path("build"),
    Path("dist"),
    Path("src/multiplayer_games_cmc2026.egg-info"),
]
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
    """Найти Python-файлы проекта."""

    return [
        path
        for path in Path("src").glob("**/*.py")
        if not IGNORED_SOURCE_PARTS.intersection(path.parts)
    ]


def is_translation_key(value):
    """Проверить, похожа ли строка на ключ перевода."""

    return (
        value.startswith(TRANSLATION_KEY_PREFIXES)
        and value not in TRANSLATION_KEY_PREFIXES
    )


def literal_message_ids():
    """Собрать ключи переводов из строк в коде."""

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
    """Собрать ключи, которые уже есть в POT-файле."""

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
    """Подготовить строку для PO/POT-файла."""

    return json.dumps(value, ensure_ascii=False)


def append_literal_keys_to_pot():
    """Добавить в POT-файл ключи, которые Babel сам не нашёл."""

    missing = sorted(literal_message_ids() - pot_message_ids())

    if not missing:
        return

    with POT_FILE.open("a", encoding="utf-8") as pot:
        pot.write("\n")
        for key in missing:
            pot.write("#: literal translation key\n")
            pot.write(f"msgid {po_quote(key)}\n")
            pot.write('msgstr ""\n\n')


def touch(path):
    """Создать файл или обновить время изменения."""

    Path(path).touch()


def run_with_src_path(command):
    """Запустить команду с добавленным src в PYTHONPATH."""

    env = os.environ.copy()
    current_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"src{os.pathsep}{current_path}" if current_path else "src"
    )
    return subprocess.run(command, env=env).returncode == 0


def erase_build_artifacts():
    """Удалить сгенерированные файлы перед сборкой пакета."""

    for build_dir in BUILD_DIRS:
        shutil.rmtree(build_dir, ignore_errors=True)

    for pattern in ("**/__pycache__", "src/lib/locale/*/LC_MESSAGES/*.mo"):
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


def task_erase():
    """Очистить сгенерированные файлы."""

    return {
        "actions": [erase_build_artifacts],
    }


def task_pot():
    """Собрать POT-файл."""

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
    """Обновить PO-файлы."""

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
    """Собрать MO-файлы."""

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


def task_dist():
    """Собрать source distribution."""

    return {
        "actions": [f"{PYTHON} -m build --no-isolation -s"],
        "task_dep": ["erase"],
        "verbosity": 2,
    }


def task_wheel():
    """Собрать wheel."""

    return {
        "actions": [f"{PYTHON} -m build --no-isolation -w"],
        "task_dep": ["erase", "mo"],
        "verbosity": 2,
    }


def task_i18n():
    """Собрать файлы переводов."""

    return {
        "actions": [(touch, [".i18n"])],
        "targets": [".i18n"],
        "task_dep": ["pot", "mo"],
        "clean": [clean_targets],
    }


def task_html():
    """Собрать HTML-документацию."""

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
    """Запустить тесты."""

    test_files = list(Path("tests").glob("test_*.py"))
    py_files = list(Path("src").glob("**/*.py"))
    return {
        "file_dep": [
            "src/lib/locale/ru/LC_MESSAGES/messages.mo",
            "src/lib/locale/en/LC_MESSAGES/messages.mo",
        ] + test_files + py_files,
        "actions": [
            (
                run_with_src_path,
                [[
                    PYTHON,
                    "-m",
                    "coverage",
                    "run",
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                ]],
            ),
            f"{PYTHON} -m coverage report",
            (touch, [".test"]),
        ],
        "targets": [".test"],
        "task_dep": ["i18n"],
        "uptodate": [False],
        "verbosity": 2,
        "clean": [clean_targets],
    }
