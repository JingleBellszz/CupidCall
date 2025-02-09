import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

ADMIN_ID = 1335448682669015122
CATEGORY_NAME = "୨୧ Private Room"


class ConfirmBroadcastView(discord.ui.View):
    """ปุ่มยืนยัน/ยกเลิกการส่งข้อความ"""

    def __init__(self, bot: commands.Bot, embed: discord.Embed):
        super().__init__(timeout=60)
        self.bot = bot
        self.embed = embed

    @discord.ui.button(label="✅ ยืนยัน", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ส่ง Embed ไปยังทุกห้องในหมวดหมู่ Private Room"""
        await interaction.response.defer()  # ✅ ป้องกัน Timeout

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        if not category:
            await interaction.followup.send(f"⚠️ หมวดหมู่ `{CATEGORY_NAME}` ไม่พบ!", ephemeral=True)
            return

        for channel in category.text_channels:
            await channel.send(embed=self.embed)

        await interaction.followup.send("✅ ส่งข้อความสำเร็จ!", ephemeral=True)
        await interaction.message.edit(view=None)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ยกเลิกการส่งข้อความ"""
        await interaction.response.edit_message(content="❌ ยกเลิกการส่งข้อความ", view=None)


class Admin(commands.Cog):
    """คำสั่งสำหรับแอดมิน"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="all", description="ส่งข้อความไปยังทุก Private Chatroom (Admin เท่านั้น)")
    async def send_to_all(self, interaction: discord.Interaction, title: str, description: str):
        """ให้แอดมินส่ง Embed ไปยังห้องทั้งหมดในหมวดหมู่ '୨୧ Private Room'"""
        await interaction.response.defer(ephemeral=True)  # ✅ ป้องกัน Timeout

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        if not category:
            await interaction.followup.send(f"⚠️ หมวดหมู่ `{CATEGORY_NAME}` ไม่พบ!", ephemeral=True)
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=0xce002d
        )
        embed.set_author(
            name="คุณได้รับข้อความใหม่",
            icon_url="https://cdn.discordapp.com/emojis/1335452788930379910.png?size=96&quality=lossless"
        )
        embed.set_footer(
            text=f"CupidCall.rp.th • {datetime.now().strftime('%d/%m/%Y')}",
            icon_url="https://i.imgur.com/81RQdUl.png"
        )

        bot_avatar = interaction.client.user.avatar.url if interaction.client.user.avatar else None
        if bot_avatar:
            embed.set_thumbnail(url=bot_avatar)

        view = ConfirmBroadcastView(self.bot, embed)
        await interaction.followup.send(
            content="🔹 **ตรวจสอบข้อความก่อนส่ง:**",
            embed=embed,
            view=view,
            ephemeral=True
        )

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="announce",
                          description="ส่งข้อความจาก Message ID ไปยังทุกห้องในหมวดหมู่ (Admin เท่านั้น)")
    async def announce(self, interaction: discord.Interaction, message_id: str):
        """ให้บอทคัดลอกข้อความจาก Message ID แล้วประกาศไปทุกห้อง"""
        await interaction.response.defer(ephemeral=True)  # ✅ ป้องกัน Timeout

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)

        if not category:
            await interaction.followup.send(f"⚠️ หมวดหมู่ `{CATEGORY_NAME}` ไม่พบ!", ephemeral=True)
            return

        message = None
        for channel in guild.text_channels:
            try:
                message = await channel.fetch_message(int(message_id))
                break
            except (discord.NotFound, discord.Forbidden):
                continue

        if message is None:
            await interaction.followup.send("❌ ไม่พบข้อความ กรุณาตรวจสอบ Message ID!", ephemeral=True)
            return

        sent_channels = []
        for channel in category.text_channels:
            try:
                owner = None
                for member in guild.members:
                    if channel.overwrites_for(member).view_channel:
                        if not member.guild_permissions.administrator:
                            owner = member
                            break

                mention = owner.mention if owner else ""

                await channel.send(f"{mention}\n{message.content}")
                sent_channels.append(channel.name)
            except discord.Forbidden:
                continue

        await interaction.followup.send(
            f"✅ ส่งข้อความจาก `{message_id}` ไปยัง {len(sent_channels)} ห้องสำเร็จ!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Admin(bot))
