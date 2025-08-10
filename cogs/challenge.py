import datetime
import traceback
import discord
from discord.ext import commands
from discord import app_commands
from lib.dbfuncs import track_queries
import lib.dbfuncs as dbfuncs
import asyncio
import random
import requests
from typing import Optional
from lib.maintenance import maintenance_check
import config


async def get_question(user1, user2, difficulty=None):
    difficulty_count = {"EASY": 870, "MEDIUM": 1819, "HARD": 817, None: 3506}
    question_data = None
    while True:
        problem_number = random.randint(1, difficulty_count[difficulty])
        query = f"&difficulty={difficulty}" if difficulty else ""
        endpoint = (
            f"{config.LC_SERVER_URL}/problems?limit=1&skip={problem_number}{query}"
        )
        question_data = requests.get(endpoint).json()

        if not question_data["problemsetQuestionList"][0][
            "isPaidOnly"
        ] and await check_question(user1, user2, question_data):
            break
    return question_data["problemsetQuestionList"][0]


async def check_question(user1, user2, question):
    question_title = question["problemsetQuestionList"][0]["title"]
    if dbfuncs.check_if_user_did_problem(
        user1, question_title
    ) or dbfuncs.check_if_user_did_problem(user2, question_title):
        return False
    return True


async def check_users_available(user1, user2):
    user1_status = dbfuncs.check_if_user_busy(user1)
    user2_status = dbfuncs.check_if_user_busy(user2)
    return not user1_status and not user2_status


async def create_problem_embed(question_data, author_user, other_user):
    problem_embed = discord.Embed(
        title=f"{question_data['questionFrontendId']}. {question_data['title']}"
    )
    problem_colors = {
        "Easy": discord.Color.green(),
        "Medium": discord.Color.orange(),
        "Hard": discord.Color.red(),
    }
    description_string = f"{author_user.mention} vs {other_user.mention}!\n"
    description_string += f"First person to solve \"{question_data['title']}\" wins!\n[Link to problem](https://leetcode.com/problems/{question_data['titleSlug']})\n"
    description_string += f"Difficulty: {question_data['difficulty']}\nAcceptance rate: {question_data['acRate']:.2f}%\n\n"
    # description_string += f"React below to start this challenge! \n-# Note: Once you start a challenge, you **cannot** participate in other challenges until you complete it by solving the problem or quit it using **/challengequit**"
    description_string += f"React below to start this challenge! \n-# Note: Once you start a challenge, you **cannot** participate in other challenges until you complete it by solving the problem!"

    # url = f"https://leetcode.server.rakibshahid.com/select?titleSlug={question_data['titleSlug']}"
    # detailed_question_data = requests.get(url).json()
    # print(detailed_question_data)

    problem_embed.color = problem_colors[question_data["difficulty"]]
    problem_embed.description = description_string

    return problem_embed


async def check_all_players_joined(msg, author_user, other_user):
    players = {author_user.id: [author_user, 0], other_user.id: [other_user, 0]}
    async for user in msg.reactions[0].users():
        if user.id == author_user.id or user.id == other_user.id:
            players[user.id][1] = 1

    if not all([player[1] for player in players.values()]):
        # embed.description = "Not all players have joined! Challenge cancelled! :crying_cat:"
        # await msg.edit(embed=embed)
        return False
    return True


async def check_problem_done_usingAPI(user, question_data):
    url = f"{config.LC_SERVER_URL}/{user}/acSubmission"
    response = requests.get(url).json()
    for submission in reversed(response["submission"]):
        if submission["title"] == question_data["title"]:
            return submission
    return None


def parse_unix_timestamp(unix_ts):
    return datetime.datetime.fromtimestamp(int(unix_ts))


def extract_submission_time(api_res, fallback_res):
    if api_res and "timestamp" in api_res:
        return parse_unix_timestamp(api_res["timestamp"])
    if fallback_res:
        return fallback_res[0][3]
    return None


