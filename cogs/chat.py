import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import random

CATEGORY_NAME = "୨୧ Private Room"
ADMIN_CHANNEL_ID = 1336725273827082291  # ID ห้องแอดมินที่ใช้แจ้งเตือน
DEFAULT_AVATAR = "https://i.imgur.com/d1ReGAn.png"  # รูป Default Avatar
ADMIN_ROLE_ID = 1337076552172703775  # Role ID ของแอดมิน


class ConfirmChatView(discord.ui.View):
    """ปุ่มยืนยัน/ยกเลิกการส่งข้อความ"""

    def __init__(self, bot, sender_username, sender_avatar, recipient, recipient_id, message, preview_message):
        super().__init__(timeout=60)
        self.bot = bot
        self.sender_username = sender_username
        self.sender_avatar = sender_avatar
        self.recipient = recipient
        self.recipient_id = recipient_id
        self.message = message
        self.preview_message = preview_message

    @discord.ui.button(label="✅ ยืนยัน", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ส่งข้อความไปยังห้องของผู้รับ"""
        await interaction.response.defer()

        # 📜 ดึงข้อมูลห้องของผู้รับจากฐานข้อมูล
        channel_id = await self.bot.db.get_channel_id(self.recipient)

        if not channel_id:
            await interaction.followup.send(f"❌ ไม่พบห้องของ `{self.recipient}` ในระบบ!", ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            await interaction.followup.send(f"❌ ไม่พบห้องของ `{self.recipient}` ในเซิร์ฟเวอร์!", ephemeral=True)
            return

        # 📜 ตรวจสอบว่าเป็น Cupid Operator หรือไม่
        recipient_mention = f"<@{self.recipient_id}>" if self.recipient != "Cupid Operator" else f"<@&{ADMIN_ROLE_ID}>"

        # 📜 สร้าง Embed สำหรับส่งข้อความ
        embed = discord.Embed(
            title=f"{self.sender_username} said :",
            description=f"```{self.message}```",
            color=0xf8a5c2,
        )
        embed.set_footer(
            text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
            icon_url="https://i.imgur.com/9XHzoAJ.png"
        )
        embed.set_author(
            name="คุณได้รับข้อความใหม่",
            icon_url="https://cdn.discordapp.com/emojis/1335452788930379910.png?size=96&quality=lossless"
        )
        embed.set_thumbnail(url=self.sender_avatar)

        await channel.send(content=recipient_mention, embed=embed)

        # 📜 แจ้งเตือนแอดมิน
        admin_channel = interaction.guild.get_channel(ADMIN_CHANNEL_ID)
        if admin_channel:
            admin_embed = discord.Embed(
                title="<:012:1335452788930379910> มีการส่งข้อความใหม่!",
                description="\u200b",
                color=0xce002d,
            )
            admin_embed.add_field(
                name=f"**`{self.sender_username}`** ส่งข้อความถึง `{self.recipient}`",
                value=f"```{self.message}```",
                inline=False
            )
            admin_embed.set_footer(
                text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
                icon_url="https://i.imgur.com/9XHzoAJ.png"
            )
            admin_embed.set_thumbnail(url=self.sender_avatar)

            await admin_channel.send(embed=admin_embed)

        # ✅ อัปเดต Embed ตัวอย่างให้แสดงว่า "ส่งข้อความสำเร็จ!"
        success_embed = self.preview_message.embeds[0]
        success_embed.add_field(
            name="\u200b",
            value=f"<a:babypinkcheck:1336305497682481152> **ข้อความส่งถึง `{self.recipient}` แล้ว!**",
            inline=False
        )
        success_embed.color = 0xf8a5c2

        await self.preview_message.edit(embed=success_embed, view=None)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        """ยกเลิกการส่งข้อความ"""
        await interaction.response.defer()
        await interaction.delete_original_response()


class Chat(commands.Cog):
    """คำสั่ง /chat ส่งข้อความหากันผ่านบอท"""

    def __init__(self, bot):
        self.bot = bot

    async def username_autocomplete(self, interaction: discord.Interaction, current: str):
        """🔎 Autocomplete: แสดงรายชื่อจากฐานข้อมูล"""
        try:
            users_data = await self.bot.db.get_all_user_data()

            if not users_data:
                return []

            users = [(user[0], user[1], user[2] if len(user) > 2 else 0) for user in users_data]

            user_data = await self.bot.db.get_user_data(interaction.user.id)
            my_username = user_data[0] if user_data else None

            filtered_users = [
                (username, display_name, is_admin)
                for username, display_name, is_admin in users
                if username.lower() != my_username.lower()
            ] if my_username else users

            final_users = []
            added_cupid_operator = False

            for username, display_name, is_admin in filtered_users:
                if is_admin:
                    if not added_cupid_operator:
                        final_users.append("Cupid Operator")
                        added_cupid_operator = True
                else:
                    final_users.append(username)

            matching_users = [name for name in final_users if current.lower() in name.lower()]
            return [app_commands.Choice(name=name, value=name) for name in matching_users[:5]]

        except Exception as e:
            print(f"❌ Error in autocomplete: {e}")
            return []

    @app_commands.command(name="chat", description="ส่งข้อความส่วนตัว")
    @app_commands.autocomplete(recipient=username_autocomplete)
    async def chat(self, interaction: discord.Interaction, recipient: str, message: str):
        """ให้ผู้ใช้ส่งข้อความถึงกันผ่านบอทโดยใช้ Username"""

        await interaction.response.defer()

        recipient_id = None

        if recipient == "Cupid Operator":
            admins = await self.bot.db.get_all_admins()
            if not admins:
                await interaction.followup.send("❌ ไม่มีแอดมินออนไลน์ในขณะนี้!", ephemeral=True)
                return

            selected_admin = random.choice(admins)
            recipient_id = selected_admin[1]
            recipient = "Cupid Operator"

        else:
            recipient_id = await self.bot.db.get_user_id(recipient)

        if not recipient_id:
            await interaction.followup.send(f"❌ ไม่พบข้อมูลของ `{recipient}` ในระบบ!", ephemeral=True)
            return

        sender_data = await self.bot.db.get_user_data(interaction.user.id)

        if not sender_data:
            await interaction.followup.send("❌ ไม่พบข้อมูลของคุณในระบบ!", ephemeral=True)
            return

        sender_username, sender_avatar, is_admin = sender_data

        if is_admin:
            sender_username = "Cupid Operator"

        # ✅ แก้ไขปัญหา Indentation ของ DEFAULT_AVATAR
        if not sender_avatar:
            sender_avatar = DEFAULT_AVATAR

        # ✅ สร้าง Embed ตัวอย่างก่อนส่ง
        preview_embed = discord.Embed(
            title=f"{sender_username} said :",
            description=f"```{message}```",
            color=0xdfe6e9,
        )
        preview_embed.set_footer(
            text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
            icon_url="https://i.imgur.com/9XHzoAJ.png"
        )
        preview_embed.set_author(
            name=f'ส่งข้อความถึง {recipient}',
            icon_url="https://cdn.discordapp.com/emojis/1335452788930379910.png?size=96&quality=lossless"
        )
        preview_embed.set_thumbnail(url=sender_avatar)  # ✅ ใส่รูปของผู้ส่งแน่ๆ

        # ✅ ส่งข้อความตัวอย่างและรับ preview_message
        preview_message = await interaction.followup.send(embed=preview_embed, ephemeral=False)

        # ✅ เพิ่มปุ่มยืนยันหลังจากส่ง Embed ตัวอย่าง
        view = ConfirmChatView(self.bot, sender_username, sender_avatar, recipient, recipient_id, message,
                               preview_message)
        await preview_message.edit(view=view)

async def setup(bot):
    await bot.add_cog(Chat(bot))
