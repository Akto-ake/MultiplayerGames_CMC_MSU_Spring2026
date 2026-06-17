"""Входная точка запуска сервера."""

import asyncio
from lib.server import run_with_server


async def _run_server(server):
    """Запустить сервер и ждать, пока не будет остановлен."""

    await server.run()


async def main():
    """Запуск сервера."""

    await run_with_server(_run_server)


def cli() -> None:
    """Точка входа консоли для сервера."""

    asyncio.run(main())


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        pass
