"""Entry point for running the multiplayer game server."""

import asyncio
import sys
from pathlib import Path
from server import run_with_server

CURRENT_DIR = Path(__file__).resolve().parent
LIB_DIR = CURRENT_DIR / "lib"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))


async def _run_server(server):
    """Start the server and keep it running until it is stopped."""

    await server.run()


async def main():
    """Run the server inside a wrapper that always closes it."""

    await run_with_server(_run_server)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
