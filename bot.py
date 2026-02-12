import os, json, asyncio
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------- helpers ----------
def load(f):
    with open(f) as file:
        return json.load(file)

def save(f, d):
    with open(f, "w") as file:
        json.dump(d, file, indent=2)

# ---------- commands ----------
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
        await update.message.reply_text("No classes today 🎉")
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
    for d, cls in tt.items():
        msg += f"*{d}*\n"
        for c in cls:
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
                    f"⏰ Reminder\n\n{c['subject']}\n🕒 {c['time']}\n🏫 {c['room']}"
                )

# ---------- handlers ----------
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("today", today))
tg_app.add_handler(CommandHandler("nextclass", nextclass))
tg_app.add_handler(CommandHandler("week", week))

tg_app.job_queue.run_repeating(reminder, interval=60, first=10)

# ---------- webhook ----------
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    tg_app.update_queue.put_nowait(update)
    return "OK"

# ---------- run ----------
if __name__ == "__main__":
    async def main():
        await tg_app.initialize()
        await tg_app.start()
        app.run(host="0.0.0.0", port=PORT)
    asyncio.run(main())
