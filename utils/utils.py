import discord
from discord.ext import commands
from utils.constants import BlackstarConstants
import uuid
import re
import edge_tts
import unicodedata
import os
import asyncio
from utils.constants import (
    URL_RE,
    ROLE_RE,
    USER_RE,
    CHANNEL_RE,
    EMOJI_RE,
    BlackstarConstants,
)

constants = BlackstarConstants()

async def has_approval_perms(ctx: commands.Context, level: int, send_message: bool = True) -> bool:
    if isinstance(ctx, discord.Interaction):
        member = ctx.user
    else:
        member = ctx.author

    if constants.ENVIRONMENT == "PRODUCTION":
        results = {
            "foundation_command": 1413208971304636597,
            "site_command": 1422416268585341049,
            "high_command": 1413226553982320713,
            "central_command": 1413226456968069180,
            "wolf_id": 1371489554279825439,
            "ghost_id": 758170288566566952,
            "option_id": 1007353417779396709,
        }
    else:
        results = {
        "foundation_command": 1450297609515307134,
        "site_command": 1450297617073442816,
        "high_command": 1450297635994079375,
        "central_command": 1450297654662660156,
        "wolf_id": 1371489554279825439,
        "ghost_id": 758170288566566952,
        "option_id": 1007353417779396709,
    }

    if member.id == results["wolf_id"]:
        return True
    
    if constants.ENVIRONMENT == "DEVELOPMENT" and member.id in (results["ghost_id"], results["option_id"]):
        return True
    
    match level:
        case 1:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"],
                results["ia_id"]
            }
        case 2:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"],
                results["drm_id"]
            }
        case 3:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"],
                results["central_command"]
            }
        case 4:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"],
                results["high_command"]
            }
        case 5:
            allowed_roles = {
                results["foundation_command"],
                results["site_command"]
            }
        case 6:
            allowed_roles = {
                results["foundation_command"]
            }
    
    roles = any(role.id in allowed_roles for role in member.roles)
    if roles:
        return True
    
    if send_message:
        if isinstance(ctx, discord.Interaction):
            try:
                await ctx.response.send_message("You do not have the required permissions to use this command.", ephemeral=True)
            except discord.HTTPException:
                await ctx.followup.send("You do not have the required permissions to use this command.", ephemeral=True)
        else:
            await ctx.send("You do not have the required permissions to use this command.")
    
    return False


def clean_username(name: str) -> str:
    return re.sub(r"\[.*?\]\s*", "", name).strip()

async def tts_to_file(user: discord.Member, last_speaker, last_message_time, text: str) -> str:
    filename = f"tts_{uuid.uuid4()}.mp3"

    user_display = unicodedata.normalize("NFKD", user.display_name)

    user_display = user_display.encode("ascii", "ignore").decode("ascii")

    display_name = clean_username(user_display)

    if last_speaker == user.id and last_message_time < 30:
        text = f"{text}"
    else:
        text = f"{display_name} said {text}"

    voice = "en-CA-LiamNeural"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

    return filename

def tts_match_object(message: discord.Message):
    text = message.content

    # Replace discord formatted things
    text = EMOJI_RE.sub("emoji", text)
    text = CHANNEL_RE.sub("channel", text)
    text = USER_RE.sub("user", text)
    text = ROLE_RE.sub("role", text)

    # Replace links anywhere in message
    text = URL_RE.sub("link", text)

    # Replace attachments (images, files, etc.)
    if message.attachments:
        if text:
            text += " with an attachment"
        else:
            text = "an attachment"

    return text.strip()

def tts_logic(queue: asyncio.Queue, vc: discord.VoiceClient, file):
    # File was deleted by clear() — skip it
    if not os.path.exists(file):
        queue.task_done()
        return None

    if not vc or not vc.is_connected():
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        queue.task_done()
        return None

    try:
        source = discord.FFmpegPCMAudio(file)
        return source

    except Exception as e:
        print(f"FFmpeg failed to open {file}: {e}")
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
        queue.task_done()
        return None