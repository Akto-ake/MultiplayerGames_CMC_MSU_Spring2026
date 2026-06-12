"""Точка входа клиентского приложения."""

import asyncio
import threading

from lib.frontend import Manager
from lib.menu import run as front
from lib.backend import run as back


def _run_backend():
    asyncio.run(back())


async def main():
    """запуск бэка и фронта"""
    backend_thread = threading.Thread(target=_run_backend, name="backend")

    try:
        backend_thread.start()
        await front()
    finally:
        Manager().push_message((0,))

        if backend_thread.is_alive():
            backend_thread.join()


def cli() -> None:
    """Console entry point for client app."""

    asyncio.run(main())


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        # Чтобы не вылетало ошибок при нажатии Ctrl+C
        pass
