import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

class TwitterAPI:
    BASE_URL = "https://api.twitter.com/2"

    @staticmethod
    async def get_user_id(username):
        url = f"{TwitterAPI.BASE_URL}/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data["data"]["id"]

    @staticmethod
    async def get_latest_tweet(username):
        user_id = await TwitterAPI.get_user_id(username)
        if not user_id:
            return None

        url = f"{TwitterAPI.BASE_URL}/users/{user_id}/tweets?exclude=retweets,replies&max_results=5&expansions=attachments.media_keys,author_id&tweet.fields=created_at,text&media.fields=url,preview_image_url&user.fields=profile_image_url"
        headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                tweet_data = await resp.json()
                tweet = tweet_data["data"][0]
                tweet["author"] = tweet_data["includes"]["users"][0]
                tweet["media"] = tweet_data["includes"].get("media", [])
                return tweet
