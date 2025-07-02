import discord
from discord.ext import commands, tasks
import json
import os
import logging
from cogs.social.twitter import TwitterAPI
from discord import app_commands

SETTINGS_FILE = "data/settings.json"
TWEETS_FILE = "data/last_tweets.json"
LOG_FILE = "logs/wicked.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

class WickedPoster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_json(SETTINGS_FILE)
        self.last_tweets = load_json(TWEETS_FILE)
        self.fetch_tweets.start()

    def cog_unload(self):
        self.fetch_tweets.cancel()

    @tasks.loop(minutes=5)
    async def fetch_tweets(self):
        await self.check_all()

    @app_commands.command(name="force_check", description="Force check all X accounts for new posts now.")
    async def force_check(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Checking now...", ephemeral=True)
        await self.check_all()
        await interaction.followup.send("✅ Check complete.", ephemeral=True)

    async def check_all(self):
        for guild_id, config in self.settings.items():
            channel = self.bot.get_channel(config.get("update_channel"))
            if not channel:
                continue
            role_id = config.get("ping_role")
            for username in config.get("x_accounts", []):
                tweet = await TwitterAPI.get_latest_tweet(username)
                if not tweet:
                    logging.warning(f"No tweet fetched for @{username}")
                    continue

                tweet_id = tweet["id"]
                if self.last_tweets.get(username) == tweet_id:
                    continue

                self.last_tweets[username] = tweet_id
                save_json(TWEETS_FILE, self.last_tweets)

                embed = discord.Embed(
                    title=f"New Tweet from @{username}",
                    description=tweet["text"],
                    url=f"https://x.com/{username}/status/{tweet_id}",
                    color=discord.Color.purple()
                )
                embed.set_author(name=f"@{tweet['author']['username']}", icon_url=tweet['author']['profile_image_url'])
                embed.set_footer(text=f"Tweet ID: {tweet_id}")
                embed.timestamp = discord.utils.parse_time(tweet['created_at'])

                if tweet.get("media"):
                    media = tweet["media"][0]
                    embed.set_image(url=media.get("url") or media.get("preview_image_url"))

                await channel.send(f"<@&{role_id}>", embed=embed)
                logging.info(f"Posted new tweet from @{username} in guild {guild_id}")

async def setup(bot):
    await bot.add_cog(WickedPoster(bot))
