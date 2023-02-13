from datetime import datetime

import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.converters import DateConverter
from utils.plots import draw_moods_plot
from utils.utils import generate_diary
from utils.views import Modal


class DiaryCommands(Cog):
    @commands.slash_command(name="new_entry")
    async def new_entry(self, inter: disnake.ApplicationCommandInteraction, mood: commands.Range[1, 10]):
        """
        Add a new entry into your diary.

        Parameters
        ----------
        mood: How good was your day from 1 (bad) to 10 (good)
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
        await self.bot.db.execute(
            "INSERT INTO moods (user_id, mood, day) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
            inter.user.id,
            mood,
            date,
        )
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
    async def edit_entry(
        self, inter: disnake.ApplicationCommandInteraction, date: DateConverter, mood: commands.Range[1, 10] = None
    ):
        """
        Edit already existing entry.

        Parameters
        ----------
        date: Day to edit entry on
        mood: New mood to set on that date
        """
        if date.is_future():
            await inter.send("Cannot edit date in the future", ephemeral=True)
            return
        entry = await self.bot.db.get_entry(inter.user.id, date)
        modal = Modal(
            title="Edit Entry",
            components=[
                disnake.ui.TextInput(
                    label="Describe your day",
                    custom_id="content",
                    style=disnake.TextInputStyle.paragraph,
                    min_length=10,
                    max_length=1024,
                    value=entry.content if entry is not None else None,
                )
            ],
        )
        await inter.response.send_modal(modal)
        m_inter = await modal.wait()
        if mood is not None:
            await self.bot.db.execute(
                """
                INSERT INTO moods (user_id, mood, day)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, day) DO
                UPDATE SET mood = $2 WHERE user_id = $1 AND day = $2""",
                inter.user.id,
                mood,
                date,
            )
        if entry is not None:
            await self.bot.db.edit_entry(inter.author.id, date, m_inter.text_values["content"])
            await inter.send("Successfully edited diary entry!")
            return
        await self.bot.db.new_entry(inter.user.id, date, m_inter.text_values["content"])
        await m_inter.send("Successfully created diary entry on that date!")

    @commands.slash_command(name="moods")
    async def moods(
        self, inter: disnake.ApplicationCommandInteraction, period_start: DateConverter, period_end: DateConverter
    ):
        """
        Draw a graph of your moods throughout the period

        Parameters
        ----------
        period_start: Start of period, e.g. Jan 10, March 20th 2023
        period_end: End of period
        """
        data = await self.bot.db.get_moods(inter.user.id, period_end - period_start)
        if len(data[0]) == 0:
            await inter.send("There are no mood records for that period!", ephemeral=True)
            return
        await inter.response.defer()
        await inter.send(file=disnake.File(await draw_moods_plot(data), filename="moods.png"))
