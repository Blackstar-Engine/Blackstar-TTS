from typing import Final
import os
from dotenv import load_dotenv
import logging
import sys
import re
load_dotenv()

class BlackstarConstants:
    '''
    Defines constants, they should always be capitals and set via the type of FINAL.
    '''
    ENVIRONMENT: Final[bool] = str(os.getenv('ENVIRONMENT'))
    TOKEN: Final[str] = str(os.getenv('TOKEN'))
    PREFIX: Final[str] = str(os.getenv('PREFIX'))

constants = BlackstarConstants()
whitelisted_guilds = [1411941814923169826, 1450297281088720928, 846843382713417810]
EMOJI_RE = re.compile(r"<a?:\w+:\d{17,20}>")
CHANNEL_RE = re.compile(r"<#\d{17,20}>")
USER_RE = re.compile(r"<@!?\d{17,20}>")
ROLE_RE = re.compile(r"<@&\d{17,20}>")
URL_RE = re.compile(r"https?://\S+")
MESSAGE_CODE_RE = re.compile(r"^(\[[^\]]+\]|\*\*[\s\S]+?\*\*)")#  \*\*(.*?)\*\* | This will check for ****

if constants.ENVIRONMENT != "PRODUCTION":
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.theme import Theme

    console = Console(
        theme=Theme(
            {
                'logging.level.info': '#a6e3a1',
                'logging.level.debug': '#8aadf4',
                'logging.level.warning': '#f9e2af',
                'logging.level.error': '#f38ba8',
            }
        )
    )
    handler = RichHandler(tracebacks_width=200, console=console, rich_tracebacks=True)
else:
    handler = logging.StreamHandler()  # plain logs for prod


handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
level = logging.DEBUG if constants.ENVIRONMENT != "PRODUCTION" else logging.INFO

logger = logging.getLogger('Blackstar Engine')
logger.setLevel(level)
logger.addHandler(handler)
logger.propagate = False

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
discord_logger.addHandler(handler)
discord_logger.propagate = False

discord_http_logger = logging.getLogger('discord.http')
discord_http_logger.setLevel(logging.INFO)
discord_http_logger.addHandler(handler)
discord_http_logger.propagate = False


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception with full traceback
    logger.critical('Uncaught exception', exc_info=(exc_type, exc_value, exc_traceback))