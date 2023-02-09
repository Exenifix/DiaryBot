from datetime import datetime

import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.converters import DateConverter
from utils.utils import generate_diary
from utils.views import Modal


class DiaryCommands(Cog):
    @commands.slash_command(name="new_entry")
    async def new_entry(self, inter: disnake.ApplicationCommandInteraction):
        """
        Add a new entry into your diary.
        """
        date = datetime.now().date()
        if await self.bot.db.fetchval(
            "SELECT EXISTS(SELECT * FROM entries WHERE user_id = $1 AND created_at = $2)", inter.user.id, date
        ):
            await inter.send("The entry on this day already exists! Use `/edit_entry` to edit it.", ephemeral=True)
            return

        modal = Modal(
            title="New Entry",
            components=[
                disnake.ui.TextInput(
                    label="Describe your day",
                    custom_id="content",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=10,
                    max_length=1024,
                )
            ],
        )
        await inter.response.send_modal(modal)
        m_inter = await modal.wait()
        await self.bot.db.new_entry(inter.user.id, date, m_inter.text_values["content"])
        await m_inter.send("Successfully added new diary entry!")

    @commands.slash_command(name="diary")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def diary(
        self, inter: disnake.ApplicationCommandInteraction, period_start: DateConverter, period_end: DateConverter
    ):
        """
        Generate diary file for selected period and send it into your DMs.

        Parameters
        ----------
        period_start: Start of the diary
        period_end: End of the diary
        """
        period = period_end - period_start
        if not 1 <= period.total_days() <= 365:
            await inter.send(
                "I can only generate diaries for periods longer than 1 day and shorter than 1 year.", ephemeral=True
            )
            return

        await inter.response.defer(ephemeral=True)
        data = await self.bot.db.get_entries(inter.user.id, period)
        if len(data) == 0:
            await inter.send("No entries found for this period.", ephemeral=True)
            return
        io = await generate_diary(data)
        if isinstance(inter.channel, disnake.DMChannel):
            await inter.send("Here's your diary!", file=disnake.File(io, filename="diary.txt"))
            return
        try:
            await inter.user.send("Here's your diary!", file=disnake.File(io, filename="diary.txt"))
            await inter.send("Sent diary to your DMs!", ephemeral=True)
        except disnake.HTTPException:
            await inter.send(
                "Failed to send diary to your DMs. Allow me to message you or use this command in DMs.", ephemeral=True
            )

    @commands.slash_command(name="edit_entry")
    async def edit_entry(self, inter: disnake.ApplicationCommandInteraction, date: DateConverter):
        """
        Edit already existing entry.

        Parameters
        ----------
        date: Day to edit entry on
        """
        entry = await self.bot.db.get_entry(inter.user.id, date)
        if entry is None:
            await inter.send("There's no entry created on that day.", ephemeral=True)
            return
        modal = Modal(
            title="Edit Entry",
            components=[
                disnake.ui.TextInput(
                    label="Describe your day",
                    custom_id="content",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=10,
                    max_length=1024,
                    value=entry.content,
                )
            ],
        )
        await inter.response.send_modal(modal)
        m_inter = await modal.wait()
        await self.bot.db.edit_entry(inter.author.id, date, m_inter.text_values["content"])
        await m_inter.send("Successfully edited diary entry!")
