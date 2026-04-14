import os
import asyncio
import threading
from flask import Flask, request
from pyrogram import Client, filters
from pymongo import MongoClient

# ----------- ENV VARIABLES -----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE = int(os.getenv("SOURCE_CHANNEL"))
DEST = int(os.getenv("DEST_CHANNEL"))

MONGO_URL = os.getenv("MONGO_URL")

# ----------- SETUP -----------
app = Flask(__name__)

mongo = MongoClient(MONGO_URL)
db = mongo["telegram"]
col = db["progress"]

bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ----------- DATABASE -----------
def get_last_id():
    data = col.find_one({"_id": "copy"})
    return data["last_id"] if data else 0

def save_last_id(msg_id):
    col.update_one(
        {"_id": "copy"},
        {"$set": {"last_id": msg_id}},
        upsert=True
    )

# ----------- BOT COMMAND -----------
@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("✅ Bot Working Successfully!")

# ----------- COPY FUNCTION -----------
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
            print("Copy Error:", e)

        if count >= limit:
            break

    return count

# ----------- FLASK ROUTES -----------
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

# ----------- BOT THREAD -----------
def run_bot():
    print("🚀 Bot starting...")
    bot.run()

# ----------- MAIN START -----------
if __name__ == "__main__":
    print("✅ Starting Flask + Bot...")

    threading.Thread(target=run_bot, daemon=True).start()

    app.run(host="0.0.0.0", port=8080)
