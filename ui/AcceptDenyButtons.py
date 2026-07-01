import discord
from discord import ui

class AcceptDenyButtonsView(ui.LayoutView):
    def __init__(self, bot, requester, target_channel):
        super().__init__(timeout=None)
        self.bot = bot
        self.requester = requester
        self.target_channel = target_channel
        self.status = None

        # Accept button
        accept_button = ui.Button(label="Accept", style=discord.ButtonStyle.green)
        accept_button.callback = self.accept

        # Deny button
        deny_button = ui.Button(label="Deny", style=discord.ButtonStyle.red)
        deny_button.callback = self.deny

        action_row = ui.ActionRow(accept_button, deny_button)

        container = ui.Container(
            ui.TextDisplay("## Move Request"),
            ui.TextDisplay(f"{requester.mention} has requested to move the bot to {target_channel.mention}. Do you accept?"),
            ui.Separator(),
            action_row,
            accent_color=discord.Color.yellow()
        )

        self.add_item(container)

    async def accept(self, interaction: discord.Interaction):
        self.status = 1

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay("## Move Request"),
            ui.TextDisplay(f"{interaction.user.mention} has accepted the move request! Moving to {self.target_channel.mention}..."),
            accent_color=discord.Color.green()
        )
        view.add_item(container)
        await interaction.response.edit_message(view=view)

        self.stop()

    async def deny(self, interaction: discord.Interaction):
        self.status = 0

        view = ui.LayoutView()
        container = ui.Container(
            ui.TextDisplay("## Move Request"),
            ui.TextDisplay(f"{interaction.user.mention} has denied the move request."),
            accent_color=discord.Color.red()
        )
        view.add_item(container)
        await interaction.response.edit_message(view=view)

        self.stop()