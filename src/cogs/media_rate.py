from asyncio import sleep as async_sleep
from mimetypes import guess_type
from re import compile as regex_compile

import discord
from aiohttp import ClientSession as AioClientSession
from discord.ext import commands  # type: ignore

from utils import BotClass


class MediaRate(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot
        self.url_regex = regex_compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )

        media_rate_channels = self.bot.CFG.get("media_rate_channels", [])

        if not media_rate_channels:
            print(
                "['media_rate_channels' channels not set, disabling media rating subroutine]"
            )
            return

        self.media_rate_channel_ids = []
        for channel_name in media_rate_channels:
            if channel_name not in self.bot.channels:
                print(
                    f"['{channel_name}' not found, disabling media rating subroutine]"
                )
                return
            self.media_rate_channel_ids.append(self.bot.channels[channel_name].id)

        self.downvote_emoji = self.bot.CFG.get("media_rate_downvote", "👎")
        self.upvote_emoji = self.bot.CFG.get("media_rate_upvote", "👍")
        self.rate_any_url = self.bot.CFG.get("media_rate_any_url", False)

    async def message_has_media(self, message: discord.Message):
        if len(message.attachments) > 0:
            # Message has an attachment, obviously media
            return True

        for embed in message.embeds:
            for nullable_property in [embed.video, embed.thumbnail, embed.image]:
                if nullable_property != discord.Embed.Empty:
                    # Embed has a media-like property that could be null, but isn't
                    return True

        message_urls = self.url_regex.findall(message.content)
        if self.rate_any_url and len(message_urls) > 0:
            # If we've set the setting, treat any found URLs as media
            return True

        for url in message_urls:
            mime_type, _ = guess_type(url)
            if (mime_type) and mime_type.startswith(("image", "video", "audio")):
                # If the url ends with a file extension that is media-like
                return True

            async with AioClientSession() as session:
                async with session.get(url) as response:
                    try:
                        # If the website itself contains common meta tags used for embedding media
                        body = await response.text()
                        if (
                            "og:image" in body
                            or "og:video" in body
                            or "og:audio" in body
                        ):
                            return True
                    except Exception:  # nosec
                        continue

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id not in self.media_rate_channel_ids:
            return
        if await self.message_has_media(message):
            # Sleep required, sometimes goes too fast and emoji shows to the poster (but fine for everyone else)
            await async_sleep(0.25)
            await message.add_reaction(self.upvote_emoji)
            await async_sleep(0.25)
            await message.add_reaction(self.downvote_emoji)
