# cogs/academic/schedule.py

import os
import discord
from discord import ui
from discord.ext import commands
import pymongo
#from dotenv import load_dotenv

#load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")


# --- ส่วนที่ 1: สร้าง Modal ที่มีทุก Field ในหน้าต่างเดียว ---
class SingleScheduleModal(ui.Modal, title="เพิ่มวิชาในตารางเรียน"):
    day_input = ui.TextInput(
        label="วัน (เช่น จันทร์, อังคาร)", placeholder="จันทร์", required=True
    )
    time_input = ui.TextInput(
        label="ช่วงเวลา (เช่น 09:00-12:00)", placeholder="09:00-12:00", required=True
    )
    subject_input = ui.TextInput(
        label="ชื่อวิชา หรือ รหัสวิชา", placeholder="GEN101 General Physics", required=True
    )

    def __init__(self, db_collection):
        super().__init__()
        self.db_collection = db_collection

    async def on_submit(self, interaction: discord.Interaction):
        day = self.day_input.value
        time = self.time_input.value
        subject = self.subject_input.value

        schedule_data = {
            "user_id": interaction.user.id,
            "day": day.lower(),
            "time": time,
            "subject": subject,
        }
        self.db_collection.insert_one(schedule_data)

        await interaction.response.send_message(
            f"✅ บันทึกวิชา **{subject}** ในวัน **{day}** เรียบร้อยแล้ว!", ephemeral=True
        )


# --- ส่วนที่ 2: สร้าง View ที่มีแค่ปุ่มเดียวสำหรับเรียก Modal ---
class AddClassView(ui.View):
    def __init__(self, author: discord.Member, db_collection):
        super().__init__(timeout=180)
        self.author = author
        self.db_collection = db_collection

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("ปุ่มนี้ไม่ใช่ของคุณนะ!", ephemeral=True)
            return False
        return True

    @ui.button(label="➕ เพิ่มตารางเรียน", style=discord.ButtonStyle.primary)
    async def add_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = SingleScheduleModal(self.db_collection)
        await interaction.response.send_modal(modal)

        self.stop()
        button.disabled = True
        await interaction.edit_original_response(view=self)


# --- ส่วนที่ 3: Cog หลัก (ที่มีครบทุกคำสั่ง) ---
class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.client = pymongo.MongoClient(MONGO_URI)
            self.db = self.client["discord_bot_db"]
            self.collection = self.db["schedules"]
            print("✅ MongoDB connection successful for Schedule Cog.")
        except pymongo.errors.ConfigurationError:
            print("❌ MongoDB connection failed. Check your MONGO_URI.")
            self.client = None

    @commands.command(name="addclass")
    async def add_class_interactive(self, ctx: commands.Context):
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        view = AddClassView(author=ctx.author, db_collection=self.collection)
        await ctx.send("กดปุ่มด้านล่างเพื่อเริ่มกรอกข้อมูลตารางเรียนได้เลย!", view=view)

    @commands.command(name="myschedule")
    async def my_schedule(self, ctx: commands.Context):
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        user_schedules = self.collection.find({"user_id": ctx.author.id})

        schedule_by_day = {}
        for item in user_schedules:
            day = item["day"].capitalize()
            if day not in schedule_by_day:
                schedule_by_day[day] = []
            schedule_by_day[day].append(item)

        if not schedule_by_day:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียนนะ! ลองใช้ `baddclass` เพื่อเพิ่มวิชาเรียนสิ")
            return

        embed = discord.Embed(
            title=f"📅 ตารางเรียนของ {ctx.author.display_name}",
            color=discord.Color.teal(),
        )
        days_order = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

        for day in days_order:
            if day in schedule_by_day:
                day_info = ""
                for s in sorted(schedule_by_day[day], key=lambda x: x["time"]):
                    day_info += f"`{s['time']}` - **{s['subject']}**\n"

                embed.add_field(name=f"🗓️ {day}", value=day_info, inline=False)

        await ctx.send(embed=embed)

    # --- โค้ด delclass (ปรับปรุงให้รับชื่อเว้นวรรคได้) ---


    @commands.command(name="delclass")
    async def delete_class(self, ctx, *, subject_to_delete: str):
            """
            ลบวิชาออกจากตารางเรียนของผู้ใช้
            รองรับชื่อวิชาที่มีการเว้นวรรค
            ตัวอย่าง: !delclass GEN101 General Physics
            """
            if not self.client:
                await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
                return

            result = self.collection.delete_one(
            {"user_id": ctx.author.id, "subject": subject_to_delete}
    )

            # ตรวจสอบว่าลบสำเร็จหรือไม่
            if result.deleted_count > 0:
            # ถ้าลบสำเร็จ (deleted_count มากกว่า 0)
                await ctx.send(
                    f"✅ **ลบสำเร็จ!** วิชา **{subject_to_delete}** ถูกนำออกจากตารางเรียนแล้ว"
                )
            else:
            # ถ้าไม่พบข้อมูลที่จะลบ
                await ctx.send(f"🤔 **ไม่พบข้อมูล**วิชา **{subject_to_delete}** ในตารางเรียนของคุณ")


async def setup(bot):
    await bot.add_cog(Schedule(bot))
