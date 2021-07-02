from fetch import fetch
from discord.ext import commands
import config

bot = commands.Bot(command_prefix="!")


@bot.command("fetch")
async def fetch_(ctx):
    data = await fetch(config.GITHUB_TOKEN)
    for i in data:
        await ctx.send(data)


bot.run(config.BOT_TOKEN)
