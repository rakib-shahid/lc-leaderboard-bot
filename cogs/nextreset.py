import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
import datetime
import traceback
import time
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class NextReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Next Reset cog loaded")

    @app_commands.command(
        name="nextreset",
        description="Check when the next leaderboard reset is.",
    )
    @track_queries
    @maintenance_check()
    async def nextreset(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(title=f"Next Reset", timestamp=datetime.datetime.now())
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        reset_info = dbfuncs.get_last_reset()
        description = ''
        if reset_info:
            reset_info = reset_info[0]
            try:
                last_reset, reset_interval = reset_info
                next_reset = last_reset + datetime.timedelta(days=reset_interval)
                # convert next_reset to a unix timestamp
                next_reset_ts = time.mktime(next_reset.timetuple())
                last_rest_ts = time.mktime(last_reset.timetuple())
                # print(next_reset_ts)
                # print(int(next_reset_ts))
                # print(last_rest_ts)
                # print(int(last_rest_ts))
                description += "Last Reset: <t:{}:R>\n".format(int(last_rest_ts))
                description += "Next Reset: <t:{}:R>\n".format(int(next_reset_ts))
                
                
                embed.description = description
            except Exception as e:
                traceback.print_exc()
                embed.description = "An error occurred while getting reset information"
                embed.set_image(url="https://media1.tenor.com/m/lxJgp-a8MrgAAAAd/laeppa-vika-half-life-alyx.gif")
                
        else:
            embed.add_field(name="Error", value="Could not get reset information", inline=False)

        await interaction.followup.send(
            embed = embed
        )


async def setup(bot):
    await bot.add_cog(NextReset(bot))
