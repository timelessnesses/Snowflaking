import sys
import typing
from datetime import datetime, timedelta

sys.path.append("..")

import asyncpg
import discord
import pytz
from discord import app_commands
from discord.ext import commands, tasks


class Timezone_checker(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        if argument in pytz.all_timezones:
            return pytz.timezone(argument)
        elif argument.startswith("-") or argument.startswith("+"):
            if argument[1:].isdigit():
                return pytz.timezone(f"Etc/GMT{argument}")
        elif " " in argument:
            argument = argument.replace(" ", "_")
            return pytz.timezone(argument)
        else:
            raise commands.BadArgument("Invalid timezone")


async def timezone_autocomplete(interaction: discord.Interaction, current: str):
    timezones = pytz.all_timezones
    return [
        app_commands.Choice(name=timezone.replace("_", " ").title(), value=timezone)
        for timezone in timezones
        if timezone.startswith(current)
    ][:25]


class Christmas(commands.Cog):
    """
    Christmas group command
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db
        self.check_time.start()
        self.initialize_guilds.start()

    def format_time_to_string(self, time: timedelta):
        return f"{time.days} days, {time.seconds // 3600} hours, {time.seconds // 60 % 60} minutes, {time.seconds % 60} seconds"

    @property
    def display_emoji(self):
        return "🎄"

    @tasks.loop(minutes=5)
    async def initialize_guilds(self):
        await self.bot.wait_until_ready()
        guilds = await self.db.fetch("SELECT guild_id FROM christmas_config")
        guilds = [x["guild_id"] for x in guilds]
        print(guilds)
        for guild in self.bot.guilds:
            if not guild.id in guilds:
                print("not exists")
                await self.db.execute(
                    "INSERT INTO christmas_config (guild_id) VALUES ($1)", guild.id
                )
                print("should exists")

    @tasks.loop(minutes=5)
    async def check_time(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        for guild in self.bot.guilds:
            guild: discord.Guild  # mf type hinting
            db_guild = await self.db.fetch(
                "SELECT * FROM christmas_config WHERE guild_id = $1", guild.id
            )
            print([x["guild_id"] for x in db_guild])
            if guild.id not in [x["guild_id"] for x in db_guild]:
                continue
            try:
                reminder_message = (
                    await self.db.fetch(
                        "SELECT * FROM christmas_reminder_message WHERE guild_id = $1",
                        guild.id,
                    )
                )[0]
            except IndexError:
                continue # no reminder message so nothing to do also this also means no channel id
            reminder_message = await guild.get_channel(
                reminder_message["channel_id"]
            ).fetch_message(reminder_message["message_id"])
            christmas_message = (
                await self.db.fetch(
                    "SELECT * FROM christmas_message WHERE guild_id = $1", guild.id
                )
            )[0]
            christmas_message = guild.get_channel(christmas_message["channel_id"])
            try:
                current_timezone = pytz.timezone(db_guild["timezone"].title())
            except pytz.exceptions.UnknownTimeZoneError:
                current_timezone = pytz.timezone("UTC")
            current_time = now.astimezone(current_timezone)
            christmas_time = datetime(
                current_time.year, 12, 25, 0, 0, 0, 0, current_timezone
            )
            estimated_left = christmas_time - current_time
            if estimated_left.total_seconds() in range(
                0, 86400 * 2
            ):  # Christmas is here and it lasts for 2 days after that
                channel = guild.get_channel(db_guild["annouce_channel_id"])
                j = await channel.send(
                    f"{(guild.get_role(christmas_message['ping_role_id']).mention if christmas_message['ping_role_id'] else '@everyone')}",
                    embed=discord.Embed(
                        title=f"{christmas_message['message_format'] if christmas_message['message_format'] else 'Happy Christmas day! 🎉'}",
                        description=f"{christmas_message['body_message_format'].format(year=christmas_time.year) if christmas_message['body_message_format'] else f'Happy Christmas! I hope you have a great life ahead!'}",
                        color=discord.Color.green(),
                    ),
                )
                await self.db.execute(
                    "UPDATE christmas_message(id) VALUES ($1) WHERE guild_id = $2",
                    j.id,
                    guild.id,
                )
            else:                                                                                                                                                                                                                                                                                                                                                                                                            
                # delete annouced message then count the time left
                try:
                    await christmas_message.get_partial_message(
                        christmas_message["message_id"]
                    ).delete()
                except:
                    pass
                await reminder_message.edit(
                    embed=(
                        discord.Embed(
                            title="Christmas is coming!",
                            description=f"{self.format_time_to_string(estimated_left)} left until Christmas!",
                            color=discord.Color.green(),
                        )
                    ).set_footer(
                        text=f"This message is controlled by timezone that's christmas_configured by the owner: {current_timezone.zone}"
                    )
                )

    @commands.hybrid_group()
    async def christmas_config(self, ctx: commands.Context):
        """
        Christmas group command
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @christmas_config.command()
    async def title_christmas(self, ctx: commands.Context, *, title: str):
        """
        Set Christmas title
        """
        await self.db.execute(
            "UPDATE christmas_message SET message_format = $1 WHERE guild_id = $2",
            title,
            ctx.guild.id,
        )
        await ctx.send(
            embed=discord.Embed(
                title="Title for Christmas annoucement is set!",
                color=discord.Color.green(),
            )
        )

    @christmas_config.command()
    async def annouce_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """
        Set a channel for update time and annouce Christmas
        """

        await self.db.execute(
            "UPDATE christmas_config SET annouce_channel_id = $1 WHERE guild_id = $2",
            channel.id,
            ctx.guild.id,
        )
        await ctx.send(
            embed=discord.Embed(
                title="Annouce channel is set!",
                color=discord.Color.green(),
            )
        )
        now = datetime.now()
        db_guild = (
            await self.db.fetch(
                "SELECT * FROM christmas_config WHERE guild_id = $1", ctx.guild.id
            )
        )[0]
        print(db_guild)
        try:
            current_timezone = pytz.timezone(db_guild["timezone"].title())
        except pytz.exceptions.UnknownTimeZoneError:
            current_timezone = pytz.timezone("UTC")
        current_time = now.astimezone(current_timezone)
        print(current_time)
        christmas_time = datetime(
            current_time.year, 12, 25, 0, 0, 0, 0, current_timezone
        )
        print(christmas_time)
        estimated_left = christmas_time - current_time

        a = await channel.send(
            embed=(
                discord.Embed(
                    title="Christmas is coming!",
                    description=f"{self.format_time_to_string(estimated_left)} left until Christmas!",
                    color=discord.Color.green(),
                )
            ).set_footer(
                text=f"This message is controlled by timezone that's christmas_configured by the owner: {current_timezone.zone}"
            )
        )
        await self.db.execute(
            "UPDATE reminder_message(message_id, channel_id, guild_id) VALUES ($1, $2, $3)",
            a.id,
            channel.id,
            ctx.guild.id,
        )

    @christmas_config.command()
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def timezone(self, ctx: commands.Context, timezone: Timezone_checker):
        """
        Set timezone for Christmas
        Note:
        - You can use autocomplete to get timezone
        - You can use UTC as default timezone
        - You can use UTC offset to set timezone (+7, -7)
        """
        timezone: typing.Union[pytz._UTCclass, pytz.StaticTzInfo, pytz.DstTzInfo]
        await self.db.execute(
            "UPDATE christmas_config SET timezone = $1 WHERE guild_id = $2",
            timezone.zone,
            ctx.guild.id,
        )
        await ctx.send(
            embed=discord.Embed(
                title="Timezone is set!",
                color=discord.Color.green(),
            )
        )

    @christmas_config.command()
    async def ping_role(self, ctx: commands.Context, role: discord.Role = None):
        """
        Set a role for ping when Christmas is coming
        """
        if not role:
            role = [x for x in ctx.guild.roles if x.name == "@everyone"][0]
        await self.db.execute(
            "UPDATE christmas_message SET ping_role_id = $1 WHERE guild_id = $2",
            role.id,
            ctx.guild.id,
        )
        await ctx.send(
            embed=discord.Embed(
                title="Ping role is set!",
                color=discord.Color.green(),
            )
        )


async def setup(bot: commands.Bot) -> typing.NoReturn:
    await bot.add_cog(Christmas(bot))
