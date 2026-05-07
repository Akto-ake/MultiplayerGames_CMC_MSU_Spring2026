"""Minimal automation commands: lint, docs, build."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> int:
    print("+", " ".join(command))
    return subprocess.run(command, cwd=ROOT).returncode


def lint() -> int:
    code1 = _run([sys.executable, "-m", "flake8", "src"])
    code2 = _run([sys.executable, "-m", "pydocstyle", "src"])
    return code1 or code2


def docs() -> int:
    return _run([sys.executable, "-m", "sphinx", "-b", "html", "docs", "docs/_build/html"])


def build() -> int:
    return _run([sys.executable, "-m", "build", "--wheel"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["lint", "docs", "build", "all"])
    args = parser.parse_args()

    if args.target == "lint":
        return lint()
    if args.target == "docs":
        return docs()
    if args.target == "build":
        return build()

    code = lint()
    if code:
        return code
    code = docs()
    if code:
        return code
    return build()


if __name__ == "__main__":
    raise SystemExit(main())
