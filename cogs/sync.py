# sync all commands2
import discord
from discord.ext import commands
import lib.dbfuncs as dbfuncs
from lib.dbfuncs import track_queries
from lib.maintenance import maintenance_check

class Sync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Sync command loaded")

    # sync command
    # move into main if possible
    @commands.command()
    # @track_queries
    @maintenance_check()
    async def sync(self, ctx) -> None:
        # print(ctx.message.author.id)
        admins = dbfuncs.get_admins()
        admins = set([admin[0] for admin in admins])
        if ctx.message.author.id in admins:
            # print("Admin detected")
            # update status
            activity = discord.Activity(
                type=discord.ActivityType.watching, name=f" NeetCode videos"
            )
            await self.bot.change_presence(activity=activity)
            # change nickname
            print("Changed name and status")
            # sync commands
            # client = self.bot
            print(ctx.guild.id)
            print("Syncing commands")
            fmt = await self.bot.tree.sync()
            commands = len(fmt)
            print("Synced commands")
            user = self.bot.get_user(ctx.message.author.id)
            # send message
            await ctx.send(f"{user.mention} synced {commands} commands")
            print("Replied")
        # other user tries to sync
        else:
            user = self.bot.get_user(ctx.message.author.id)
            await ctx.send(f"{user} is not a bot admin! Can't sync :(")


async def setup(bot):
    await bot.add_cog(Sync(bot))