async def sleep_and_monitor(
    msg, embed, author_user, other_user, time_limit, question_data
):
    winner = None
    loser = None
    winner_res = None
    loser_res = None
    minutes = 1

    for _ in range(time_limit // minutes):
        await asyncio.sleep(minutes * 60)

        author_api_res = await check_problem_done_usingAPI(
            dbfuncs.get_leetcode_from_discord(author_user.name), question_data
        )
        other_api_res = await check_problem_done_usingAPI(
            dbfuncs.get_leetcode_from_discord(other_user.name), question_data
        )

        if author_api_res:
            print(f"[API] {author_user.name}: {author_api_res}")
        if other_api_res:
            print(f"[API] {other_user.name}: {other_api_res}")

        author_res = dbfuncs.check_if_user_did_problem(
            author_user.name, question_data["title"]
        )
        other_res = dbfuncs.check_if_user_did_problem(
            other_user.name, question_data["title"]
        )

        print(f"[DB] {author_user.name}: {author_res}")
        print(f"[DB] {other_user.name}: {other_res}")

        author_time = extract_submission_time(author_api_res, author_res)
        other_time = extract_submission_time(other_api_res, other_res)

        if author_time and other_time:
            if author_time < other_time:
                winner, loser = author_user, other_user
                winner_res, loser_res = (
                    author_api_res or author_res,
                    other_api_res or other_res,
                )
            elif other_time < author_time:
                winner, loser = other_user, author_user
                winner_res, loser_res = (
                    other_api_res or other_res,
                    author_api_res or author_res,
                )
            else:
                print("Both submitted at the same time:", author_time)
            break
        elif author_time:
            winner, loser = author_user, other_user
            winner_res, loser_res = (
                author_api_res or author_res,
                other_api_res or other_res,
            )
            break
        elif other_time:
            winner, loser = other_user, author_user
            winner_res, loser_res = (
                other_api_res or other_res,
                author_api_res or author_res,
            )
            break

    if winner is None or loser is None:
        embed.description += "\nNo winner could be determined! Either both failed to solve or finished at the same time. Challenge concluded!"
        embed.color = discord.Color.orange()
        embed.timestamp = datetime.datetime.now()
        embed.set_footer(text="Challenge concluded.")
        await msg.edit(embed=embed)
        dbfuncs.set_user_busy(author_user.name, busy=False)
        dbfuncs.set_user_busy(other_user.name, busy=False)
        return

    await wrapup_challenge(
        msg, embed, winner, loser, question_data, winner_res, loser_res
    )


def get_submission_time_str(res):
    if isinstance(res, dict) and "timestamp" in res:
        return str(parse_unix_timestamp(res["timestamp"]))
    if isinstance(res, list) and len(res) > 0:
        return str(res[0][3])
    return None


async def wrapup_challenge(
    msg, embed, winner, loser, question_data, winner_res, loser_res
):
    dbfuncs.set_user_busy(winner.name, busy=False)
    dbfuncs.set_user_busy(loser.name, busy=False)
    embed.timestamp = datetime.datetime.now()
    embed.set_footer(text=f"Challenge concluded.")
    await msg.edit(embed=embed)

    dbfuncs.add_win(winner.name)
    dbfuncs.add_loss(loser.name)
    w_stats = dbfuncs.get_user_challenge_stats(winner.name)
    l_stats = dbfuncs.get_user_challenge_stats(loser.name)

    final_embed = discord.Embed(title="Challenge Over!", color=discord.Color.blue())
    final_embed.description = (
        f"Challenge between {winner.mention} and {loser.mention} has ended!\n"
    )
    final_embed.description += f"After completing '{question_data['title']}' first, {winner.mention} has won!\n"
    final_embed.description += f"Final stats:\n"

    winner_time = get_submission_time_str(winner_res)
    loser_time = get_submission_time_str(loser_res)

    if winner_time:
        final_embed.description += (
            f"{winner.mention} completed the problem at {winner_time}\n"
        )
    else:
        final_embed.description += (
            f"{winner.mention} did not complete the problem at the time of checking!\n"
        )

    if loser_time:
        final_embed.description += (
            f"{loser.mention} completed the problem at {loser_time}\n"
        )
    else:
        final_embed.description += (
            f"{loser.mention} did not complete the problem at the time of checking!\n"
        )

    final_embed.description += f"\nUser, Wins, Losses, Quits\n"
    final_embed.description += (
        f"{winner.name}: {', '.join([str(x) for x in w_stats])}\n"
    )
    final_embed.description += f"{loser.name}: {', '.join([str(x) for x in l_stats])}\n"

    await msg.reply(embed=final_embed)


async def start_challenge(msg, embed, author_user, other_user, question_data):
    await msg.add_reaction("✅")
    embed.description += (
        f"\n\nWaiting 20 seconds for all users to join before starting\n"
    )
    description_string = embed.description

    for i in range(20, 0, -1):
        await asyncio.sleep(1)
        embed.description = description_string + f"." * i
        await msg.edit(embed=embed)
    embed.description = description_string
    await msg.edit(embed=embed)

    msg = await msg.fetch()

    if not await check_all_players_joined(msg, author_user, other_user):
        embed.description += (
            "\nNot all players have confirmed! Challenge cancelled! :crying_cat:"
        )
        embed.color = discord.Color.red()
        await msg.edit(embed=embed)
        return False

    time_limit = 0
    if question_data["difficulty"] == "Easy":
        time_limit = 15
    elif question_data["difficulty"] == "Medium":
        time_limit = 30
    elif question_data["difficulty"] == "Hard":
        time_limit = 60
    embed.description += f"\nAll players joined. Challenge started!\nYou have {time_limit} minutes to complete the problem!"
    await msg.edit(embed=embed)
    dbfuncs.set_user_busy(author_user.name)
    dbfuncs.set_user_busy(other_user.name)

    await sleep_and_monitor(
        msg, embed, author_user, other_user, time_limit, question_data
    )


class Challenge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Challenge cog loaded")

    async def users_valid(self, author_user, other_user):
        author = dbfuncs.check_discord_user(author_user.name)
        other = dbfuncs.check_discord_user(other_user.name)
        return {author_user: author, other_user: other}

    @app_commands.command(name="challenge", description="Challenge a user")
    @app_commands.describe(discord_user="discord user to challenge")
    @app_commands.describe(difficulty="Problem Difficulty")
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="Easy", value="EASY"),
            app_commands.Choice(name="Medium", value="MEDIUM"),
            app_commands.Choice(name="Hard", value="HARD"),
        ]
    )
    @track_queries
    @maintenance_check()
    async def challenge(
        self,
        interaction: discord.Interaction,
        discord_user: discord.Member,
        difficulty: Optional[discord.app_commands.Choice[str]],
    ):
        try:
            await interaction.response.defer()
            ################################################
            # if interaction.user.id != 235835251052642315:
            #   await interaction.followup.send(content=":shushing_face: :eyes:")
            #    return
            author_user = await self.bot.fetch_user(interaction.user.id)
            other_user = await self.bot.fetch_user(discord_user.id)

            if author_user == other_user:
                await interaction.followup.send(f"Challenge someone else!")
                return

            # check for unregistered users
            valid_res = await self.users_valid(interaction.user, discord_user)
            if any(x == [] for x in valid_res.values()):
                invalid_users = [
                    user.mention for user, res in valid_res.items() if res == []
                ]
                await interaction.followup.send(
                    f"Invalid users: {''.join(invalid_users)}! Make them register for the leaderboard first! :crying_cat:"
                )
                return

            description_string = f"Waiting 15s for {other_user.mention} and {author_user.mention} to join! React below to join!"
            if difficulty is not None:
                description_string += f"\n{difficulty.name} Problem"
            message_embed = discord.Embed(
                title="Leetcode Challenge!",
                description=description_string,
                color=discord.Color.blue(),
            )
            await interaction.followup.send(
                embed=message_embed,
                content=f"{author_user.mention} vs {other_user.mention}",
            )
            msg = await interaction.original_response()
            await msg.add_reaction("✅")
            # wait
            for i in range(15, 0, -1):
                message_embed.description = description_string + f"\n{'.'*i}"
                await asyncio.sleep(1)
                await msg.edit(embed=message_embed)
            # check if join
            msg = await msg.fetch()
            # {id: int -> [user: discord.User, joined: Boolean]}
            if not await check_all_players_joined(
                msg=msg, author_user=author_user, other_user=other_user
            ):
                message_embed.description = (
                    "Not all players have joined! Challenge cancelled! :crying_cat:"
                )
                message_embed.color = discord.Color.red()
                await msg.edit(embed=message_embed)
                return

            difficulty = difficulty.value if difficulty is not None else None
            question_data = await get_question(
                user1=interaction.user.name,
                user2=discord_user.name,
                difficulty=difficulty,
            )
            # print(question_data)
            # check if already engaged in 1v1
            available = await check_users_available(
                interaction.user.name, discord_user.name
            )
            if not available:
                # message_embed.description = "At least one user is already in a challenge!\n They must either complete the challenge or quit it using /challengequit!\n Challenge cancelled! :crying_cat:"
                message_embed.description = "At least one user is already in a challenge!\n They must complete their ongoing challenge\n Challenge cancelled! :crying_cat:"
                message_embed.color = discord.Color.red()
                await msg.edit(embed=message_embed)
                return

            message_embed.description = f"Both players {author_user.mention} and {other_user.mention} joined!\nSee following reply to start the challenge..."
            await msg.edit(embed=message_embed)
            problem_embed = await create_problem_embed(
                question_data, author_user, other_user
            )
            problem_msg = await msg.reply(embed=problem_embed)
            if not await start_challenge(
                problem_msg, problem_embed, author_user, other_user, question_data
            ):
                return

        except Exception as e:
            traceback.print_exc()
            dbfuncs.set_user_busy(author_user.name, busy=False)
            dbfuncs.set_user_busy(other_user.name, busy=False)
        # sleep_until_done()


async def setup(bot):
    await bot.add_cog(Challenge(bot))
