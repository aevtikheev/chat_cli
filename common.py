"""Common functions to work with MineChat."""
import asyncio
from contextlib import asynccontextmanager
from typing import Tuple


@asynccontextmanager
async def chat_connection(
        host: str, port: int,
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect to the chat."""
    reader, writer = await asyncio.open_connection(host, port)
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()
