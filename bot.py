import discord
import os
import asyncio
from discord.ext import commands, tasks  
from dotenv import load_dotenv
from database import Database
from google.oauth2 import service_account
import gspread

# ✅ โหลด .env ถ้าอยู่ในเครื่อง Local
if os.path.exists('.env'):
    load_dotenv()

# ✅ ดึง TOKEN จาก Railway Environment หรือ .env
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ ไม่พบ DISCORD_TOKEN! กรุณาเพิ่มใน Railway Environment Variables")

# ✅ ดึง CREDENTIALS_JSON จาก Environment Variables หรือ .env
CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")  # CREDENTIALS_JSON ในรูปแบบ base64 หรือเป็น path ไฟล์
if not CREDENTIALS_JSON:
    raise ValueError("❌ ไม่พบ CREDENTIALS_JSON! กรุณาเพิ่มใน Railway Environment Variables")

# ถ้าค่า CREDENTIALS_JSON เป็น Path ของไฟล์ JSON, คุณสามารถใช้ได้โดยตรง
if os.path.exists(CREDENTIALS_JSON):
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_JSON)
else:
    # หาก CREDENTIALS_JSON เป็นข้อมูล base64 สามารถแปลงเป็นไฟล์ชั่วคราวได้
    import base64
    from io import BytesIO

    creds_data = base64.b64decode(CREDENTIALS_JSON)
    creds_file = BytesIO(creds_data)
    creds = service_account.Credentials.from_service_account_file(creds_file)

# ตั้งค่าบอทพร้อม Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.db = Database()
bot.db_lock = asyncio.Lock()  # ✅ ใช้ Lock ป้องกัน Database Locked

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.db.initialize()  # สร้างฐานข้อมูลก่อนใช้

    # ✅ กำหนด status ของบอท
    await bot.change_presence(activity=discord.Game("กับใจคุณ"))

    success_count, failed_cogs = 0, []

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(cog_name)
                success_count += 1
                print(f"✅ Loaded {cog_name}")
            except Exception as e:
                failed_cogs.append((cog_name, str(e)))
                print(f"❌ Failed to load {cog_name}: {e}")

    try:
        await bot.tree.sync()
        print("✅ Synced Slash Commands!")
    except Exception as e:
        print(f"❌ Failed to sync Slash Commands: {e}")

    print(f"\n🎯 Loaded {success_count} cogs successfully.")
    if failed_cogs:
        print("❌ Failed to load the following cogs:")
        for cog, error in failed_cogs:
            print(f"   - {cog}: {error}")

    print("✅ Cupid Call Online")

    @tasks.loop(minutes=25)  # ทำงานทุกๆ 25 นาที
    async def keep_alive():
        channel = bot.get_channel(1335980962189672509)
        if channel:
            await channel.send("🟢Online CupidCall ยังทำงานอยู่!")

bot.run(TOKEN)
