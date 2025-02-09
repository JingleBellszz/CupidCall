import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from googlesheet import get_user_data  # เชื่อมต่อ Google Sheets
from datetime import datetime
import asyncio

CATEGORY_NAME = "୨୧ Private Room"
ROLE_ID = 1335453115477917868  # เปลี่ยนเป็น ID Role ที่ถูกต้อง


def create_profile_embed(username, display_name, profile_pic):
    """สร้าง Embed หน้าโปรไฟล์ผู้เล่น"""
    embed = discord.Embed(
        title="<:012:1335452788930379910> Login Successful!",
        description=f"ติ๊ง! CupidCall พร้อมให้บริการแล้ว!\n\n"
                    f"{username}, ได้รับ `CupidCall Premium Package` 7 วัน <:013:1335452790906028136>",
        color=0xce002d
    )
    embed.add_field(name="<:014:1335452794362265693> Display Name", value=f"```{display_name}```", inline=False)
    embed.add_field(name="<a:pumping_heart:1336304764354429001> CupidCall Username", value=f"```{username}```", inline=False)
    embed.set_footer(
        text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
        icon_url="https://i.imgur.com/81RQdUl.png"
    )
    if profile_pic:  # ✅ ป้องกันปัญหาในกรณีไม่มีรูป
        embed.set_thumbnail(url=profile_pic)
    return embed

