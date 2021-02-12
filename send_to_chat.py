"""Script for sending messages to MineChat."""
import argparse
import asyncio
import json
import logging
from typing import Tuple, Union

import aiofiles

from settings import settings

CREDS_NICKNAME_FIELD = 'nickname'
CREDS_TOKEN_FIELD = 'account_hash'

logger = logging.getLogger()


async def send_message(
        message: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
) -> None:
    """Send a message to the authorized chat."""
    message_lines = message.split('\n')
    for message_line in message_lines:
        writer.write(f'{message_line}\n\n'.encode())
        logger.debug(f'Sent: {message_line}')
        chat_reply = await reader.readline()
        logger.debug(f'Received: {chat_reply}')


async def authorize(
        user_token: str, host: str, port: int,
) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Authorize with a user token."""
    reader, writer = await asyncio.open_connection(host, port)

    # Read the token prompt
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    writer.write(f'{user_token}\n'.encode())

    chat_reply = await reader.readline()
    user_creds = json.loads(chat_reply)
    if user_creds is None:
        raise RuntimeError('Unrecognized token.')

    logger.debug(f'Logged as "{user_creds[CREDS_NICKNAME_FIELD]}"')

    # Read the welcome message
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    return reader, writer


async def register(nickname: str, host: str, port: int) -> dict:
    """Register a new user. Return JSON with user creds."""
    nickname = nickname.replace('\n', ' ')

    reader, writer = await asyncio.open_connection(host, port)

    # Read the token prompt
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    writer.write(b'\n')

    # Read the nickname prompt
    chat_reply = await reader.readline()
    logger.debug(f'Received: {chat_reply}')

    writer.write(f'{nickname}\n'.encode())
    chat_reply = await reader.readline()
    user_creds = json.loads(chat_reply)

    logger.info(f'Registered new user: "{user_creds[CREDS_NICKNAME_FIELD]}"')

    writer.close()
    await writer.wait_closed()

    return user_creds


async def store_creds(user_creds: dict) -> None:
    """Save credentials received from the chat to a file."""
    creds_filename = f'creds {user_creds[CREDS_NICKNAME_FIELD]}'
    async with aiofiles.open(creds_filename, 'w') as creds_file:
        await creds_file.write(json.dumps(user_creds))
        logger.info(f'New user credentials are saved to {creds_filename}')


async def connect_and_send(
        host: str,
        port: int,
        message: str,
        nickname: str,
        token: Union[str, None] = None,
) -> None:
    """Connect to the chat and send a message. Register a new user if token is not provided."""
    if token is None:
        user_creds = await register(nickname=nickname, host=host, port=port)
        await store_creds(user_creds)
        token = user_creds[CREDS_TOKEN_FIELD]

    reader, writer = await authorize(user_token=token, host=host, port=port)

    await send_message(message=message, reader=reader, writer=writer)

    writer.close()
    await writer.wait_closed()


def parse_cmd_args() -> argparse.Namespace:
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--message',
        dest='message',
        required=True,
        help='Message that will be sent to a chat',
    )
    parser.add_argument(
        '--host',
        dest='host',
        default=settings.host,
        help='Hostname of a chat',
    )
    parser.add_argument(
        '--port',
        dest='port',
        default=settings.send_port,
        type=int,
        help='Port of a chat',
    )
    parser.add_argument(
        '--token',
        dest='token',
        default=None,
        help='Authorization token',
    )
    parser.add_argument(
        '--nickname',
        dest='nickname',
        default=settings.nickname,
        help='Nickname for a new user. Ignored if a token for existing user is provided',
    )
    return parser.parse_args()


def main() -> None:
    """Execute script for sending messages."""
    logging.basicConfig(level=logging.DEBUG)
    cmd_args = parse_cmd_args()

    asyncio.run(connect_and_send(
        host=cmd_args.host,
        port=cmd_args.port,
        message=cmd_args.message,
        token=cmd_args.token,
        nickname=cmd_args.nickname,
    ))


if __name__ == '__main__':
    main()
