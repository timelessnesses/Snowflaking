import enum
import io

import aiohttp
import asyncpg
import discord
import yarl
from discord.ext import commands
from PIL import Image, ImageDraw


class Things(enum.Enum):
    background = "background"
    rgb = "rgb"
    roles_level = "roles_level"


class URLConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        try:
            assert yarl.URL(argument).scheme in ["http", "https"], "Invalid URL"
            return argument
        except AssertionError as e:
            raise commands.BadArgument(e)


class Configure(commands.Cog,name="Level Configure"):
    """
    Configure the bot you intended to do in your server!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = self.bot.db

    @property
    def display_emoji(self):
        return "🔨"

    @commands.hybrid_group()
    async def config(self, ctx: commands.Context):
        if ctx.invoked_with == "config":
            await ctx.send_help()

    async def cog_before_invoke(self, ctx: commands.Context):
        await ctx.defer()
        if ctx.invoked_subcommand == "send_level_up":
            pass
        elif (
            not ctx.author.guild_permissions.administrator
            or not ctx.author.guild_permissions.manage_guild
        ):
            raise commands.MissingPermissions(["administrator", "manage_guild"])

    @config.command()
    async def add_roles_level(
        self, ctx: commands.Context, level: int, role: discord.Role
    ):
        """
        Add a role to the list of roles that can be assigned to a user based on their level.
        """
        try:
            await self.db.execute(
                """INSERT INTO roles_level (guild_id, level_, role_id) VALUES ($1, $2, $3)""",
                ctx.guild.id,
                level,
                role.id,
            )
        except asyncpg.UniqueViolationError:
            await self.db.execute(
                """UPDATE  roles_level SET role_id = $3 WHERE guild_id = $1 AND level_ = $2""",
                ctx.guild.id,
                level,
                role.id,
            )
        await ctx.send(
            embed=discord.Embed(
                title="Success!",
                description="Added role {} to level {}".format(role.name, level),
                color=discord.Color.green(),
            )
        )

    @config.command()
    async def change_bg_level(self, ctx: commands.Context, path: URLConverter = None):
        """
        Change the background for the level. (Supports attachments)
        If your image is too big, it will be cropped to fit.
        """
        if path is None:
            try:
                path = ctx.message.attachments[0].url
            except IndexError:
                await ctx.send(
                    embed=discord.Embed(
                        title="Error!",
                        description="No image provided!",
                        color=discord.Color.red(),
                    )
                )
                return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(path) as resp:
                    content = await resp.read()

                    end = resp.headers["Content-Type"].split("/")[1]
                    assert resp.status == 200, "Invalid image"
                    assert resp.headers["Content-Type"].startswith(
                        "image"
                    ), "Invalid image"
                    assert resp.headers["Content-Type"].endswith("png") or resp.headers[
                        "Content-Type"
                    ].endswith("jpg"), "Invalid image"
        except AssertionError:
            await ctx.send(
                embed=discord.Embed(
                    title="Error!",
                    description="Invalid image!",
                    color=discord.Color.red(),
                ),
                file=discord.File(io.BytesIO(content), filename=f"stuff.{end}"),
            )
            return
        await self.db.execute(
            "UPDATE levels_background SET background = $2 WHERE guild_id = $1",
            ctx.guild.id,
            path,
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success!",
                description="Changed background to",
                color=discord.Color.green(),
            ),
            file=discord.File(io.BytesIO(content), filename=f"stuff.{end}"),
        )

    @config.command()
    async def change_font_color(
        self, ctx: commands.Context, r: int = None, g: int = None, b: int = None
    ):
        rgb = (r, g, b)
        for x in rgb:
            try:
                assert x is not None and not x > 255

            except AssertionError:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error!",
                        description="Your RGB value is either wrong or left some of color value to none!",
                    )
                )
        await self.db.execute(
            "UPDATE  font_colors SET color = $1 WHERE guild_id = $2",
            ctx.guild.id,
            ",".join(rgb),
        )
        file = io.BytesIO()
        image = Image.new("RGBA", (100, 100))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 100, 100), fill=(rgb))
        image.save(file, "png")
        file.seek(0)
        await ctx.send(
            embed=discord.Embed(title="Here's your color result!"),
            file=discord.File(file),
        )

    @config.command()
    async def reset(self, ctx: commands.Context, thing: Things, level: int = None):
        """
        Reset the configuration of the bot.
        """
        if thing == Things.background:
            await self.db.execute(
                "UPDATE levels_background SET background = $1 WHERE guild_id = $2",
                None,
                ctx.guild.id,
            )
        elif thing == Things.rgb:
            await self.db.execute(
                "UPDATE font_colors SET color = $1 WHERE guild_id = $2",
                None,
                ctx.guild.id,
            )
        elif thing == Things.roles_level:
            await self.db.execute(
                "DELETE FROM roles_level WHERE level_ = $1 AND guild_id = $2",
                level,
                ctx.guild.id,
            )
        await ctx.send(
            embed=discord.Embed(
                title="Success!",
                description="Reseted {}".format(thing.value),
                color=discord.Color.green(),
            )
        )

    @config.command()
    async def send_level_up(self, ctx: commands.Context, enable: bool = None):
        """
        Enable or disable the level up message.
        """
        if enable is None:
            enable = not (
                await self.db.fetch(
                    "SELECT send_level_up_message FROM user_config WHERE user_id = $1",
                    ctx.author.id,
                )
            )[0]["send_level_up_message"]
        await self.db.execute(
            "UPDATE user_config SET send_level_up_message = $1 WHERE user_id = $2",
            enable,
            ctx.author.id,
        )
        await ctx.send(
            embed=discord.Embed(
                title="Success!",
                description="Changed level up message to {}".format(
                    "enabled" if enable else "disabled"
                ),
                color=discord.Color.green(),
            )
        )

    @config.command()
    async def prevent_channel_send(
        self, ctx: commands.Context, channel: discord.TextChannel, enable: bool
    ):
        """
        Ban list that bot shouldn't send message to
        """
        if enable:
            exists = await self.db.fetch(
                "SELECT * FROM prevent_channel_send WHERE guild_id = $1 AND channel_id = $2",
                ctx.guild.id,
                channel.id,
            )
            if not exists:
                await self.db.execute(
                    "INSERT INTO prevent_channel_send VALUES ($1, $2)",
                    ctx.guild.id,
                    channel.id,
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        title="Error!",
                        description="This channel is already in the ban list!",
                        color=discord.Color.red(),
                    )
                )
                return
        else:
            await self.db.execute(
                "DELETE FROM prevent_channel_send WHERE guild_id = $1 AND channel_id = $2",
                ctx.guild.id,
                channel.id,
            )
        await ctx.send(
            embed=discord.Embed(
                title="Success!",
                description="Changed prevent channel {} send to {}".format(
                    channel.mention, "enabled" if enable else "disabled"
                ),
                color=discord.Color.green(),
            )
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Configure(bot))
