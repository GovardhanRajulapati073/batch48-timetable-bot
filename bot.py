import os, json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

def load(file):
    with open(file) as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    users = load("users.json")
    if cid not in users:
        users.append(cid)
        save("users.json", users)

    await update.message.reply_text(
        "📚 Batch 48 Timetable Bot\n\n"
        "/today – Today’s classes\n"
        "/nextclass – Next class\n"
        "/week – Weekly timetable"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = datetime.now().strftime("%A")
    tt = load("timetable.json")

    if day not in tt:
        await update.message.reply_text("🎉 No classes today!")
        return

    msg = f"📅 {day}\n\n"
    for c in tt[day]:
        msg += f"{c['time']} – {c['subject']}\n🏫 {c['room']}\n\n"
    await update.message.reply_text(msg)

async def nextclass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    day = now.strftime("%A")
    tt = load("timetable.json")

    for c in tt.get(day, []):
        ct = datetime.strptime(c["time"], "%I:%M %p").replace(
            year=now.year, month=now.month, day=now.day
        )
        if ct > now:
            await update.message.reply_text(
                f"⏭ Next Class\n\n{c['subject']}\n🕒 {c['time']}\n🏫 {c['room']}"
            )
            return
    await update.message.reply_text("No more classes today")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tt = load("timetable.json")
    msg = "📅 Weekly Timetable\n\n"
    for day, classes in tt.items():
        msg += f"*{day}*\n"
        for c in classes:
            msg += f"{c['time']} – {c['subject']} ({c['room']})\n"
        msg += "\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def reminder(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    day = now.strftime("%A")
    tt = load("timetable.json")
    users = load("users.json")

    for c in tt.get(day, []):
        ct = datetime.strptime(c["time"], "%I:%M %p").replace(
            year=now.year, month=now.month, day=now.day
        )
        if timedelta(minutes=9) <= (ct - now) <= timedelta(minutes=10):
            for u in users:
                await context.bot.send_message(
                    u,
                    f"⏰ Class Reminder\n\n{c['subject']}\n🕒 {c['time']}\n🏫 {c['room']}"
                )

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("nextclass", nextclass))
    app.add_handler(CommandHandler("week", week))

    app.job_queue.run_repeating(reminder, interval=60, first=10)

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
