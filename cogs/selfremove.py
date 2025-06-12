import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class SelfRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Self Remove cog loaded")

    @app_commands.command(
        name="remove",
        description="Remove yourself from the leaderboard. WARNING: This is irreversible, points will be reset to 0",
    )
    @app_commands.describe(confirmation="type CONFIRM to remove yourself")
    @track_queries
    @maintenance_check()
    async def selfremove(self, interaction: discord.Interaction, confirmation: str):
        await interaction.response.defer()

        if confirmation != "CONFIRM":
            await interaction.followup.send("Removal cancelled.")
            return
        discord_user = interaction.user.name
        if not dbfuncs.check_discord_user(discord_user):
            out = f"Discord user {discord_user} not registered"
            await interaction.followup.send(out)
            return

        dbfuncs.remove_user(interaction.user.id)
        await interaction.followup.send(
            f"Removed {discord_user} from leaderboard and database."
        )


async def setup(bot):
    await bot.add_cog(SelfRemove(bot))
