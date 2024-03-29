from asyncio import sleep as async_sleep

import discord
from discord.ext import commands  # type: ignore

from utils import BotClass


class Fun(commands.Cog):
    def __init__(self, bot: BotClass):
        self.bot = bot
        self.morb_emoji = self.bot.CFG.get("morb_emoji", "🚩")

    async def morb_detector(self, message: discord.Message):
        # split_message = message.content.lower().split(" ")
        morb_indicators = ["morb"]
        for indicator in morb_indicators:
            if indicator in message.content.lower():
                await async_sleep(0.25)
                await message.add_reaction(self.morb_emoji)
                break

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.morb_detector(message)
