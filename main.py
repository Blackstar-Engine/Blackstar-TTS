import discord 
from discord.ext import commands
from cogwatch import watch
import os
import sys
import asyncio
from collections import defaultdict
from utils.constants import BlackstarConstants, whitelisted_guilds, logger, discord_http_logger, discord_logger

constants = BlackstarConstants()

if constants.ENVIRONMENT == "PRODUCTION":
    presence = "t!join"
else:
    presence = "Testing TTS Bot"


class Bot(commands.Bot):
    def __init__(self):
        intent = discord.Intents.default()
        intent.message_content = True
        intent.members = True

        super().__init__(
            command_prefix=constants.PREFIX,
            intents=intent,
            chunk_guilds_at_startup=False,
            help_command=None,
            reconnect=True,
        )
    
    async def is_owner(self, user: discord.User) -> bool:
        bypassed_users = [
            758170288566566952, #Ghost
            1371489554279825439, #Wolf
            1007353417779396709 #Option
        ]

        return user.id in bypassed_users

    async def setup_hook(self):
        cog_counter = 0

        for root, _, files in os.walk("./cogs"):
            for file in files:
                if file.endswith(".py"):
                    cog_path = os.path.relpath(os.path.join(root, file), "./cogs")
                    cog_module = cog_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        await bot.load_extension(f"cogs.{cog_module}")
                        cog_counter += 1
                        logger.info(f"{cog_module} loaded successfully")
                    except Exception as e:
                        logger.error(f"{cog_module} failed to load: {e}")

        logger.info(f"Successfully loaded {cog_counter} cog(s)")

    async def on_connect(self):
        discord_http_logger.info('Connected to discord gateway')
    
    async def on_disconnected(self):
        discord_http_logger.error('Disconnected from discord gateway')

    async def on_shard_connect(self, shard_id: int):
        await self.tree.sync()
        discord_http_logger.info(f'Shard {shard_id} has connected to discord gateway')
    
    async def on_shard_disconnected(self, shard_id: int):
        discord_http_logger.error(f'Shard {shard_id} has disconnected from discord gateway')
            

    @watch(path='cogs', preload=False)
    async def on_ready(self):
        bot.tts_queues = defaultdict(asyncio.Queue)
        bot.tts_tasks = {}

        await bot.change_presence(activity=discord.CustomActivity(name=presence))

        for guild in bot.guilds:
            if guild.id not in whitelisted_guilds:
                logger.error(f"Server not found: {guild.name}({guild.id})")
                try:
                    await guild.leave()
                except Exception:
                    await guild.owner.send(f"Please remove me from **{guild.name}**, I will not work!")
                
            else:
                logger.info(f'Chunked: {guild.id}')
                await guild.chunk()
        
        logger.info(f'{self.user} is ready.')

bot = Bot()

async def start_bot():
    max_retries = 10
    retry_delay = 5
    retries = 0

    while retries < max_retries:
        try:
            discord_logger.info(f'Starting bot... (Attempt {retries + 1})')
            await bot.start(constants.TOKEN)
        except (TimeoutError) as e:
            retries += 1
            discord_logger.error(f'Connection error occured. Thrown error: {e}')

            if retries < max_retries:
                discord_logger.info(f'Retrying in {retry_delay} seconds...')
                await asyncio.sleep(retry_delay)
            else:
                break

        except Exception as e:
            discord_logger.error(f'Unexpected error occured. {e}')
            sys.exit('FAILED TO START: UNEXPECTED ERROR')

    
    discord_logger.critical('Max retries reached - stopping bot...')
    sys.exit('FAILED TO START: MAX RETRIES')
            

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        discord_logger.info('Bot shutting down...')
        sys.exit(0)