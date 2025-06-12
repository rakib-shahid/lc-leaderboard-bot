from discord import app_commands
from discord import Interaction
from discord.embeds import Embed
from discord.app_commands import CheckFailure

MAINTENANCE_COMMANDS = {
    # "challenge",
    "register",
    "remove",
}

class MaintenanceCheckFailure(CheckFailure):
    pass

def maintenance_check():
    async def predicate(interaction: Interaction) -> bool:
        cmd = interaction.command.name
        cog_name = interaction.command.extras.get("cog", None)
        # print("cmd name: ",cmd)
        full_name = f"{cog_name}.{cmd}" if cog_name else cmd
        if cmd in MAINTENANCE_COMMANDS or full_name in MAINTENANCE_COMMANDS:
            embed = Embed(
                title="🚧 Under Maintenance",
                description="This command is currently undergoing maintenance.",
                color=0xFFA500,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            raise MaintenanceCheckFailure()
        return True
    return app_commands.check(predicate)

