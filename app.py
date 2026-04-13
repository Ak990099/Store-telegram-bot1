import asyncio
import os
from flask import Flask, request
from pyrogram import Client
from pyrogram.errors import FloodWait
from pymongo import MongoClient

# ── ENV VARIABLES ─────────────────────────
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

SOURCE = int(os.getenv("SOURCE_CHANNEL"))
DEST = int(os.getenv("DEST_CHANNEL"))

MONGO_URL = os.getenv("MONGO_URL")

# ── SETUP ────────────────────────────────
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

# ── DATABASE FUNCTIONS ───────────────────
def get_last_id():
    data = col.find_one({"_id": "copy"})
    return data["last_id"] if data else 0

def save_last_id(msg_id):
    col.update_one(
        {"_id": "copy"},
        {"$set": {"last_id": msg_id}},
        upsert=True
    )

# ── COPY FUNCTION ────────────────────────
async def copy_batch(limit):
    last_id = get_last_id()
    count = 0

    async for msg in bot.get_chat_history(SOURCE):
        if msg.id <= last_id:
            break

        try:
            # Sirf video/document copy karega
            if msg.video or msg.document:
                await msg.copy(DEST)
                save_last_id(msg.id)
                count += 1

                # SAFE DELAY
                await asyncio.sleep(2)

                if count >= limit:
                    break

        except FloodWait as e:
            print(f"FloodWait: {e.value}s")
            await asyncio.sleep(e.value)

        except Exception as e:
            print("Error:", e)
            continue

    return count

# ── WEB ROUTE ────────────────────────────
@app.route("/")
def home():
    return "Bot Running ✅"

@app.route("/copy")
def copy_route():
    limit = int(request.args.get("limit", 50))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = loop.run_until_complete(copy_batch(limit))

    return f"Copied {result} messages ✅"

# ── START BOT ────────────────────────────
bot.start()

# ── RUN SERVER ───────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
