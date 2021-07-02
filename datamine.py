from fetch import fetch
import discord
from discord.ext import commands, tasks
from tortoise import Tortoise
from config import GITHUB_TOKEN
from models import *


class Datamine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.handler.start()

    def cog_unload(self):
        return self.handler.cancel()

    @tasks.loop(minutes=10)
    async def handler(self):
        comments = await fetch(GITHUB_TOKEN)

        for comment in comments:
            if not await Comment.exists(id=comment["id"]):
                await Comment.create(sended=False, **comment)

        for comment in await Comment.all():
            if not comment.sended:
                await self.send_update(comment)
                await Comment.filter(id=comment.id).update(sended=True)

    async def send_update(self, comment):
        channels = [self.bot.get_channel(719187980518031460)]

        embed = discord.Embed()
        embed.color = discord.Color.blurple()
        embed.title = comment.title
        embed.description = (
            comment.description[:4000] + "..."
            if len(comment.description) > 4000
            else comment.description
        )
        embed.url = comment.url
        embed.timestamp = comment.timestamp

        embed.set_author(
            name=comment.user["username"],
            icon_url=comment.user["avatar_url"],
            url=comment.user["url"],
        )

        image_queue = []
        if len(comment.images) > 0:
            embed.set_image(url=comment.images[0])
            image_queue = comment.images[1:]

        for channel in channels:
            await channel.send(embed=embed)
            for image in image_queue:
                await channel.send(image)

    @commands.command("종료")
    @commands.is_owner()
    async def exit_bot(self, ctx):
        await ctx.send("봇을 종료합니다.")
        await Tortoise.close_connections()
        await self.bot.close()


def setup(bot):
    bot.add_cog(Datamine(bot))
