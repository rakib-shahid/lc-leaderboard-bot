import typing
import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class AdminReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin Points cog loaded")

    @app_commands.command(
        name="zreset", description="Select a reset interval for the leaderboard (ADMIN ONLY)"
    )
    @app_commands.describe(interval="Choose a reset interval")
    @app_commands.describe(confirmation="type CONFIRM to confirm a RESET interval change")
    @app_commands.choices(
        interval=[
            app_commands.Choice(name="Weekly", value="7"),
            app_commands.Choice(name="Biweekly", value="14"),
            app_commands.Choice(name="Monthly", value="30"),
        ]
    )
    @track_queries
    @maintenance_check()
    async def adminreset(
        self,
        interaction: discord.Interaction,
        confirmation: typing.Optional[str],
        interval: typing.Optional[app_commands.Choice[str]],
    ):
        await interaction.response.defer()
        admins = dbfuncs.get_admins()
        admins = set([admin[0] for admin in admins])
        if interaction.user.id in admins:
            if confirmation != "CONFIRM":
                await interaction.followup.send("No confirmation, reset cancelled")
                return
            # dbfuncs.CLEAR_ALL_POINTS(int(interval.value) if interval else None)
            await interaction.followup.send(
                f"Leaderboard will reset with the interval of {interval} days"
            )

        else:
            await interaction.followup.send("You are not an admin")


async def setup(bot):
    await bot.add_cog(AdminReset(bot))
