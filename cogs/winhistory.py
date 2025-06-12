import discord
from discord.ext import commands
from discord import app_commands
import requests
import datetime
import lib.dbfuncs as dbfuncs
import traceback
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class WinHistory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_mobile_view = False

    @commands.Cog.listener()
    async def on_ready(self):
        print("Win History cog loaded")

    @app_commands.command(
        name="winhistory",
        description="View the latest 10 winners.",
    )
    @track_queries
    @maintenance_check()
    async def winhistory(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            data = dbfuncs.get_win_history()
            # url = 'https://server.rakibshahid.com/leaderboard'
            # response = requests.get(url)
            # data = response.json()
            if data is None:
                embed = discord.Embed(title="No Winners Yet", description="No winners have been recorded yet.", timestamp=datetime.datetime.now())
                await interaction.followup.send(embed=embed)
            else:
                embed = self.create_detailed_embed(data, interaction.user.name)

                view = discord.ui.View()
                toggle_button = discord.ui.Button(label="Toggle View", style=discord.ButtonStyle.primary)
                view.add_item(toggle_button)

                message = await interaction.followup.send(embed=embed, view=view)

                async def button_callback(interaction: discord.Interaction):
                    self.is_mobile_view = not self.is_mobile_view
                    new_embed = self.create_mobile_embed(data, interaction.user.name) if self.is_mobile_view else self.create_detailed_embed(data, interaction.user.name)
                    await interaction.response.edit_message(embed=new_embed)

                toggle_button.callback = button_callback
            
        except Exception as e:
            traceback.print_exc()
            print(e)

    def create_mobile_embed(self, data, user_name):
        description = ''
        leetcode_emoji = self.bot.get_emoji(1290903612351844464)
        discord_emoji = self.bot.get_emoji(1290903900169310248)
        try:
            for i in range(min(10,len(data))):
                cleaned_discord_username = str(data[i][0]).replace('_', '\\_').replace('*', '\\*')
                cleaned_leetcode_username = str(data[i][1]).replace('_', '\\_').replace('*', '\\*')
                description += f"{i + 1}. {discord_emoji}{cleaned_discord_username} ({leetcode_emoji}{cleaned_leetcode_username}) - <t:{str(data[i][2])[:-2]}:R> \n"
        except:
            traceback.print_exc()
        embed = discord.Embed(title=f"Latest Winners - Mobile View", description=description, timestamp=datetime.datetime.now())
        embed.set_footer(text=f"Requested by {user_name}")
        return embed

    def create_detailed_embed(self, data, user_name):
        embed = discord.Embed(title=f"Latest Winners", timestamp=datetime.datetime.utcnow())
        leetcode_emoji = self.bot.get_emoji(1290903612351844464)
        discord_emoji = self.bot.get_emoji(1290903900169310248)
        discord_users = []
        leetcode_users = []
        wins = []
        for i in range(min(len(data),10)):
            cleaned_discord_username = str(data[i][0]).replace('_', '\\_').replace('*', '\\*')
            cleaned_leetcode_username = str(data[i][1]).replace('_', '\\_').replace('*', '\\*')
            leetcode_users.append(cleaned_leetcode_username)
            discord_users.append(cleaned_discord_username)
            wins.append(f"<t:{str(data[i][2])[:-2]}:R>")
        embed.add_field(name=f"{discord_emoji} Discord User", value="\n".join(discord_users), inline=True)
        embed.add_field(name=f"{leetcode_emoji} Leetcode User", value="\n".join(leetcode_users), inline=True)
        embed.add_field(name="Time Won", value="\n".join(map(str, wins)), inline = True)
        embed.set_footer(text=f"Requested by {user_name}")
        return embed

async def setup(bot):
    await bot.add_cog(WinHistory(bot))
