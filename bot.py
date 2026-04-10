import asyncio
import random
import os
from pyrogram import Client, filters
from pymongo import MongoClient
from flask import Flask
import threading

# FIX EVENT LOOP
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URI = os.getenv("MONGO_URI")

STORAGE_CHANNEL = int(os.getenv("STORAGE_CHANNEL"))
RELEASE_CHANNEL = int(os.getenv("RELEASE_CHANNEL"))

PASSWORD = "ankit123"

# DB
mongo = MongoClient(MONGO_URI)
db = mongo["moviedb"]
movies = db["movies"]

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

authorized_users = set()

# LOGIN
@app.on_message(filters.command("login"))
async def login(client, message):
    try:
        if message.text.split()[1] == PASSWORD:
            authorized_users.add(message.from_user.id)
            await message.reply("✅ Login successful!")
        else:
            await message.reply("❌ Wrong password")
    except:
        await message.reply("Usage: /login password")

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🤖 Bot is alive!\nUse /login password")

# SAVE MOVIE
@app.on_message(filters.private)
async def save_movie(client, message):
    if message.from_user.id not in authorized_users:
        return

    if not (message.video or message.document):
        return

    try:
        sent = await message.copy(STORAGE_CHANNEL)

        movies.insert_one({
            "message_id": sent.id
        })

        await message.reply("✅ Movie saved successfully!")

    except Exception as e:
        # 🔥 IMPORTANT DEBUG LINE
        await message.reply(f"❌ SAVE ERROR:\n{e}")

# TOTAL
@app.on_message(filters.command("total"))
async def total(client, message):
    if message.from_user.id not in authorized_users:
        return

    try:
        count = movies.count_documents({})
        await message.reply(f"📊 Total movies: {count}")
    except Exception as e:
        await message.reply(f"❌ TOTAL ERROR:\n{e}")

# RELEASE
@app.on_message(filters.command("release"))
async def release(client, message):
    if message.from_user.id not in authorized_users:
        return

    try:
        _, start, end = message.text.split()
        start = int(start) - 1
        end = int(end)

        data = list(movies.find())[start:end]

        if not data:
            await message.reply("❌ No movies found")
            return

        await message.reply(f"🚀 Releasing {len(data)} movies...")

        for movie in data:
            try:
                await client.forward_messages(
                    RELEASE_CHANNEL,
                    STORAGE_CHANNEL,
                    movie["message_id"]
                )
            except Exception as e:
                await message.reply(f"❌ RELEASE ERROR:\n{e}")

            await asyncio.sleep(random.randint(8, 12))

        await message.reply("✅ Release completed")

    except Exception as e:
        await message.reply(f"❌ COMMAND ERROR:\n{e}")

# FLASK
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

app.run()
