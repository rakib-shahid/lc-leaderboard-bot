import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class AdminRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin Remove cog loaded")

    @app_commands.command(name="zremove", description="Remove a user (ADMIN ONLY)")
    @app_commands.describe(discord_user="discord user to remove")
    @track_queries
    @maintenance_check()
    async def adminremove(self, interaction: discord.Interaction, discord_user: str):
        await interaction.response.defer()
        admins = dbfuncs.get_admins()
        admins = set([admin[0] for admin in admins])
        if interaction.user.id in admins:
            if not dbfuncs.check_discord_user(discord_user):
                out = f"Discord user {discord_user} not registered"
                await interaction.followup.send(out)
                return

            dbfuncs.remove_user(discord_user)
            await interaction.followup.send(
                f"Removed {discord_user} from leaderboard and database."
            )

        else:
            await interaction.followup.send("You are not an admin")


async def setup(bot):
    await bot.add_cog(AdminRemove(bot))
