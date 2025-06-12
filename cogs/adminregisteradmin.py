import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class AdminRegisterAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin Register new Admin cog loaded")

    @app_commands.command(
        name="zregisteradmin", description="Register a new admin (ADMIN ONLY)"
    )
    @app_commands.describe(discord_id="discord ID to register")
    @track_queries
    @maintenance_check()
    async def adminregisteradmin(
        self, interaction: discord.Interaction, discord_id: str
    ):
        await interaction.response.defer()
        discord_id = int(discord_id)
        admins = dbfuncs.get_admins()
        admins = set([admin[0] for admin in admins])
        if interaction.user.id in admins:
            # insert discord_id to admin table
            if dbfuncs.add_admin(discord_id):
                await interaction.followup.send(f"Registered {discord_id} as new admin")
            else:
                await interaction.followup.send(
                    f"Failed to register {discord_id} as new admin"
                )

        else:
            await interaction.followup.send("You are not an admin")


async def setup(bot):
    await bot.add_cog(AdminRegisterAdmin(bot))
