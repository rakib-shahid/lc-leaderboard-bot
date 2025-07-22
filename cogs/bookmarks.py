import discord
from discord.ext import commands
from discord import app_commands
import datetime
from lib.dbfuncs import track_queries, with_db, add_bookmark
from lib.maintenance import maintenance_check


@with_db
def get_bookmarks(cursor, discord_id, start=0):
    try:
        cursor.execute("SELECT id FROM users WHERE discord_id = %s;", (discord_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "User not found"

        user_id = user_row[0]

        cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE user_id = %s;", (user_id,))
        total_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT problem_slug
            FROM bookmarks
            WHERE user_id = %s
            ORDER BY saved_at DESC
            OFFSET %s LIMIT 10;
            """,
            (user_id, start),
        )
        bookmarks = [row[0] for row in cursor.fetchall()]

        return True, (bookmarks, total_count)

    except Exception as e:
        return False, str(e)


@with_db
def remove_bookmarks_by_indices(cursor, discord_id, indices):
    try:
        cursor.execute("SELECT id FROM users WHERE discord_id = %s;", (discord_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return False, "User not found"
        user_id = user_row[0]

        cursor.execute(
            "SELECT problem_slug FROM bookmarks WHERE user_id = %s ORDER BY saved_at DESC;",
            (user_id,),
        )
        all_slugs = [row[0] for row in cursor.fetchall()]

        to_remove = [all_slugs[i - 1] for i in indices if 0 < i <= len(all_slugs)]

        for slug in to_remove:
            cursor.execute(
                "DELETE FROM bookmarks WHERE user_id = %s AND problem_slug = %s;",
                (user_id, slug),
            )

        return True, to_remove
    except Exception as e:
        return False, str(e)


class Bookmarks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bookmarks cog loaded")

    @app_commands.command(
        name="bookmarks",
        description="View your saved bookmarks.",
    )
    @track_queries
    @maintenance_check()
    async def bookmarks(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        class BookmarksView(discord.ui.View):
            def __init__(self, bot, user_id, user_name, start=0):
                super().__init__(timeout=None)
                self.bot = bot
                self.user_id = user_id
                self.user_name = user_name
                self.start = start
                self.total_count = 0
                self.message = None

                self.add_button = discord.ui.Button(
                    label="Add Bookmark",
                    style=discord.ButtonStyle.primary,
                    row=1,
                    emoji="🔖",
                )
                self.remove_button = discord.ui.Button(
                    label="Remove Bookmark",
                    style=discord.ButtonStyle.danger,
                    row=2,
                    emoji="🗑️",
                )
                self.prev_button = discord.ui.Button(
                    label="",
                    style=discord.ButtonStyle.secondary,
                    row=0,
                    emoji="⬅️",
                )
                self.next_button = discord.ui.Button(
                    label="", style=discord.ButtonStyle.secondary, row=0, emoji="➡️"
                )

                self.add_button.callback = self.open_add_modal
                self.remove_button.callback = self.open_remove_modal
                self.prev_button.callback = self.prev_page
                self.next_button.callback = self.next_page

                self.add_item(self.add_button)
                self.add_item(self.remove_button)
                self.add_item(self.prev_button)
                self.add_item(self.next_button)

            async def refresh_embed(self):
                success, result = get_bookmarks(self.user_id, self.start)
                if not success:
                    return await self.message.edit(
                        content=f"Error: {result}", embed=None, view=self
                    )

                bookmarks, self.total_count = result
                embed = discord.Embed(
                    title="Your bookmarked problems:",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow(),
                )

                if not bookmarks:
                    embed.description = "No bookmarks saved."
                else:
                    links = "\n".join(
                        f"{self.start + i + 1}. [{slug.replace('-', ' ').title()}](https://leetcode.com/problems/{slug}/)"
                        for i, slug in enumerate(bookmarks)
                    )
                    embed.description = links

                embed.set_footer(text=f"Requested by {self.user_name}")

                self.prev_button.disabled = self.start == 0
                self.next_button.disabled = self.start + 10 >= self.total_count

                await self.message.edit(embed=embed, view=self)

            async def prev_page(self, interaction: discord.Interaction):
                self.start = max(0, self.start - 10)
                await self.refresh_embed()
                await interaction.response.defer()

            async def next_page(self, interaction: discord.Interaction):
                self.start += 10
                await self.refresh_embed()
                await interaction.response.defer()

            async def open_add_modal(self, interaction: discord.Interaction):
                class AddBookmarkModal(discord.ui.Modal, title="Add a Bookmark"):
                    url = discord.ui.TextInput(label="LeetCode problem URL")

                    async def on_submit(modal_self, interaction: discord.Interaction):
                        success, msg = add_bookmark(
                            interaction.user.id, str(modal_self.url)
                        )
                        if success:
                            await interaction.response.send_message(
                                f"✅ Bookmark added for **[{msg}]({modal_self.url})**",
                                ephemeral=True,
                            )
                            await self.refresh_embed()
                        else:
                            await interaction.response.send_message(
                                f"❌ Error: {msg}", ephemeral=True
                            )

                await interaction.response.send_modal(AddBookmarkModal())

            async def open_remove_modal(self, interaction: discord.Interaction):
                class RemoveBookmarkModal(discord.ui.Modal, title="Remove Bookmarks"):
                    instructions = discord.ui.TextInput(
                        label="Which to remove? (e.g. 1,3,7)",
                        placeholder="1,5,33,16",
                        required=True,
                    )
                    confirm_text = discord.ui.TextInput(
                        label="Type CONFIRM to confirm:",
                        placeholder="...",
                        required=True,
                    )

                    async def on_submit(modal_self, interaction: discord.Interaction):
                        try:
                            nums = [
                                int(x.strip())
                                for x in str(modal_self.instructions).split(",")
                            ]
                            if modal_self.confirm_text.value != "CONFIRM":
                                await interaction.response.send_message(
                                    "❌ Failed to confirm.", ephemeral=True
                                )
                                return
                            success, result = remove_bookmarks_by_indices(
                                interaction.user.id, nums
                            )
                            if success:
                                await interaction.response.send_message(
                                    f"🗑️ Removed: `{', '.join(result)}`", ephemeral=True
                                )
                                await self.refresh_embed()
                            else:
                                await interaction.response.send_message(
                                    f"❌ Error: {result}", ephemeral=True
                                )
                        except Exception as e:
                            await interaction.response.send_message(
                                f"❌ Error: {e}", ephemeral=True
                            )

                await interaction.response.send_modal(RemoveBookmarkModal())

        view = BookmarksView(
            self.bot, interaction.user.id, interaction.user.name, start=0
        )

        success, result = get_bookmarks(interaction.user.id, 0)
        if not success:
            await interaction.followup.send(f"Error: {result}", ephemeral=True)
            return

        bookmarks, total = result
        embed = discord.Embed(
            title="Your bookmarked problems:",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow(),
        )
        if not bookmarks:
            embed.description = "No bookmarks saved."
        else:
            links = "\n".join(
                f"{i+1}. [{slug.replace('-', ' ').title()}](https://leetcode.com/problems/{slug}/)"
                for i, slug in enumerate(bookmarks)
            )
            embed.description = links

        embed.set_footer(text=f"Requested by {interaction.user.name}")
        view.total_count = total
        view.message = await interaction.followup.send(
            embed=embed, ephemeral=True, view=view
        )


async def setup(bot):
    await bot.add_cog(Bookmarks(bot))
