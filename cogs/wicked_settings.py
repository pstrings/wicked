import discord
from discord import app_commands
from discord.ext import commands
import json
import os

SETTINGS_FILE = "data/settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

class WickedSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()

    @app_commands.command(name="set_wicked_channel", description="Set the Wicked update channel and ping role.")
    @app_commands.describe(
        channel="The channel where updates will be posted", ping_role="The role to ping for updates")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @is_admin()
    async def set_wicked_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, ping_role: discord.Role):
        guild_id = str(interaction.guild_id)
        self.settings[guild_id] = self.settings.get(guild_id, {})
        self.settings[guild_id]['update_channel'] = channel.id
        self.settings[guild_id]['ping_role'] = ping_role.id
        save_settings(self.settings)
        await interaction.response.send_message(f"✅ Updates will be posted in {channel.mention} and ping {ping_role.mention}", ephemeral=True)

    @app_commands.command(name="add_x_account", description="Add an X (Twitter) account to follow.")
    @app_commands.describe(username="The X (Twitter) username to track (without @)")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @is_admin()
    async def add_x_account(self, interaction: discord.Interaction, username: str):
        guild_id = str(interaction.guild_id)
        g = self.settings.setdefault(guild_id, {})
        accounts = g.setdefault("x_accounts", [])
        if username.lower() not in accounts:
            accounts.append(username.lower())
            save_settings(self.settings)
            await interaction.response.send_message(f"✅ Now tracking `@{username}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ Already tracking `@{username}`", ephemeral=True)

    @app_commands.command(name="remove_x_account", description="Stop tracking an X (Twitter) account.")
    @app_commands.describe(username="The X (Twitter) username to stop tracking (without @)")
    @app_commands.guild_install()
    @app_commands.guild_only()
    @is_admin()
    async def remove_x_account(self, interaction: discord.Interaction, username: str):
        guild_id = str(interaction.guild_id)
        g = self.settings.get(guild_id, {})
        accounts = g.get("x_accounts", [])
        if username.lower() in accounts:
            accounts.remove(username.lower())
            save_settings(self.settings)
            await interaction.response.send_message(f"✅ Stopped tracking `@{username}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ `@{username}` was not being tracked", ephemeral=True)

async def setup(bot):
    await bot.add_cog(WickedSettings(bot))
