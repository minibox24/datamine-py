import discord
from discord.ext import commands, tasks
from tortoise import Tortoise
from tortoise.query_utils import Q

from config import GITHUB_TOKEN
from fetch import fetch
from models import *
import asyncio


class Paginator:
    def __init__(self, ctx, embeds):
        self.ctx = ctx
        self.bot = ctx.bot
        self.embeds = embeds
        self.page = 1

    async def start(self):
        data = {
            "embeds": [self.embeds[0].to_dict()],
            "components": [
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "style": 4,
                            "label": "이전",
                            "custom_id": "previous",
                            "disabled": True,
                        },
                        {
                            "type": 2,
                            "style": 2,
                            "label": f"1 / {len(self.embeds)}",
                            "custom_id": "info",
                            "disabled": True,
                        },
                        {"type": 2, "style": 3, "label": "다음", "custom_id": "next"},
                    ],
                }
            ],
        }

        message = await self.bot.http.request(
            discord.http.Route("POST", f"/channels/{self.ctx.channel.id}/messages"),
            json=data,
        )

        message_id = message["id"]

        try:
            while True:
                msg = await self.bot.wait_for(
                    "socket_response",
                    check=lambda m: m["t"] == "INTERACTION_CREATE"
                    and m["d"]["data"]["custom_id"] in ["next", "previous"]
                    and m["d"]["message"]["id"] == message_id,
                    timeout=120,
                )

                custom_id = msg["d"]["data"]["custom_id"]

                if custom_id == "next":
                    self.page += 1
                else:
                    self.page -= 1

                try:
                    data["embeds"] = [self.embeds[self.page - 1].to_dict()]
                except IndexError:
                    continue

                data["components"][0]["components"][1][
                    "label"
                ] = f"{self.page} / {len(self.embeds)}"

                data["components"][0]["components"][0]["disabled"] = self.page <= 1
                data["components"][0]["components"][2]["disabled"] = self.page >= len(
                    self.embeds
                )

                await self.bot.http.request(
                    discord.http.Route(
                        "PATCH",
                        f"/channels/{self.ctx.channel.id}/messages/{message_id}",
                    ),
                    json=data,
                )

                await self.bot.http.request(
                    discord.http.Route(
                        "POST",
                        "/interactions/{id}/{token}/callback",
                        id=msg["d"]["id"],
                        token=msg["d"]["token"],
                    ),
                    json={"type": 7},
                )
        except asyncio.TimeoutError:
            data["components"] = []
            await self.bot.http.request(
                discord.http.Route(
                    "PATCH", f"/channels/{self.ctx.channel.id}/messages/{message_id}"
                ),
                json=data,
            )


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

        for comment in await Comment.filter(sended=False).order_by("timestamp"):
            await self.send_update(comment)
            await Comment.filter(id=comment.id).update(sended=True)

    def make_message(self, comment):
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

        embed.set_footer(text="bot source: minibox24/datamine-py")

        if len(comment.images) > 0:
            embed.set_image(url=comment.images[0])

        return embed, comment.images[1:]

    async def send_update(self, comment):
        embed, images = self.make_message(comment)

        for ch in await UpdateChannel.all():
            channel = self.bot.get_channel(ch.id)

            await channel.send(embed=embed)
            if images:
                await channel.send("\n".join(images))

    @commands.command("종료")
    @commands.is_owner()
    async def exit_bot(self, ctx):
        await ctx.send("봇을 종료합니다.")
        await Tortoise.close_connections()
        await self.bot.close()

    @commands.group("구독")
    async def sub(self, ctx):
        if ctx.invoked_subcommand:
            return

        if not await UpdateChannel.exists(id=ctx.channel.id):
            await UpdateChannel.create(id=ctx.channel.id)
            await ctx.send("이 채널에 데이터마이닝 알림을 구독했습니다.")
        else:
            await ctx.send("이 채널은 이미 데이터마이닝 알림 구독중입니다.")

    @sub.command("취소")
    async def unsub(self, ctx):
        if await UpdateChannel.exists(id=ctx.channel.id):
            await UpdateChannel.filter(id=ctx.channel.id).delete()
            await ctx.send("이 채널의 데이터마이닝 알림 구독을 취소했습니다.")
        else:
            await ctx.send("이 채널은 데이터마이닝 알림 구독중이 아닙니다.")

    @commands.command("최신")
    async def latest(self, ctx):
        latest = list(await Comment.all().order_by("timestamp"))[-1]

        embed, images = self.make_message(latest)
        await ctx.send(embed=embed)
        if images:
            await ctx.send("\n".join(images))

    @commands.command("검색")
    async def search(self, ctx, *, query=None):
        if not query:
            return await ctx.send("검색어를 입력해주세요.")

        results = (
            await Comment.filter(
                Q(description__icontains=query) | Q(title__icontains=query)
            )
            .order_by("timestamp")
            .all()
        )

        if len(results) == 0:
            await ctx.send("검색결과가 없습니다.")
        else:
            embeds = list(map(lambda x: self.make_message(x)[0], results))
            paginator = Paginator(ctx, embeds)
            await paginator.start()


def setup(bot):
    bot.add_cog(Datamine(bot))
