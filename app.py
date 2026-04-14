import os
import asyncio
import threading
from flask import Flask, request
from pyrogram import Client, filters
from pymongo import MongoClient

# ================= ENV =================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

SOURCE = int(os.getenv("SOURCE_CHANNEL", "0"))
DEST = int(os.getenv("DEST_CHANNEL", "0"))
MONGO_URL = os.getenv("MONGO_URL", "")

# ================= FLASK =================
app = Flask(__name__)

# ================= DB =================
mongo = MongoClient(MONGO_URL)
db = mongo["telegram"]
col = db["progress"]

def get_last_id():
    data = col.find_one({"_id": "copy"})
    return data["last_id"] if data else 0

def save_last_id(msg_id):
    col.update_one(
        {"_id": "copy"},
        {"$set": {"last_id": msg_id}},
        upsert=True
    )

# ================= BOT =================
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 🔥 START COMMAND
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("Bot working ✅")

# ================= COPY FUNCTION =================
async def copy_messages(limit):
    last_id = get_last_id()
    count = 0

    async for msg in bot.get_chat_history(SOURCE):
        if msg.id <= last_id:
            break

        try:
            await msg.copy(DEST)
            save_last_id(msg.id)
            count += 1
        except Exception as e:
            print("Copy error:", e)

        if count >= limit:
            break

    return count

# ================= ROUTES =================
@app.route("/")
def home():
    return "Bot Running ✅"

@app.route("/copy")
def copy_route():
    limit = int(request.args.get("limit", 5))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = loop.run_until_complete(copy_messages(limit))

    return f"Copied {result} messages"

# ================= START BOT =================
def run_bot():
    try:
        print("🚀 Bot starting...")
        bot.run()
    except Exception as e:
        print("❌ Bot crash:", e)

threading.Thread(target=run_bot, daemon=True).start()
print("✅ Thread started")

# ================= RUN SERVER =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
