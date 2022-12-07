import random
import time

import discord
from discord.ext import commands

from .utils import imagegen

import asyncpg

class Levelling(commands.Cog):
    """
    Levelling group command
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = self.bot.db
        self.ratelimit = {}

    async def cog_before_invoke(self, ctx: commands.Context):
        await ctx.defer()

    @property
    def display_emoji(self):
        return "📈"

    @commands.hybrid_group()
    async def level(self, ctx: commands.Context, member: discord.Member = None):
        """
        Level group command
        """
        if member is None:
            member = ctx.author
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.level.get_command("info"), member=member)

    @level.command(name="info", aliases=["lvl"])
    async def info(self, ctx: commands.Context, member: discord.Member = None):
        """
        Show your information inside this guild!
        """
        # TODO: sort members in guild :pog:
        if member is None:
            member = ctx.author
        if member.bot:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Bots don't have levels.",
                    color=discord.Color.red(),
                )
            )
        try:
            str(member.guild_avatar.url)
        except AttributeError:
            str(member.avatar.url)

        level = (
            await self.db.fetch(
                "SELECT * FROM user_ WHERE user_id = $1 AND guild_id = $2",
                member.id,
                member.guild.id,
            )
        )[0]
        try:
            bg_path = (
                await self.db.fetch(
                    "SELECT background FROM levels_background WHERE guild_id = $1",
                    member.guild.id,
                )
            )[0]["background"]
        except IndexError:
            bg_path = None
        users = await self.db.fetch(
            "SELECT * FROM user_ WHERE guild_id = $1", member.guild.id
        )
        users = sorted(users, key=lambda x: x["experience"], reverse=True)
        position = 1
        for user in users:
            if user["user_id"] == member.id:
                break
            position += 1
        level["experience"]
        color = tuple(
            int(x)
            for x in (
                await self.db.fetch(
                    "SELECT color FROM font_colors WHERE guild_id = $1",
                    ctx.guild.id,
                )
            )[0]["color"].split(",")
        )
        return await ctx.send(
            file=await imagegen.generate_profile(
                bg_path,
                str(ctx.author.avatar.url),
                level["experience"] // 100,
                level["experience"] % 100,
                100,
                position,
                str(ctx.author),
                str(ctx.author.status),
            ),
        )

    # TODO: make a on_message event that listen and keep track of the member's message then increase the exp
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        try:
            assert time.time() - self.ratelimit[message.author.id]["time"] >= 2
        except KeyError:
            self.ratelimit[message.author.id] = {"time": time.time()}
        except AssertionError:
            return
        self.ratelimit[message.author.id]["time"] = time.time()
        exp = (
            await self.db.fetch(
                "SELECT experience FROM user_ WHERE user_id = $1 AND guild_id = $2",
                message.author.id,
                message.guild.id,
            )
        )[0]["experience"]
        level = exp // 100
        if level <= 50:
            exp += random.randint(1, 10)
        elif level <= 100:
            exp += random.randint(1, 8)
        elif level <= 150:
            exp += random.randint(1, 6)
        elif level <= 200:
            exp += random.randint(1, 4)
        elif level <= 400:
            exp += random.randint(1, 3)
        else:
            exp += random.randint(1, 2)
        try:
            disable_level_user = (
                await self.db.fetch(
                    "SELECT send_level_up_message FROM user_config WHERE user_id = $1",
                    message.author.id,
                )
            )[0]["send_level_up_message"]
        except (IndexError, KeyError):
            disable_level_user = False
        try:
            disable_level_guild_channel = await self.db.fetch(
                "SELECT * FROM prevent_channel_send WHERE guild_id = $1 AND channel_id = $2",
                message.guild.id,
                message.channel.id,
            )
            assert disable_level_guild_channel is not None
            disable_level_guild_channel[0]
            disable_level_guild_channel[0]["channel_id"]
        except (AssertionError, IndexError, KeyError):
            disable_level_guild_channel = False
        if (
            (exp // 100) > (level)
            and (not disable_level_user)
            and (not disable_level_guild_channel)
        ):
            bg_path = (
                await self.db.fetch(
                    "SELECT background FROM levels_background WHERE guild_id = $1",
                    message.guild.id,
                )
            )[0]["background"]
            users = await self.db.fetch(
                "SELECT * FROM user_ WHERE guild_id = $1", message.guild.id
            )
            users = sorted(users, key=lambda x: x["experience"], reverse=True)
            position = 1
            for user in users:
                if user["user_id"] == message.author.id:
                    break
                position += 1
            left_over = exp % 100
            await message.channel.send(
                f"Congratulations {message.author.mention}! You have leveled up to level {exp // 100 + 1}!",
                file=await imagegen.generate_profile(
                    bg_path,
                    str(message.author.avatar.url),
                    exp // 100,
                    left_over,
                    100,
                    position,
                    str(message.author),
                    str(message.author.status),
                ),
            )
        await self.db.execute(
            "UPDATE user_ SET experience = $1 WHERE user_id = $2 AND guild_id = $3",
            exp,
            message.author.id,
            message.guild.id,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Levelling(bot))
