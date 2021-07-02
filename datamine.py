from discord.ext import commands, tasks


class Datamine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handler.start()

    def cog_unload(self):
        return self.handler.cancel()

    @tasks.loop(minutes=10)
    async def handler(self):
        pass

    async def send_update(comment):
        pass


def setup(bot):
    bot.add_cog(Datamine(bot))
