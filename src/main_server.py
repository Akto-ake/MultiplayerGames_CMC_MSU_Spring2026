"""Entry point for running the multiplayer game server."""

import asyncio
from lib.server import run_with_server


async def _run_server(server):
    """Start the server and keep it running until it is stopped."""

    await server.run()


async def main():
    """Run the server inside a wrapper that always closes it."""

    await run_with_server(_run_server)


def cli() -> None:
    """Console entry point for server app."""

    asyncio.run(main())


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        pass
