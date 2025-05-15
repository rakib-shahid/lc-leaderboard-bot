import traceback
import discord
import re
from discord.ext import commands
from discord import app_commands
import requests
import datetime
import html
from html.parser import HTMLParser
from lib.dbfuncs import track_queries


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code':
            self.out.append('`')
        elif tag in {'strong', 'b'}:
            self.out.append('**')
        elif tag == 'li':
            self.out.append('• ')
        elif tag in {'em', 'i'}:
            self.out.append('*')
        elif tag == 'br':
            self.out.append('\n')

    def handle_endtag(self, tag):
        if tag == 'code':
            self.out.append('`')
        elif tag in {'strong', 'b'}:
            self.out.append('**')
        elif tag == 'li':
            self.out.append('\n')
        elif tag in {'em', 'i'}:
            self.out.append('*')

    def handle_data(self, data):
        self.out.append(data.replace('`', '\\`'))

    def get_text(self):
        text = ''.join(self.out)
        return re.sub(r'\n{2,}', '\n', text).strip()


class Daily(commands.Cog):
    def __init__(self, bot, parser):
        self.bot = bot
        self.parser = parser

    @commands.Cog.listener()
    async def on_ready(self):
        print("Daily cog loaded")

    @app_commands.command(
        name="daily",
        description="View the LeetCode Daily question.",
    )
    @track_queries
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            date = datetime.datetime.now().strftime('%m/%d/%y')
            embed = discord.Embed(title=f"Daily Question {date}", timestamp=datetime.datetime.now())
            url = 'https://leetcode.server.rakibshahid.com/daily'
            response = requests.get(url).json()
            q_link = response['questionLink']
            q_id = response['questionFrontendId']
            q_title = response['questionTitle']
            q_diff = response['difficulty']
            q_prem = response['isPaidOnly']
            q_desc = response['question']
            q_desc = html.unescape(q_desc)
            self.parser.feed(q_desc)
            q_desc = self.parser.get_text()
            topics = [topic['name'] for topic in response['topicTags']]
            hints = response['hints']
            likes = response['likes']
            dislikes = response['dislikes']
            # FORM DESCRIPTION STRING
            desc_string = ''
            desc_string += f'**[{q_id}. {q_title}]({q_link})**\n'
            match q_diff:
                case 'Hard':
                    desc_string += ':red_square: Hard\n'
                    embed.color = discord.Color.red()
                case 'Medium':
                    desc_string += ':orange_square: Medium\n'
                    embed.color = discord.Color.orange()
                case 'Easy':
                    desc_string += ':green_square: Easy\n'
                    embed.color = discord.Color.green()
            if q_prem:
                desc_string += "\n:lock: Premium required!"
            desc_string += '\n**Description:**\n'
            desc_string += q_desc
            desc_string += '\n'
            desc_string += '\nTopics:\n'
            desc_string += ','.join(['||'+topic+'||' for topic in topics])
            
            desc_string += '\n'
            desc_string += '\nHints:\n'
            desc_string += '\n'.join(['- ||'+hint+'||' for hint in hints])
            desc_string += f'\n:+1:{likes}, :-1:{dislikes}\n'
            
            if len(desc_string) >= 4096 :
                print(f'[DAILY ERROR] embed description too long! {len(desc_string)} exceeds limit of 4096 ')
            embed.description = desc_string
            await interaction.followup.send(
                embed = embed
            )
        except Exception as e:
            print(f"[DAILY ERROR] see below:")
            traceback.print_exc()
            


async def setup(bot):
    await bot.add_cog(Daily(bot, Parser()))
