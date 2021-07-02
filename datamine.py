from discord.ext import commands


class Datamine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Datamine(bot))
