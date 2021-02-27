import argparse
import asyncio
import logging
import json
import socket
from contextlib import asynccontextmanager
from typing import Tuple, Optional

import aiofiles

import gui
from settings import settings


logger = logging.getLogger()

CREDS_NICKNAME_FIELD = 'nickname'
CREDS_TOKEN_FIELD = 'account_hash'


class InvalidToken(Exception):
    """"""


@asynccontextmanager
async def chat_connection(
        host: str,
        port: int,
        status_updates_queue: asyncio.Queue,
        connection_type,
        user_token: Optional[str] = None
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Connect to the chat."""
    status_updates_queue.put_nowait(connection_type.INITIATED)

    reader, writer = await asyncio.open_connection(host, port)
    try:
        if user_token is not None:
            reader, writer = await authorize(user_token=user_token, reader=reader, writer=writer)
        yield reader, writer
    except InvalidToken:
        gui.show_error_message('Invalid token', 'User\' token is not recognized.')
        yield None, None
    finally:
        writer.close()
        await writer.wait_closed()


async def authorize(
        user_token: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Authorize with a user token."""
    # Read the token prompt
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    writer.write(f'{user_token}\n'.encode())
    await writer.drain()

    chat_reply = await reader.readline()
    user_creds = json.loads(chat_reply)
    if user_creds is None:
        raise InvalidToken

    logger.debug(f'Logged as "{user_creds[CREDS_NICKNAME_FIELD]}"')

    # Read the welcome message
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    return reader, writer


async def send_message(
        message: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
) -> None:
    """Send a message to the authorized chat."""
    message_lines = message.split('\n')
    for message_line in message_lines:
        writer.write(f'{message_line}\n\n'.encode())
        await writer.drain()
        logger.debug(f'Sent: {message_line}')

        chat_reply = await reader.readline()
        logger.debug(f'Received: {chat_reply}')


async def read_message(reader: asyncio.StreamReader) -> str:
    """Get a single message from a chat."""
    chat_message = await reader.readline()
    return chat_message.decode().rstrip('\n')


async def load_old_messages(history_file: str, messages_queue: asyncio.Queue) -> None:
    async with aiofiles.open(history_file, 'r') as history_file_descriptor:
        old_messages = await history_file_descriptor.readlines()
    for message in old_messages:
        messages_queue.put_nowait(str(message).rstrip('\n'))


async def read_msgs(
        host: str,
        port: int,
        messages_queue: asyncio.Queue,
        status_updates_queue: asyncio.Queue,
        chat_history_queue: asyncio.Queue,
) -> None:
    async with chat_connection(
            host=host,
            port=port,
            status_updates_queue=status_updates_queue,
            connection_type=gui.ReadConnectionStateChanged,
    ) as (reader, writer):
        while not reader.at_eof():
            message = await read_message(reader)
            messages_queue.put_nowait(message)
            chat_history_queue.put_nowait(message)


async def save_msgs(history_file: str, chat_history_queue: asyncio.Queue) -> None:
    while True:
        message = await chat_history_queue.get()
        async with aiofiles.open(history_file, 'a') as output_file:
            await output_file.write(f'{message}\n')


async def send_messages(host, port, token, sending_queue, status_updates_queue):
    async with chat_connection(
            host=host,
            port=port,
            status_updates_queue=status_updates_queue,
            connection_type=gui.SendingConnectionStateChanged,
            user_token=token,
    ) as (reader, writer):
        if any((reader is None, writer is None)):
            return
        while True:
            message = await sending_queue.get()
            await send_message(message=message, reader=reader, writer=writer)


async def start_chat(
        host: str,
        listen_port: int,
        send_port: int,
        history_file: str,
        token: str,
) -> None:

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    chat_history_queue = asyncio.Queue()

    await asyncio.gather(
        gui.draw(
            messages_queue=messages_queue,
            sending_queue=sending_queue,
            status_updates_queue=status_updates_queue,
        ),
        read_msgs(
            host=host,
            port=listen_port,
            messages_queue=messages_queue,
            status_updates_queue=status_updates_queue,
            chat_history_queue=chat_history_queue,
        ),
        save_msgs(history_file, chat_history_queue),
        load_old_messages(history_file, messages_queue),
        send_messages(
            host=host,
            port=send_port,
            token=token,
            sending_queue=sending_queue,
            status_updates_queue=status_updates_queue,
        ),
    )


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
        '--listen_port',
        dest='listen_port',
        default=settings.listen_port,
        type=int,
        help='Port of a chat to send messages',
    )
    parser.add_argument(
        '--send_port',
        dest='send_port',
        default=settings.send_port,
        type=int,
        help='Port of a chat to listen for messages',
    )
    parser.add_argument(
        '--history_file',
        dest='history_file',
        default=settings.history_file,
        type=str,
        help='File where the chat history will be saved',
    )
    parser.add_argument(
        '--token',
        dest='token',
        default=settings.token,
        help='Authorization token',
    )
    return parser.parse_args()


def main() -> None:
    """Run GUI version of the chat client."""
    logging.basicConfig(level=logging.DEBUG)
    cmd_args = parse_cmd_args()

    asyncio.run(
        start_chat(
            host=cmd_args.host,
            listen_port=cmd_args.listen_port,
            send_port=cmd_args.send_port,
            history_file=cmd_args.history_file,
            token=cmd_args.token,
        ),
    )


if __name__ == '__main__':
    main()
