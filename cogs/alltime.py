import discord
from discord.ext import commands
from discord import app_commands
import requests
import datetime
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check


class AllTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_mobile_view = False

    @commands.Cog.listener()
    async def on_ready(self):
        print("Top OAT cog loaded")

    @app_commands.command(
        name="alltime",
        description="View the top 10 users of all time.",
    )
    @track_queries
    @maintenance_check()
    async def alltime(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = "https://server.rakibshahid.com/leaderboard/leaderboard_history"
            response = requests.get(url)
            data = response.json()
            embed = self.create_detailed_embed(data, interaction.user.name)

            view = discord.ui.View(timeout=None)
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
        try:
            description = ""
            leetcode_emoji = self.bot.get_emoji(1290903612351844464)
            discord_emoji = self.bot.get_emoji(1290903900169310248)
            for i in range(10):
                cleaned_discord_username = (
                    str(data[i]["discord_username"])
                    .replace("_", "\\_")
                    .replace("*", "\\*")
                )
                cleaned_leetcode_username = (
                    str(data[i]["username"]).replace("_", "\\_").replace("*", "\\*")
                )
                description += f"{str(f'{i + 1}.').ljust(4)}{('**'+(str(data[i]['total_wins'])+'**')+' wins, '+('**'+str(data[i]['total_points'])+'**') + ' pts').rjust(17)} - {discord_emoji}{str(cleaned_discord_username)} ([{leetcode_emoji}{str(cleaned_leetcode_username)}](https://leetcode.com/u/{data[i]['username']}))\n"

            embed = discord.Embed(
                title="All Time Top 10 - Mobile View",
                description=description,
                timestamp=datetime.datetime.now(),
            )
            embed.set_footer(text=f"Requested by {user_name}")
            return embed
        except Exception as e:
            print(e)
            return

    def create_detailed_embed(self, data, user_name):
        embed = discord.Embed(
            title="All Time Top 10", timestamp=datetime.datetime.utcnow()
        )
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
            discord_users.append(f"{cleaned_discord_username}")
            points.append(
                f"{(str(data[i]['total_wins'])+',').ljust(5)}{data[i]['total_points']}"
            )
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
            name=":trophy: Wins,Points", value="\n".join(map(str, points)), inline=True
        )
        embed.set_footer(text=f"Requested by {user_name}")
        return embed


async def setup(bot):
    await bot.add_cog(AllTime(bot))
