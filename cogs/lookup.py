import discord
from discord.ext import commands
from discord import app_commands
import lib.dbfuncs as dbfuncs
import lib.emojis as emojis
import requests
import datetime
import traceback


class Lookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Lookup cog loaded")

    @app_commands.command(
        name="lookup",
        description="Lookup a user on the leaderboard by discord or leetcode username.",
    )
    @app_commands.describe(username="enter discord or leetcode username")
    async def lookup(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        embed = discord.Embed(title=f"User Lookup - {username}", timestamp=datetime.datetime.now())
        sad = self.bot.get_emoji(1110418413920206868)
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        description = f'User {username} not found {sad if sad else ":cry:"}'
        embed.set_image(url="https://media1.tenor.com/m/lxJgp-a8MrgAAAAd/laeppa-vika-half-life-alyx.gif")
        urls = ["https://server.rakibshahid.com/api/discord_lookup", "https://server.rakibshahid.com/api/leetcode_lookup"]
        # get emojis
        emojimap = emojis.get_all_emojis(self)
        leetcode_emoji = emojimap["lc"]
        discord_emoji = emojimap["dc"]
        header_titles = ["discord-username", "leetcode-username"]
        for url, header_title in zip(urls, header_titles):
            response = requests.get(url, headers={header_title: username})
            try:
                if response.status_code == 200:
                    data = response.json()
                    description = f"{discord_emoji} **Discord Username**: {data['discord_username']}\n"
                    leetcode_url = f"https://leetcode.com/u/{data['leetcode_username']}"
                    description += f"{leetcode_emoji} **LeetCode Username**: [{data['leetcode_username']}]({leetcode_url})\n"
                    # get points using db function
                    points = dbfuncs.get_user_points(data['discord_username'])
                    description += f":chart_with_upwards_trend: **Points**: {points}\n"
                    description += f":crown: **Wins**: {data['wins']}\n"
                    description += f":1234: **Local Rank**: {data['local_ranking']}\n"
                    # format global rank with commas
                    global_ranking = "{:,}".format(data['ranking'])
                    description += f":earth_americas: **Global LeetCode Rank**: {global_ranking}\n"
                    
                    
                    # get leetcode ac
                    leetcode_ac_url = "https://server.rakibshahid.com/api/leetcode_ac"
                    leetcode_ac_response = requests.get(leetcode_ac_url, headers={"leetcode-username": data['leetcode_username']})
                    leetcode_ac = []
                    if leetcode_ac_response.status_code == 200:
                        json = leetcode_ac_response.json()
                        for i in range(min(5,json["count"])):
                            timestamp = (json['submission'][i]['timestamp'])
                            language = json['submission'][i]['lang'].lower()
                            if "c++" in language:
                                emoji = emojimap["cpp"]
                            elif language == "c":
                                emoji = emojimap["c"]
                            elif language == "java":
                                emoji = emojimap["java"]
                            elif language == "javascript":
                                emoji = emojimap["js"]
                            elif language == "rust":
                                emoji = emojimap["rust"]
                            elif language == "typescript":
                                emoji = emojimap["ts"]
                            elif language == "golang":
                                emoji = emojimap["go"]
                            elif "py" in language:
                                emoji = emojimap["py"]
                            else:
                                emoji = ""
                            
                            leetcode_ac.append(f"{emoji} {json['submission'][i]['title']} - <t:{timestamp}:R>")
                    if leetcode_ac:
                        leetcode_ac_string = '\n'.join(leetcode_ac)
                        description += f":white_check_mark: **{len(leetcode_ac)} Recent LeetCode Accepted Submissions**:\n{leetcode_ac_string}\n"
                    
                    embed.set_image(url=data['avatar'])
                        
                    break
            except Exception as e:
                traceback.print_exc()
        embed.description = description

        
        
        await interaction.followup.send(
            embed = embed
        )


async def setup(bot):
    await bot.add_cog(Lookup(bot))