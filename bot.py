import os
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))

# ---------- helpers ----------
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ---------- commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_json("users.json")
    cid = update.effective_chat.id
    if cid not in users:
        users.append(cid)
        save_json("users.json", users)

    await update.message.reply_text(
        "📚 Batch 48 Timetable Bot\n\n"
        "/today – Today’s classes\n"
        "/nextclass – Next class\n"
        "/week – Weekly timetable"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = datetime.now().strftime("%A")
    tt = load_json("timetable.json")

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
    tt = load_json("timetable.json")

    for c in tt.get(day, []):
        ct = datetime.strptime(c["time"], "%I:%M %p").replace(
            year=now.year, month=now.month, day=now.day
        )
        if ct > now:
            await update.message.reply_text(
                f"⏭ Next Class\n\n"
                f"{c['subject']}\n"
                f"🕒 {c['time']}\n"
                f"🏫 {c['room']}"
            )
            return

    await update.message.reply_text("No more classes today")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tt = load_json("timetable.json")
    msg = "📅 Weekly Timetable\n\n"

    for day, classes in tt.items():
        msg += f"{day}\n"
        for c in classes:
            msg += f"{c['time']} – {c['subject']} ({c['room']})\n"
        msg += "\n"

    await update.message.reply_text(msg)

# ---------- reminders ----------
async def reminder(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    day = now.strftime("%A")
    tt = load_json("timetable.json")
    users = load_json("users.json")

    for c in tt.get(day, []):
        ct = datetime.strptime(c["time"], "%I:%M %p").replace(
            year=now.year, month=now.month, day=now.day
        )
        if timedelta(minutes=9) <= (ct - now) <= timedelta(minutes=10):
            for u in users:
                await context.bot.send_message(
                    chat_id=u,
                    text=(
                        "⏰ Class Reminder\n\n"
                        f"{c['subject']}\n"
                        f"🕒 {c['time']}\n"
                        f"🏫 {c['room']}"
                    )
                )

# ---------- app ----------
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("nextclass", nextclass))
app.add_handler(CommandHandler("week", week))

app.job_queue.run_repeating(reminder, interval=60, first=10)

# ---------- RUN WEBHOOK (THIS IS THE KEY) ----------
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="",
        webhook_url=f"https://batch48-timetable-bot.onrender.com"
    )
