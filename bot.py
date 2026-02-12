import os
import json
import asyncio
from datetime import datetime, timedelta

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ================= UTIL =================
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = load_json("users.json")

    if chat_id not in users:
        users.append(chat_id)
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

# ================= REMINDERS =================
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

# ================= HANDLERS =================
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("today", today))
tg_app.add_handler(CommandHandler("nextclass", nextclass))
tg_app.add_handler(CommandHandler("week", week))

tg_app.job_queue.run_repeating(reminder, interval=60, first=10)

# ================= WEBHOOK =================
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    asyncio.run(tg_app.process_update(update))
    return "OK"

# ================= RUN =================
if __name__ == "__main__":
    async def main():
        await tg_app.initialize()
        await tg_app.start()
        app.run(host="0.0.0.0", port=PORT)

    asyncio.run(main())
