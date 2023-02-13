import disnake
from disnake.ext import commands, tasks

from utils.bot import Cog
from utils.errors import UNKNOWN, get_error_msg


class SystemListeners(Cog):
    @Cog.listener()
    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError
    ) -> None:
        msg = get_error_msg(error)
        if msg is UNKNOWN:
            await inter.send("Sorry unknown exception occurred, we are already working on it!", ephemeral=True)
            raise error
        await inter.send(msg)


class SystemLoops(Cog):
    def __init__(self, *args):
        super().__init__(*args)
        self.presence_updater.start()

    @tasks.loop(minutes=30)
    async def presence_updater(self):
        await self.bot.wait_until_ready()
        users_count = len(self.bot.users)
        await self.bot.change_presence(
            activity=disnake.Activity(name=f"{users_count} user{'s' if users_count != 1 else ''}")
        )
