import discord
from discord.ext import commands
import asyncio
from cogs.TTS import tts_system_commands

class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    async def clear_queue(self, queue, guild_id):
        try:
            tts_system_commands._drain_queue(self, queue)
            await tts_system_commands._cancel_tts_task(self, guild_id)
            tts_system_commands._cleanup_mp3_files(self)
        except Exception as e:
            print(f"VC Update Error: {e}")
    
    async def handle_tts_logic(self, vc: discord.VoiceClient, member: discord.Member, before: discord.VoiceState):
        channel = vc.channel
        guild_id = member.guild.id
        queue = self.bot.tts_queues[guild_id]

        if before.channel == channel:
            humans = [m for m in channel.members if not m.bot]

            if len(humans) == 0:
                await asyncio.sleep(30)

                current_vc = member.guild.voice_client
                if not current_vc or current_vc.channel != channel:
                    return

                humans_after = [m for m in current_vc.channel.members if not m.bot]
                if len(humans_after) == 0:
                    await current_vc.disconnect()
                    await self.clear_queue(queue, guild_id)
                    
                else:
                    # There are now people in the same channel, so keep the bot connected
                    return

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        await self.bot.wait_until_ready()

        vc = member.guild.voice_client
        if vc:
            await self.handle_tts_logic(vc, member, before)
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot=bot))
