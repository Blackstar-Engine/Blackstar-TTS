import discord
from discord.ext import commands
from utils.constants import MESSAGE_CODE_RE
from utils.utils import tts_to_file, tts_match_object, tts_logic
import os
import asyncio
import time
from datetime import datetime, UTC

class Messaging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_speaker = {}
        self.last_message_time = {}

    def _create_after_playback(self, file, queue):
        def _after_playback(error):
            if error:
                print(f"Playback error: {error}")

            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                print(f"Cleanup failed: {e}")

            self.bot.loop.call_soon_threadsafe(queue.task_done)

        return _after_playback

    async def _play_audio(self, vc: discord.VoiceClient, source, file, queue):
        try:
            vc.play(source, after=self._create_after_playback(file, queue))
        except Exception as e:
            print(f"vc.play failed: {e}")
            try:
                if os.path.exists(file):
                    os.remove(file)
            finally:
                queue.task_done()
            return

        while vc.is_connected() and vc.is_playing():
            await asyncio.sleep(0.1)
    
    async def tts_player(self, guild: discord.Guild):
        queue: asyncio.Queue = self.bot.tts_queues[guild.id]

        try:
            while True:
                file = await queue.get()
                vc: discord.VoiceClient = guild.voice_client

                source = tts_logic(queue, vc, file)
                if not source:
                    continue

                await self._play_audio(vc, source, file, queue)

        except asyncio.CancelledError:
            # allows clean shutdowns
            raise
        except Exception as e:
            print(f"TTS player crashed in guild {guild.id}: {e}")
    
    async def TTS_Event(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.voice: 
            if message.content.startswith(("-", "d!", "!")):
                return
            
            bot_vc = message.guild.voice_client 
            guild_id = message.guild.id
            user = message.author
            now = time.time()
            if bot_vc and message.channel == message.guild.voice_client.channel: 
                content = tts_match_object(message)

                last_speaker = self.last_speaker.get(guild_id)
                last_message_time = now - self.last_message_time.get(guild_id, 0)

                file = await tts_to_file(user, last_speaker, last_message_time, str(content)) 

                self.last_speaker[guild_id] = message.author.id
                self.last_message_time[guild_id] = now
                
                queue = self.bot.tts_queues[message.guild.id]
                await queue.put(file)

                if message.guild.id not in self.bot.tts_tasks or self.bot.tts_tasks[message.guild.id].done():
                    self.bot.tts_tasks[message.guild.id] = self.bot.loop.create_task(
                        self.tts_player(message.guild)
                    )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.wait_until_ready()
        
        if message.author == self.bot.user or message.author.bot:
            return
        # Text to Speech
        await self.TTS_Event(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Messaging(bot))