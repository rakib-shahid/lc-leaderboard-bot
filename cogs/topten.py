import discord
from discord.ext import commands
from discord import app_commands
import requests
import datetime
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check


class TopTen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_mobile_view = False

    @commands.Cog.listener()
    async def on_ready(self):
        print("Top 10 cog loaded")

    @app_commands.command(
        name="top10",
        description="View the top 10 users.",
    )
    @track_queries
    @maintenance_check()
    async def topten(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # update_query_count(interaction.user.id, interaction.user.name)
        try:
            url = "https://server.rakibshahid.com/leaderboard"
            response = requests.get(url)
            data = response.json()
            embed = self.create_detailed_embed(data, interaction.user.name)

            view = discord.ui.View()
            toggle_button = discord.ui.Button(
                label="Toggle View", style=discord.ButtonStyle.primary
            )
            view.add_item(toggle_button)

            message = await interaction.followup.send(embed=embed, view=view)

            async def button_callback(interaction: discord.Interaction):
                self.is_mobile_view = not self.is_mobile_view
                new_embed = (
                    self.create_mobile_embed(data, interaction.user.name)
                    if self.is_mobile_view
                    else self.create_detailed_embed(data, interaction.user.name)
                )
                await interaction.response.edit_message(embed=new_embed)

            toggle_button.callback = button_callback

        except Exception as e:
            print(e)

    def create_mobile_embed(self, data, user_name):
        description = "View full leaderboard at [codeforall.nyc](https://www.codeforall.nyc/leaderboard)\n"
        leetcode_emoji = self.bot.get_emoji(1290903612351844464)
        discord_emoji = self.bot.get_emoji(1290903900169310248)
        for i in range(10):
            cleaned_discord_username = (
                str(data[i]["discord_username"]).replace("_", "\\_").replace("*", "\\*")
            )
            cleaned_leetcode_username = (
                str(data[i]["username"]).replace("_", "\\_").replace("*", "\\*")
            )
            description += f"{str(f'{i + 1}.')}{str(data[i]['points']).rjust(5):.2f} pts - {discord_emoji}{cleaned_discord_username} ([{leetcode_emoji}{cleaned_leetcode_username}](https://leetcode.com/u/{data[i]['username']}))\n"
        embed = discord.Embed(
            title="Top 10 Users - Mobile View",
            description=description,
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text=f"Requested by {user_name}")
        return embed

    def create_detailed_embed(self, data, user_name):
        embed = discord.Embed(
            title="Top 10 Users", timestamp=datetime.datetime.utcnow()
        )
        embed.description = "View full leaderboard at [codeforall.nyc](https://www.codeforall.nyc/leaderboard)"
        leetcode_emoji = self.bot.get_emoji(1290903612351844464)
        discord_emoji = self.bot.get_emoji(1290903900169310248)
        discord_users = []
        leetcode_users = []
        points = []
        for i in range(10):
            cleaned_discord_username = (
                str(data[i]["discord_username"]).replace("_", "\\_").replace("*", "\\*")
            )
            cleaned_leetcode_username = (
                str(data[i]["username"]).replace("_", "\\_").replace("*", "\\*")
            )
            leetcode_users.append(cleaned_leetcode_username)
            discord_users.append(cleaned_discord_username)
            points.append(data[i]["points"])
        embed.add_field(
            name=f"{discord_emoji} Discord User",
            value="\n".join(discord_users),
            inline=True,
        )
        embed.add_field(
            name=f"{leetcode_emoji} Leetcode User",
            value="\n".join(leetcode_users),
            inline=True,
        )
        embed.add_field(
            name=":chart_with_upwards_trend: Points",
            value="\n".join(map(str, [f"{x:.2f}" for x in points])),
            inline=True,
        )
        embed.set_footer(text=f"Requested by {user_name}. ")
        return embed


async def setup(bot):
    await bot.add_cog(TopTen(bot))
