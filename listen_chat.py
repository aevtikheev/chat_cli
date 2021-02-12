"""Script for listening MineChat messages."""
import argparse
import asyncio
import datetime
import logging

import aiofiles

from settings import settings

logger = logging.getLogger()


def format_message(message: str) -> str:
    """Add timestamp to the message."""
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y.%m.%d %H:%M')
    return f'[{timestamp}] {message}'


async def log_message(message: str, history_file: str) -> None:
    """Log the message to chat history file and console."""
    formatted_message = format_message(message)
    logger.info(formatted_message)
    async with aiofiles.open(history_file, 'a') as output_file:
        await output_file.write(f'{formatted_message}\n')


async def get_message(reader: asyncio.StreamReader) -> str:
    """Get a single message from a chat."""
    chat_message = await reader.readline()
    return chat_message.decode().rstrip('\n')


async def listen_chat(host: str, port: int, history_file: str) -> None:
    """Connect to the chat and log incoming messages."""
    reader, writer = await asyncio.open_connection(host, port)
    while not reader.at_eof():
        message = await get_message(reader)
        await log_message(message, history_file)
    writer.close()
    await writer.wait_closed()


def parse_cmd_args() -> argparse.Namespace:
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host',
        dest='host',
        default=settings.host,
        help='Hostname of a chat',
    )
    parser.add_argument(
        '--port',
        dest='port',
        default=settings.listen_port,
        type=int,
        help='Port of a chat',
    )
    parser.add_argument(
        '--history',
        dest='history',
        default=settings.history_file,
        type=str,
        help='File where the chat history will be saved',
    )
    return parser.parse_args()


def main() -> None:
    """Execute chat listening script."""
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    cmd_args = parse_cmd_args()

    logger.info('Listening started.')
    try:
        asyncio.run(
            listen_chat(host=cmd_args.host, port=cmd_args.port, history_file=cmd_args.history),
        )
    except KeyboardInterrupt:
        logger.info('Listening cancelled.')


if __name__ == '__main__':
    main()