class LoginModal(Modal):
    """ฟอร์ม Login ด้วย CupidCall Username"""
    def __init__(self, bot, member, channel):
        super().__init__(title="🔑 Login to CupidCall")
        self.bot = bot
        self.member = member
        self.channel = channel

        self.username = TextInput(label="💘 CupidCall Username", placeholder="ใส่ชื่อโปรไฟล์ใหม่ที่ได้ลงทะเบียนเอาไว้", required=True)
        # ✅ ทำให้ช่อง Password ไม่สามารถแก้ไขได้
        self.password = TextInput(
            label="🔒 Password (ไม่จำเป็นต้องกรอก)",
            placeholder="***********",
            default="***********",  #
            required=False,  #
            style=discord.TextStyle.short
        )

        self.add_item(self.username)
        self.add_item(self.password)  # ✅ เพิ่มช่อง Password (แต่แก้ไขไม่ได้)

    async def on_submit(self, interaction: discord.Interaction):
        """เมื่อผู้ใช้กด Login"""
        await interaction.response.defer(thinking=True)  # ป้องกัน Interaction Timeout

        username = self.username.value.strip()
        user_data = get_user_data(username)

        if not user_data:
            await interaction.followup.send("❌ ไม่พบบัญชี CupidCall นี้ในระบบ! กรุณาลองใหม่", ephemeral=True)
            return

        display_name = user_data["Display Name"]
        nickname = user_data["Nickname"]
        profile_pic = user_data["Profile Picture"]

        # **🎭 ให้ Role (ยศ)**
        role = discord.utils.get(interaction.guild.roles, id=ROLE_ID)
        if role and role not in interaction.user.roles:
            await interaction.user.add_roles(role)

        # **📛 เปลี่ยนชื่อเล่นเป็น `Display Name`**
        if interaction.user.nick != display_name:
            await interaction.user.edit(nick=display_name)

        # **🏠 เปลี่ยนชื่อห้องเป็น `꒰usernameヾnickname꒱`**
        if self.channel:
            new_channel_name = f"꒰{username}ヾ{nickname}꒱"
            if self.channel.name != new_channel_name:
                await self.channel.edit(name=new_channel_name)

        # **💾 บันทึกข้อมูลลงฐานข้อมูล (ใช้ Lock)**
            async with self.bot.db_lock:  # 🔐 ใช้ asyncio.Lock() ป้องกัน Database Locked
                db = self.bot.db
                await db.save_user(
                    discord_id=interaction.user.id,
                    display_name=display_name,
                    nickname=nickname,
                    username=username,
                    profile_pic=profile_pic,
                    channel_id=self.channel.id
                )

        # **📜 ส่ง Embed หน้าโปรไฟล์**
        embed = create_profile_embed(username, display_name, profile_pic)
        message1 = await interaction.followup.send(embed=embed, ephemeral=False)
        await message1.pin()

        # ตรวจสอบว่า `bot_avatar_url` มีค่าหรือไม่
        bot_avatar_url = interaction.client.user.avatar.url if interaction.client.user.avatar else None

        # กำหนดค่า `new_embed` ก่อนใช้
        new_embed = discord.Embed(
            title="<:032:1335453941340704808> Welcome to CupidCall!",
            description="บัญชีนี้ใช้สำหรับกิจกรรมเท่านั้น ห้ามส่งต่อเด็ดขาด",
            color=0xce002d
        )
        new_embed.add_field(
            name="<:026:1335453926543196241> RPTH User",
            value="```CupidCall```",
            inline=False
        )
        new_embed.add_field(
            name="<:025:1335453922579578962> Password",
            value="```LoveCraft```",
            inline=False
        )
        new_embed.add_field(
            name="\u200b",
            value="<:011:1335452786938089642> ขอให้คุณสนุกกับการค้นหาคู่เดท! และอย่าลืมรักษาตัวตนของคุณให้เป็นความลับนะ!\n\n"
                  "มีข้อสงสัย ติดต่อ : <@&1337076552172703775>",
            inline=False
        )
        new_embed.set_footer(
            text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
            icon_url="https://i.imgur.com/81RQdUl.png"   # ✅ ใช้รูปโปรไฟล์ของบอท
        )
        new_embed.set_image(url="https://i.imgur.com/Mhip3Ee.png")

        if bot_avatar_url:
            new_embed.set_thumbnail(url=bot_avatar_url)

        message2 = await interaction.followup.send(embed=new_embed, ephemeral=False)

        await message2.pin()

        # ✅ **สร้างเธรดส่วนตัวหลังจาก message2 ถูกส่งแล้ว**
        thread_name = f"💌 {username}ヾ𝑚𝑎𝑖𝑙𝑏𝑜𝑥"
        thread = await self.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            auto_archive_duration=60  # ซ่อนเธรดหลังจากไม่มีการใช้งาน 1 ชม.
        )

        # ✅ **ส่งข้อความฟอร์มไปในเธรด**
        form_message = f"""-# {interaction.user.mention}

# <:012:1335452788930379910> แบบฟอร์มต่าง ๆ
-# <:smallredheart:1336199079008407604> **สำหรับส่งใน Discord (เธรดส่วนตัวเท่านั้น)**  
-# <:smallredheart:1336199079008407604> **CupidCall Username คือชื่อที่ใช้ในกิจกรรมนี้**  
-# <:smallredheart:1336199079008407604><@&1337076552172703775> ด้วยทุกครั้งที่ส่งแบบฟอร์ม
=================================

## <:015:1335452796241055785> **แบบฟอร์ม Cupid’s Memories**  
-# **Cupid’s Memories (การบันทึกความทรงจำหลังเดต)**  
> **ชื่อ :** (CupidCall Username)  
> **ชื่อคู่เดต :**  
> **ผลการเดต :** (สำเร็จ / ไม่สำเร็จ)  
> **ลิงก์เดต :** (ลิงก์ไปยังโรลเพลย์แรกของตัวเอง)  
> **ลิงก์โปรไฟล์ :** (ลิงก์โปรไฟล์ของตัวเอง หลังจากอัปเดต Cupid’s Memories)  

## <:011:1335452786938089642> **แบบฟอร์ม Cupid Rings A Bell**  
-# **Cupid Rings A Bell (ขอโอกาสเดตอีกครั้ง)**  
> **ชื่อ :** (CupidCall Username)  
> **ชื่อคู่เดต :**  
> **ข้อความ :** (ข้อความถึงคู่เดต)  

## <:016:1335452798573219973> **แบบฟอร์ม Cupid Love Confession**  
-# **Cupid’s Heartfelt (ช่วงสุดท้ายของกิจกรรม)**  
> **ชื่อ :** (CupidCall Username)  
> **ชื่อคู่เดต :**  
> **ข้อความ :** (ความในใจถึงคู่เดตคนโปรด) 
"""

        thread_message = await thread.send(form_message)
        await thread_message.pin()  # ✅ ปักหมุดข้อความฟอร์ม

