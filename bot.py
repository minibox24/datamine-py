from discord.ext import commands
from tortoise import Tortoise

import config

bot = commands.Bot(command_prefix="!")
bot.remove_command("help")
bot.load_extension("datamine")


@bot.event
async def on_ready():
    await Tortoise.init(db_url="sqlite://db.sqlite3", modules={"models": ["models"]})
    await Tortoise.generate_schemas()
    print("Ready")


bot.run(config.BOT_TOKEN)
