import discord 
from discord.ext import commands
import os
import asyncio
from ui.RequestButton import RequestButtonView
from utils.utils import has_approval_perms

class tts_system_commands(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.hybrid_command(name="move", description="Force move the bot to a different VC (Central Command+).", extras={'category': 'TTS'})
    async def move(self, ctx: commands.Context, channel: discord.VoiceChannel):
        if not await has_approval_perms(ctx, 3):
            return

        if not ctx.author.voice:
            embed = discord.Embed(title="Whoops....", description="Please make sure you are in a channel!", color=discord.Color.light_grey())
            return await ctx.send(embed=embed, ephemeral=True)

        if ctx.guild.voice_client is None:
            embed = discord.Embed(title="Whoops....", description="I need to be connected to a voice channel to move!", color=discord.Color.light_grey())
            return await ctx.send(embed=embed, ephemeral=True)
        
        current_vc = ctx.guild.voice_client.channel

        await ctx.guild.voice_client.move_to(channel)

        # notify users in the channel that the bot was originially in that it has been moved
        embed_not = discord.Embed(
            title="Bot has been moved!",
            description=f"{ctx.author.mention} has moved the bot to {channel.mention}!",
            color=discord.Color.green()
        )

        await current_vc.send(embed=embed_not)

        # Send to the new channel the bot will be moved to
        embed = discord.Embed(title="Moved!", description=f"Moved to {channel.mention}!", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    @commands.hybrid_command(name="join", description="Have the bot join your current VC.", extras={'category': 'TTS'})
    async def join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        if not ctx.author.voice:
            embed = discord.Embed(title="Whoops....", description="Please make sure you are in a channel!", color=discord.Color.light_grey())
            return await ctx.send(embed=embed, ephemeral=True)
        
        if not channel:
            channel = ctx.author.voice.channel
        
        if ctx.guild.voice_client is None:
            await channel.connect(self_deaf=True)
        else:

            if channel == ctx.voice_client.channel:
                embed = discord.Embed(title="Hmm....", description=f"I'm already in {channel.mention}!", color=discord.Color.light_grey())
                return await ctx.send(embed=embed, ephemeral=True)

            view = RequestButtonView(self.bot, ctx.voice_client, channel)
            return await ctx.send(view=view, ephemeral=True)
            

        embed = discord.Embed(title="Connected!", description=f"Connected to {channel.mention}!", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    @commands.hybrid_command(name="leave", description="Have the bot leave your current VC.", extras={'category': 'TTS'})
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client is not None:
            guild_id = ctx.guild.id
            queue = self.bot.tts_queues[guild_id]
            channel: discord.VoiceChannel = ctx.voice_client.channel

            await ctx.guild.voice_client.disconnect()

            self._drain_queue(queue)
            await self._cancel_tts_task(guild_id)
            self._cleanup_mp3_files()
            
            embed = discord.Embed(title="Disconnected!", description=f"Disconnected from {channel.mention}!", color=discord.Color.green())
            embed.set_footer(text=f"Executed by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Whoops....", description="I need be in a channel to leave!", color=discord.Color.light_grey())
            await ctx.send(embed=embed, ephemeral=True)
    
    def _drain_queue(self, queue):
        """Drain the queue and delete files."""
        while not queue.empty():
            try:
                file = queue.get_nowait()
                queue.task_done()
                if os.path.exists(file):
                    os.remove(file)
            except asyncio.QueueEmpty:
                break

    async def _cancel_tts_task(self, guild_id):
        """Cancel the TTS worker task."""
        task = self.bot.tts_tasks.get(guild_id)
        if not task:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            del self.bot.tts_tasks[guild_id]

    def _cleanup_mp3_files(self):
        """Delete stray mp3 files."""
        for entry in os.scandir("."):
            if entry.is_file() and entry.name.startswith("tts_") and entry.name.endswith(".mp3"):
                try:
                    os.remove(entry.path)
                except OSError:
                    pass

    @commands.hybrid_command(name="clear", description="Clear the TTS queue.", extras={'category': 'TTS'})
    async def clear(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        vc = ctx.guild.voice_client
        queue = self.bot.tts_queues[guild_id]

        if not vc or queue.empty():
            return await ctx.send("There is nothing to clear!", ephemeral=True)

        if vc.is_playing():
            vc.stop()

        self._drain_queue(queue)
        await self._cancel_tts_task(guild_id)
        self._cleanup_mp3_files()

        embed = discord.Embed(title="Queue Cleared!", description="All records have been cleared", color=discord.Color.green())
        embed.set_footer(text=f"Executed by {ctx.author.name}")
        await ctx.send(embed=embed)

    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(tts_system_commands(bot))