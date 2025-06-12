import typing
import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class AdminPoints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin Points cog loaded")

    @app_commands.command(
        name="zpoints", description="Add points to a user (ADMIN ONLY)"
    )
    @app_commands.describe(discord_user="discord user to add points")
    @app_commands.describe(leetcode_user="leetcode user to add points")
    @app_commands.describe(points="points to add")
    @track_queries
    @maintenance_check()
    async def adminpoints(
        self,
        interaction: discord.Interaction,
        discord_user: typing.Optional[str],
        leetcode_user: typing.Optional[str],
        points: int,
    ):
        await interaction.response.defer()
        admins = dbfuncs.get_admins()
        admins = set([admin[0] for admin in admins])
        if interaction.user.id in admins:
            if not discord_user and not leetcode_user:
                await interaction.followup.send(
                    "Provide a valid user (leetcode or discord)"
                )
                return
            if discord_user:
                if not dbfuncs.check_discord_user(discord_user):
                    out = f"Discord user {discord_user} not registered"
                    await interaction.followup.send(out)
                    return
                dbfuncs.add_points(discord_user, None, points)
                await interaction.followup.send(
                    f"Added {points} points to {discord_user} by discord user"
                )
            else:
                if not dbfuncs.check_leetcode_user(leetcode_user):
                    out = f"User {leetcode_user} not registered"
                    await interaction.followup.send(out)
                    return
                dbfuncs.add_points(None, leetcode_user, points)
                await interaction.followup.send(
                    f"Added {points} points to {leetcode_user} by leetcode user"
                )

        else:
            await interaction.followup.send("You are not an admin")


async def setup(bot):
    await bot.add_cog(AdminPoints(bot))
