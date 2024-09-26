import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs


class SelfRegister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Self Register cog loaded")

    @app_commands.command(
        name="register",
        description="Register yourself to the leaderboard.",
    )
    @app_commands.describe(leetcode_user="link your discord to this leetcode account")
    async def selfregister(self, interaction: discord.Interaction, leetcode_user: str):
        await interaction.response.defer()
        try:

            if dbfuncs.check_discord_user(interaction.user.name):
                out = f"Discord user {interaction.user.mention} already registered"
                lc_user = dbfuncs.get_leetcode_from_discord(interaction.user.name)
                if lc_user:
                    out += f" as {lc_user}"
                await interaction.followup.send(out)
                return

            if dbfuncs.check_leetcode_user(leetcode_user):
                out = f"User {leetcode_user} already registered"
                dc_user = dbfuncs.get_discord_from_leetcode(leetcode_user)
                if dc_user:
                    out += f" with Discord: {dc_user}"
                await interaction.followup.send(out)
                return

            dbfuncs.add_user(interaction.user.name, leetcode_user)
            await interaction.followup.send(
                f"Registered {interaction.user.name} as {leetcode_user}"
            )
        except Exception as e:
            print(e)


async def setup(bot):
    await bot.add_cog(SelfRegister(bot))
