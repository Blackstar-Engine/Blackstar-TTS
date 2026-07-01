import discord
from discord import ui
from ui.AcceptDenyButtons import AcceptDenyButtonsView

class RequestButton(ui.Button):
    def __init__(self, bot, voice_client: discord.VoiceClient, channel: discord.VoiceChannel):
        super().__init__(label="Send Request", style=discord.ButtonStyle.primary)
        self.bot = bot
        self.voice_client = voice_client
        self.channel = channel

    async def callback(self, interaction: discord.Interaction):
        sent_view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay("## Move Request"),
            ui.TextDisplay("Move request has been sent!"),
            accent_color=discord.Color.red()
        )
        sent_view.add_item(container)
        await interaction.response.edit_message(view=sent_view)

        view = AcceptDenyButtonsView(self.bot, interaction.user, self.channel)
        await self.voice_client.channel.send(view=view)

        await view.wait()

        confirm_view = ui.LayoutView()
        container = ui.Container(accent_color=discord.Color.green())

        if view.status == 1:
            await self.voice_client.move_to(self.channel)
            container.add_item(ui.TextDisplay(f"Request accepted! Moved to {self.channel.mention}."))
            confirm_view.add_item(container)
            await interaction.edit_original_response(view=confirm_view)
        else:
            container.add_item(ui.TextDisplay("Request denied."))
            confirm_view.add_item(container)
            await interaction.edit_original_response(view=confirm_view)

class RequestButtonView(ui.LayoutView):
    def __init__(self, bot, voice_client: discord.VoiceClient, channel: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.bot = bot
        self.voice_client = voice_client
        self.channel = channel
        action_row = ui.ActionRow(RequestButton(bot, voice_client, channel))

        container = ui.Container(
            ui.TextDisplay("## Already Connected!"),
            ui.TextDisplay(f"Im already connected to {voice_client.channel.mention}. Would you like to send a request to move me to {channel.mention}?"),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.red()
        )

        self.add_item(container)

    