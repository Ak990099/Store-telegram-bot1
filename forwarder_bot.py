import asyncio
import os
import threading
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message

# ── ENV VARIABLES ──────────────────────────────────────────
BOT_TOKEN        = os.environ.get("BOT_TOKEN")
API_ID           = int(os.environ.get("API_ID"))
API_HASH         = os.environ.get("API_HASH")
SOURCE_CHAT      = int(os.environ.get("SOURCE_CHAT"))
DESTINATION_CHAT = int(os.environ.get("DESTINATION_CHAT"))

PROGRESS_FILE = "last_msg_id.txt"

bot = Client("forwarder_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_last_id():
    if os.path.exists(PROGRESS_FILE):
        val = open(PROGRESS_FILE).read().strip()
        return int(val) if val else 0
    return 0

def save_last_id(msg_id):
    open(PROGRESS_FILE, "w").write(str(msg_id))

def reset_progress():
    open(PROGRESS_FILE, "w").write("0")

config = {
    "source": SOURCE_CHAT,
    "destination": DESTINATION_CHAT,
    "running": False
}

@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply(
        "👋 **NC™ Forwarder Bot**\n\n"
        "📋 **Commands:**\n"
        "/status — Current config\n"
        "/setsource -100xxx — Source change\n"
        "/setdest -100xxx — Destination change\n"
        "/forward — Forwarding shuru\n"
        "/stop — Forwarding roko\n"
        "/reset — Fresh start\n"
    )

@bot.on_message(filters.command("status"))
async def status(_, m: Message):
    await m.reply(
        f"📊 **Current Config:**\n\n"
        f"📥 Source: `{config['source']}`\n"
        f"📤 Destination: `{config['destination']}`\n"
        f"⏩ Last ID: `{get_last_id()}`\n"
        f"🔄 Running: `{config['running']}`"
    )

@bot.on_message(filters.command("setsource"))
async def set_source(_, m: Message):
    try:
        new_id = int(m.text.split()[1])
        config["source"] = new_id
        await m.reply(f"✅ Source set: `{new_id}`")
    except:
        await m.reply("❌ Usage: `/setsource -100xxxxxxxxxx`")

@bot.on_message(filters.command("setdest"))
async def set_dest(_, m: Message):
    try:
        new_id = int(m.text.split()[1])
        config["destination"] = new_id
        await m.reply(f"✅ Destination set: `{new_id}`")
    except:
        await m.reply("❌ Usage: `/setdest -100xxxxxxxxxx`")

@bot.on_message(filters.command("reset"))
async def reset(_, m: Message):
    reset_progress()
    await m.reply("🔄 Reset! Ab /forward se fresh start hoga.")

@bot.on_message(filters.command("stop"))
async def stop(_, m: Message):
    config["running"] = False
    await m.reply("🛑 Forwarding rok di!")

@bot.on_message(filters.command("forward"))
async def forward(_, m: Message):
    if config["running"]:
        await m.reply("⚠️ Already chal raha hai! Pehle /stop karo.")
        return
    config["running"] = True
    await m.reply(
        f"🚀 **Forwarding Shuru!**\n\n"
        f"📥 From: `{config['source']}`\n"
        f"📤 To: `{config['destination']}`\n"
        f"⏩ Resume ID: `{get_last_id()}`"
    )
    asyncio.create_task(run_forward(m.chat.id))

async def run_forward(notify_id):
    count = 0
    last_id = get_last_id()
    try:
        async for message in bot.get_chat_history(config["source"]):
            if not config["running"]:
                await bot.send_message(notify_id, f"🛑 Stopped! Forwarded: {count}")
                return
            if message.id <= last_id:
                continue
            try:
                if message.video or message.document:
                    await bot.copy_message(
                        chat_id=config["destination"],
                        from_chat_id=config["source"],
                        message_id=message.id
                    )
                    count += 1
                    save_last_id(message.id)
                    if count % 100 == 0:
                        await bot.send_message(
                            notify_id,
                            f"✅ Progress: {count} forwarded\n⏩ Last ID: {message.id}"
                        )
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                print(f"⚠️ Error: {e}")
                await asyncio.sleep(3)
    except Exception as e:
        await bot.send_message(notify_id, f"❌ Error: {e}")
    config["running"] = False
    await bot.send_message(notify_id, f"🎉 Done! Total: {count}")

async def health(request):
    return web.Response(text="✅ Running!")

def run_web():
    webapp = web.Application()
    webapp.router.add_get("/", health)
    web.run_app(webapp, port=int(os.environ.get("PORT", 8080)))

threading.Thread(target=run_web, daemon=True).start()
bot.run()
