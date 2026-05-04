"""Entry point for running the multiplayer game server."""

import asyncio
import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
LIB_DIR = CURRENT_DIR / "lib"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from server import Server


async def main():
    """Start the server and run it until it is stopped."""

    server = Server()
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
