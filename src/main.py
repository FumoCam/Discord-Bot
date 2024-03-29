import os
from traceback import format_exc

import discord
from dotenv import load_dotenv

import utils
from cogs.fun import Fun as FunCog
from cogs.invite_check import InviteCheck as InviteCheckCog
from cogs.leave_message import LeaveMessage as LeaveMessageCog
from cogs.media_rate import MediaRate as MediaRateCog
from cogs.message_logging import MessageLogging as MessageLoggingCog
from cogs.suggestions import Suggestions as SuggestionsCog
from cogs.voice_channel_hoist import VoiceChannelHoist as VoiceChannelHoistCog

global bot
bot = utils.BotClass()


@bot.client.event
async def on_error(event, args="", kwargs=""):
    error = format_exc()
    utils.log_error("[Uncaught Error] " + error)


@bot.client.event
async def on_message(message: discord.Message):
    if not bot.ready:  # Handle race condition
        return

    # Basic non-overridable shutdown command
    if message.author.id == bot.CFG[
        "discord_bot_owner_id"
    ] and message.content.lower().startswith("/off"):
        try:
            await message.delete()
        finally:
            await bot.client.close()
            await bot.client.logout()
            return

    # For safety, strip sensitive pings
    message.content = message.content.replace("@everyone", "@ everyone")
    message.content = message.content.replace("@here", "@ here")

    # Process commands
    await bot.client.process_commands(message)


async def post_init():
    await bot.client.add_cog(InviteCheckCog(bot))
    await bot.client.add_cog(MessageLoggingCog(bot))
    await bot.client.add_cog(MediaRateCog(bot))
    await bot.client.add_cog(LeaveMessageCog(bot))
    await bot.client.add_cog(SuggestionsCog(bot))
    await bot.client.add_cog(VoiceChannelHoistCog(bot))
    await bot.client.add_cog(FunCog(bot))


async def config():
    bot.guild = bot.client.get_guild(bot.CFG["discord_guild_id"])

    # Instantiate channel objects
    bot.channels = {}
    for channel_name in bot.CFG["discord_channel_ids"]:
        channel_id = bot.CFG["discord_channel_ids"][channel_name]
        bot.channels[channel_name] = bot.guild.get_channel(channel_id)

    # Instantiate role objects
    bot.roles = {}
    for role_name in bot.CFG["discord_role_ids"]:
        role_id = bot.CFG["discord_role_ids"][role_name]
        bot.roles[role_name] = bot.guild.get_role(role_id)


@bot.client.event
async def on_ready():
    try:
        utils.do_log(f"Bot name: {bot.client.user.name}")
        utils.do_log(f"Bot ID: {bot.client.user.id}")
        # await bot.client.change_presence(
        #     activity=discord.Game(name="/help", type=0)
        # )
        await config()

        utils.do_log("Ready\n\n")
        bot.ready = True
        await post_init()
    except Exception:
        utils.log_error(f"\n\n\nCRITICAL ERROR: FAILURE TO INITIALIZE{format_exc()}")
        await bot.client.close()
        await bot.client.logout()
        raise Exception("CRITICAL ERROR: FAILURE TO INITIALIZE")


def main():
    global bot
    bot.ready = False
    utils.do_log("Loading Config")

    bot = utils.load_config_to_bot(bot)  # Load a json to the bot class
    load_dotenv(verbose=True)

    # Merge any env vars with config vars, and make variables easily accessible
    utils.do_log(f"Discord token: {utils.censor_text(os.getenv('DISCORD_TOKEN'))}")

    # DiscordPy tasks
    utils.do_log("Loaded Config")
    utils.do_log("Logging in")
    bot.client.run(os.getenv("DISCORD_TOKEN"))
    utils.do_log("Logging out")


if __name__ == "__main__":
    main()
