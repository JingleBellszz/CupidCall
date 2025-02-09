import aiosqlite
import asyncio
import shutil
import datetime

class Database:
    def __init__(self, db_name="cupidcall.db"):
        self.db_name = db_name
        self.db = None
        self.lock = asyncio.Lock()  # 🔐 ป้องกัน Database Locked

        # ✅ เพิ่มรายการ ID ของแอดมิน
        self.ADMIN_IDS = {
            264091289010700288,
            625292873914515456,
            685853506481291416,
            285099806601510912,
            954297193500643361
        }

    async def backup_database(self):
        """📦 สำรองฐานข้อมูลก่อนการใช้งาน"""
        try:
            shutil.copy(self.db_name, f"{self.db_name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            print("✅ Database Backup Completed!")
        except Exception as e:
            print(f"⚠️ Database Backup Failed: {e}")

    async def initialize(self):
        """🔄 เปิด Connection และตั้งค่า WAL Mode"""
        if self.db is None:
            self.db = await aiosqlite.connect(self.db_name)
            await self.db.execute("PRAGMA journal_mode=WAL;")  # ✅ ป้องกัน Database Locked
            await self.db.execute("PRAGMA synchronous=NORMAL;")  # ✅ ลด Latency
            await self.db.execute("PRAGMA wal_autocheckpoint=1000;")  # ✅ ปรับปรุง WAL Performance
            await self.create_tables()

    async def create_tables(self):
        """🗄️ สร้างตารางถ้ายังไม่มี"""
        async with self.lock:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    discord_id INTEGER PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    username TEXT NOT NULL,
                    profile_pic TEXT,
                    channel_id INTEGER,
                    is_admin BOOLEAN DEFAULT 0  -- ✅ 0 = ผู้เล่นทั่วไป, 1 = Admin
                )
            """)
            await self.db.commit()

    ADMIN_IDS = {264091289010700288, 625292873914515456, 685853506481291416, 285099806601510912, 954297193500643361}
    ADMIN_USERNAME = "Cupid Operator"
    ADMIN_AVATAR = "https://i.imgur.com/81RQdUl.png"
    ADMIN_CHANNEL_ID = 1335980962189672509

    async def save_user(self, discord_id, display_name, nickname, username, profile_pic, channel_id):
        """💾 บันทึกข้อมูลผู้ใช้"""
        async with self.lock:
            await self.initialize()
            is_admin = 1 if discord_id in self.ADMIN_IDS else 0  # ✅ ใช้ self.ADMIN_IDS

            await self.db.execute("""
                INSERT INTO users (discord_id, display_name, nickname, username, profile_pic, channel_id, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET 
                    display_name = excluded.display_name,
                    nickname = excluded.nickname,
                    username = excluded.username,
                    profile_pic = excluded.profile_pic,
                    channel_id = excluded.channel_id,
                    is_admin = excluded.is_admin
            """, (discord_id, display_name, nickname, username, profile_pic, channel_id, is_admin))
            await self.db.commit()

    async def get_user(self, user_id):
        """🔍 ดึงข้อมูลผู้ใช้"""
        async with self.lock:
            await self.initialize()
            async with self.db.execute("SELECT display_name, nickname, username, profile_pic FROM users WHERE discord_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def close(self):
        """❌ ปิดฐานข้อมูลเมื่อบอทปิด"""
        async with self.lock:
            if self.db:
                await self.db.close()
                self.db = None

    async def get_user_data(self, discord_id):
        """📌 ดึงข้อมูล Username และรูปโปรไฟล์ของผู้ใช้"""
        async with self.lock:
            await self.initialize()
            async with self.db.execute("SELECT username, profile_pic, is_admin FROM users WHERE discord_id = ?", (discord_id,)) as cursor:
                return await cursor.fetchone()

    async def get_user_id(self, username):
        """🔢 ดึง `discord_id` ของ Username"""
        async with self.lock:
            await self.initialize()
            async with self.db.execute("SELECT discord_id FROM users WHERE username = ?", (username,)) as cursor:
                data = await cursor.fetchone()
                return data[0] if data else None

    async def get_channel_id(self, username):
        """📢 ดึง `channel_id` ของผู้ใช้"""
        async with self.lock:
            await self.initialize()
            if username == "Cupid Operator":  # ✅ ถ้าผู้รับเป็นแอดมิน
                async with self.db.execute("SELECT channel_id FROM users WHERE is_admin = 1 LIMIT 1") as cursor:
                    data = await cursor.fetchone()
                    return data[0] if data else None  # ✅ คืนค่า channel_id ของแอดมิน
            else:
                async with self.db.execute("SELECT channel_id FROM users WHERE username = ?", (username,)) as cursor:
                    data = await cursor.fetchone()
                    return data[0] if data else None  # ✅ คืนค่า channel_id ของผู้เล่นทั่วไป

    async def get_all_admins(self):
        """📌 ดึงข้อมูลแอดมินทั้งหมด"""
        async with self.lock:
            await self.initialize()
            async with self.db.execute("SELECT discord_id FROM users WHERE is_admin = 1") as cursor:
                data = await cursor.fetchall()
                return [(self.ADMIN_USERNAME, row[0]) for row in data] if data else []

    async def get_all_user_data(self):
        """📌 ดึงข้อมูล username, display_name, และ is_admin ของทุก user"""
        async with self.lock:
            await self.initialize()
            async with self.db.execute("SELECT username, display_name, is_admin FROM users") as cursor:
                data = await cursor.fetchall()
                return data if data else []  # ✅ ถ้าไม่มีข้อมูล คืน `[]`

    async def setup(bot):
        bot.db = Database()
        await bot.db.initialize()
