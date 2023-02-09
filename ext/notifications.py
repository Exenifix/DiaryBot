from datetime import time

import asyncpg
import disnake
from disnake.ext import commands, tasks

from utils.bot import Cog


class NotificationManagers(Cog):
    def __init__(self, *args):
        super().__init__(*args)
        self.send_notifications.start()

    @tasks.loop(minutes=1)
    async def send_notifications(self):
        await self.bot.wait_until_ready()
        users_to_notify: set[int] = {
            r["user_id"]
            for r in await self.bot.db.fetchall(
                """
                SELECT
                    user_id
                FROM
                    notifications
                WHERE notification_time < CURRENT_TIME AND (last_notified IS NULL OR last_notified < CURRENT_DATE)
                """
            )
        }
        await self.bot.db.execute(
            """
            UPDATE
                notifications
            SET
                last_notified = CURRENT_DATE
            WHERE notification_time < CURRENT_TIME AND (last_notified IS NULL OR last_notified < CURRENT_DATE)
            """
        )
        users_to_delete: list[int] = []
        for user_id in users_to_notify:
            try:
                user = await self.bot.getch_user(user_id, strict=True)
                await user.send(
                    "Hey, time to fill out new diary entry! To disable this notification, use `/notification disable`"
                )
            except (commands.UserNotFound, disnake.HTTPException):
                users_to_delete.append(user_id)
        if len(users_to_delete) > 0:
            await self.bot.db.executemany(
                "DELETE FROM notifications WHERE user_id = $1", [(i,) for i in users_to_delete]
            )
            self.bot.log.warning("Failed to notify %d users", len(users_to_delete))


class NotificationCommands(Cog):
    @commands.slash_command(name="notification")
    async def notification(self, inter: disnake.ApplicationCommandInteraction):
        ...

    @notification.sub_command(name="set")
    async def notif_set(
        self, inter: disnake.ApplicationCommandInteraction, hour: commands.Range[0, 24], minute: commands.Range[0, 60]
    ):
        """
        Set time to send the notification at every day

        Parameters
        ----------
        hour: Time hour, 24-hour format, UTC timezone
        minute: Time minute
        """
        try:
            t = time(hour, minute)  # type: ignore
        except Exception as e:
            await inter.send(f"Invalid time + timezone provided: {e}", ephemeral=True)
            return
        try:
            await inter.user.send(
                "This is a test message to ensure I am able to send notifications to you", delete_after=1
            )
            await self.bot.db.execute(
                "INSERT INTO notifications (user_id, notification_time) VALUES ($1, $2)", inter.user.id, t
            )
            await inter.send(
                f"Successfully set the notification to be sent every day at **{t.hour}:{t.minute} UTC**!\n\n"
                "**WARNING**\nIf you close DMs or leave all mutual servers with bot, "
                "it will remove you from notifications list and you will have to "
                "configure it again."
            )
        except asyncpg.UniqueViolationError:
            await inter.send(
                "You already have a notification set. First use `/notification disable`, then set new one",
                ephemeral=True,
            )
        except disnake.HTTPException:
            await inter.send(
                "I am unable to send you notifications. Please open your DMs. "
                "You can add this bot to your personal server and open them there.",
                ephemeral=True,
            )

    @notification.sub_command(name="disable")
    async def notif_disable(self, inter: disnake.ApplicationCommandInteraction):
        """
        Remove yourself from notifications list
        """
        await self.bot.db.execute("DELETE FROM notifications WHERE user_id = $1", inter.user.id)
        await inter.send("Removed you from notifications list (if you even were there)")
