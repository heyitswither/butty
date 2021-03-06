from discord.ext import commands
import discord
from datetime import datetime
from dateutil.relativedelta import relativedelta
import parsedatetime.parsedatetime
from pytz import timezone
import time
import sqlite3
import asyncio


class Reminders:


    def __init__(self, bot):
        self.bot = bot
        self.database = sqlite3.connect("cogs/reminders.db")
        self.cursor = self.database.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS alerts
                          (user, channel, time, message, repeat, id)''')
        self.loop = self.bot.loop.create_task(self.reminder_loop())

    async def reminder_loop(self):
        while not self.bot.is_closed:
            now = datetime.now(timezone('UTC'))
            now = format(now, '%Y-%m-%d %H:%M:%S')
            alerts = self.cursor.execute("SELECT user, channel, message FROM alerts WHERE time < ?", (now,)).fetchall()

            for user_id, channel, message in alerts:
                try:
                    await self.bot.send_message(discord.Object(channel), "<@{}> {}".format(user_id, message))
                except:
                    pass

            self.cursor.execute("DELETE FROM alerts WHERE time < ?", (now,))
            self.database.commit()
            await asyncio.sleep(5)

    @commands.group(aliases=['r'], brief='do "help r" for more detail')
    async def reminder(self):
        """Because you need to not forget stuff

        EG:
        [reminder add 2 hours, remove the cake from hell
        [r show
        """
        pass

    @reminder.command(aliases=['a'], pass_context="True")
    async def add(self, context):
        # oh god what is this shit
        # harru why you do this
        # fuck off it works probably
        message = " ".join(context.message.content.split(" ")[2:])
        msg = message.split(",", 1)
        cal = parsedatetime.Calendar()
        alertid = len(self.cursor.execute("SELECT * FROM alerts WHERE user=?", (context.message.author.id,)).fetchall()) + 1
        dontusemodulesasvariablenames = cal.parse(msg[0], datetime.now(timezone('UTC')))
        alert_time = time.strftime('%Y-%m-%d %H:%M:%S', dontusemodulesasvariablenames[0])
        self.cursor.execute("INSERT INTO alerts VALUES(?, ?, ?, ?, ?, ?)", (context.message.author.id, context.message.channel.id, alert_time, msg[1], "no", alertid))
        self.database.commit()
        await self.bot.say("Reminder set for " +  alert_time + " UTC")

    @reminder.command(aliases=['d', 'r'],pass_context=True)
    async def delete(self, context):
        args = context.message.content.split(" ")
        ids = int(args[2])
        moveup = []
        user = context.message.author.id
        removed = (self.cursor.execute("SELECT message FROM alerts WHERE user=? AND id=?", (user, ids))).fetchall()
        self.cursor.execute("DELETE FROM alerts WHERE user=? AND id=?", (user, ids))
        newid = (self.cursor.execute("SELECT id FROM alerts WHERE id=?", (user,))).fetchall()
        for x in range(0, len(newid)):
            if newid[x][0] > ids:
                moveup.append(newid[x][0])
        for x in range(0, len(moveup)):
            self.cursor.execute("UPDATE alerts SET id=? WHERE id=? AND user=?", ((moveup[x] - 1), moveup[x], user))
        self.database.commit()
        await self.bot.say("Deleted **" + removed[0][0] + "** from your reminder list")

    @reminder.command(aliases=['c'], pass_context=True)
    async def clear(self, context):
        user = context.message.author.id
        self.cursor.execute("DELETE FROM alerts WHERE user=?", (user,))
        self.database.commit()
        await self.bot.say("Your reminders have been cleared")

    @reminder.command(aliases=['s', 'l'], pass_context=True)
    async def show(self, context):
        reminder_list = self.cursor.execute("SELECT message FROM alerts WHERE user=?", (context.message.author.id,)).fetchall()
        x = 0
        reply = ''
        for reminder in reminder_list:
            x += 1
            reply += str(x) + ": " + reminder[0] + "\n"
        await self.bot.say("<@" + context.message.author.id + ">'s reminders:\n" + reply)


def setup(bot):
    bot.add_cog(Reminders(bot))