class LoginView(View):
    def __init__(self, bot, member, channel):
        super().__init__(timeout=120)  # ⏳ ปุ่มจะหายไปใน 120 วินาที
        self.bot = bot
        self.member = member
        self.channel = channel
        self.message = None  # บันทึกข้อความของปุ่มที่ส่งไป
        self.is_logged_in = False  # ✅ ตรวจสอบว่า Login สำเร็จหรือยัง
        self.is_timeout_handled = False  # ✅ ป้องกันการส่งปุ่มซ้ำ

    async def send(self):
        """🔄 ส่งปุ่มใหม่ไปยังห้อง (ถ้ายังไม่ Login)"""
        if self.is_logged_in:
            return  # ✅ ถ้า Login สำเร็จแล้ว ไม่ต้องส่งปุ่มใหม่

        embed = discord.Embed(
            title="<:032:1335453941340704808> Welcome to Cupid Call!",
            description=f"{self.member.mention} กรุณากดปุ่ม **LOGIN** ด้านล่างเพื่อเข้าสู่ระบบ",
            color=0xce002d
        )
        embed.set_image(url="https://i.imgur.com/frjkz97.png")

        self.message = await self.channel.send(embed=embed, view=self)

    @discord.ui.button(label="LOGIN", style=discord.ButtonStyle.danger)
    async def login(self, interaction: discord.Interaction, button: Button):
        """เมื่อกดปุ่ม Login"""
        self.is_logged_in = True  # ✅ กำหนดให้ผู้เล่น Login สำเร็จแล้ว

        if self.message:
            await self.message.edit(view=None)  # ✅ ลบปุ่มออกหลังจาก Login สำเร็จ

        await interaction.response.send_modal(LoginModal(self.bot, interaction.user, self.channel))

    async def on_timeout(self):
        """⏳ เมื่อปุ่มหมดเวลา ให้บอทส่งปุ่มใหม่ (ถ้ายังไม่ Login สำเร็จ)"""
        if self.is_logged_in or self.is_timeout_handled:
            return  # ✅ หยุดส่งปุ่มใหม่ถ้า Login สำเร็จแล้ว หรือ ปุ่มหมดเวลาไปแล้ว

        self.is_timeout_handled = True  # ✅ ป้องกันการส่งปุ่มซ้ำ

        for child in self.children:
            child.disabled = True  # ❌ ปิดปุ่มเก่า

        if self.message:
            await self.message.edit(view=self)  # ✅ อัปเดตปุ่มให้เป็นปิดใช้งานแทนการลบ

        # ✅ ส่งปุ่มใหม่อีกครั้ง (ถ้ายังไม่ Login)
        await asyncio.sleep(1)
        new_view = LoginView(self.bot, self.member, self.channel)
        await new_view.send()

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.private_channels = {}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """เมื่อสมาชิกใหม่เข้ามาในเซิร์ฟเวอร์"""
        if member.bot:
            return  # ไม่ต้องสร้างห้องให้บอท

        guild = member.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        # ถ้าไม่มีหมวดหมู่ ให้สร้างใหม่
        if category is None:
            category = await guild.create_category(CATEGORY_NAME)

        # ตั้งค่าให้สมาชิกเห็นห้องตัวเองเท่านั้น
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                create_public_threads=True,
                create_private_threads=True,
                use_external_stickers=True,
                use_external_emojis=True,
                read_message_history=True,
                manage_messages=False,
                mention_everyone=False
            )
        }

        # สร้างห้องแชทส่วนตัว
        channel_name = f"private-{member.name}"
        channel = await guild.create_text_channel(name=channel_name, category=category, overwrites=overwrites)
        self.private_channels[member.id] = channel.id

        welcome_message = f"-# {member.mention}"

        embed = discord.Embed(
            title="<:032:1335453941340704808> Welcome to Cupid Call!",
            description=f"กรุณากดปุ่ม **LOGIN** ด้านล่างเพื่อเข้าสู่ระบบ",
            color=0xce002d
        )
        embed.set_image(url="https://i.imgur.com/frjkz97.png")

        await channel.send(content=welcome_message, embed=embed, view=LoginView(self.bot, member, channel))

async def setup(bot):
    await bot.add_cog(Welcome(bot))

