import copy

import asyncpg
import discord
from discord.ext import commands


class Leaderboard(commands.Cog):
    """
    Get a ranking of the top 10 users/servers!
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db: asyncpg.pool.Pool = bot.db

    @property
    def display_emoji(self) -> str:
        return "📊"

    def prefix(self, n: int):
        return str(n) + (
            "th"
            if 4 <= n % 100 <= 20
            else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        )

    async def cog_before_invoke(self, ctx: commands.Context):
        await ctx.defer()

    @commands.hybrid_group()
    async def leaderboard(self, ctx: commands.Context) -> None:
        """
        Leaderboard command group
        """
        await ctx.invoke(self.leaderboard.get_command("users"))

    @leaderboard.command(name="users")
    async def users(self, ctx: commands.Context) -> None:
        """
        Get top 10 users ranked by highest exp!
        """
        users = await self.db.fetch(
            "SELECT * FROM user_ WHERE guild_id = $1 ORDER BY experience DESC LIMIT 10",
            ctx.guild.id,
        )
        if not users:
            await ctx.send(
                embed=discord.Embed(
                    title="Leaderboard",
                    description="No users found.",
                    color=discord.Color.red(),
                )
            )
            return
        embed = discord.Embed(
            title="Leaderboard",
            description="Top 10 users ranked by highest exp!",
            color=discord.Color.blue(),
        )
        e = None
        for i, user in enumerate(users):
            embed.add_field(
                name=f"{self.prefix(i + 1)} {await self.bot.fetch_user(user['user_id'])}",
                value=f"{user['experience'] % 100} exp {user['experience'] // 100} level",
                inline=False,
            )
            if user["user_id"] == ctx.author.id:
                e = copy.copy(i)

        embed.set_footer(text=f"You are {self.prefix(e + 1)} in the leaderboard.")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))
