import asyncio
import random
import os
from pyrogram import Client, filters
from pymongo import MongoClient
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# CONFIG (ENV VARIABLES)
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URI = os.getenv("MONGO_URI")

STORAGE_CHANNEL = int(os.getenv("STORAGE_CHANNEL"))
RELEASE_CHANNEL = int(os.getenv("RELEASE_CHANNEL"))
OWNER_ID = int(os.getenv("OWNER_ID"))

# DB setup
mongo = MongoClient(MONGO_URI)
db = mongo["moviedb"]
movies = db["movies"]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

admins = [OWNER_ID]

# SAVE MOVIE (PRIVATE ONLY)
@app.on_message(filters.private & (filters.video | filters.document))
async def save_movie(client, message):
    if message.from_user.id not in admins:
        return

    sent = await message.copy(STORAGE_CHANNEL)

    movies.insert_one({
        "message_id": sent.id
    })

    await message.reply("✅ Movie saved successfully!")

# TOTAL
@app.on_message(filters.command("total"))
async def total(client, message):
    count = movies.count_documents({})
    await message.reply(f"📊 Total movies: {count}")

# SET RELEASE CHANNEL
@app.on_message(filters.command("set_release"))
async def set_release(client, message):
    global RELEASE_CHANNEL

    if message.from_user.id != OWNER_ID:
        return

    try:
        new_id = int(message.text.split()[1])
        RELEASE_CHANNEL = new_id
        await message.reply("✅ Release channel updated")
    except:
        await message.reply("❌ Invalid ID")

# RELEASE RANGE
@app.on_message(filters.command("release"))
async def release(client, message):
    if message.from_user.id not in admins:
        return

    try:
        _, start, end = message.text.split()
        start = int(start) - 1
        end = int(end)

        data = list(movies.find())[start:end]

        await message.reply(f"🚀 Releasing {len(data)} movies...")

        for movie in data:
            await client.forward_messages(
                RELEASE_CHANNEL,
                STORAGE_CHANNEL,
                movie["message_id"]
            )
            await asyncio.sleep(random.randint(8, 12))

        await message.reply("✅ Release completed")

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ADMIN ADD
@app.on_message(filters.command("add_admin"))
async def add_admin(client, message):
    if message.from_user.id != OWNER_ID:
        return

    user_id = int(message.text.split()[1])
    admins.append(user_id)

    await message.reply("✅ Admin added")

# ADMIN LIST
@app.on_message(filters.command("admins"))
async def list_admins(client, message):
    await message.reply(f"Admins:\n{admins}")

app.run()
from flask import Flask
import threading
import os

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()
