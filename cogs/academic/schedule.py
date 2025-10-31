# cogs/academic/schedule.py

import os
import re
import discord
from discord import ui
from discord.ext import commands
import pymongo
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# --------------------------
# ค่าคงที่: รายชื่อวัน ไทย/อังกฤษ
# --------------------------
DAYS_TH_EN = [
    ("จันทร์", "Mon"),
    ("อังคาร", "Tue"),
    ("พุธ", "Wed"),
    ("พฤหัสบดี", "Thu"),
    ("ศุกร์", "Fri"),
    ("เสาร์", "Sat"),
    ("อาทิตย์", "Sun"),
]
DAYS_ORDER_TH = [d[0] for d in DAYS_TH_EN]
DAY_TH_TO_EN = {th: en for th, en in DAYS_TH_EN}
DAY_TH_LOWER_TO_EN = {th.lower(): en for th, en in DAYS_TH_EN}

# --------------------------
# Modal 2 ช่อง (เวลา + วิชา)
# วันรับมาจาก dropdown
# --------------------------
class TwoFieldModal(ui.Modal, title="เพิ่มวิชาในตารางเรียน"):
    time_input = ui.TextInput(
        label="ช่วงเวลา (เช่น 09:00-12:00)", placeholder="09:00-12:00", required=True
    )
    subject_input = ui.TextInput(
        label="ชื่อวิชา หรือ รหัสวิชา", placeholder="GEN101 General Physics", required=True
    )

    def __init__(self, db_collection, selected_day_th: str):
        super().__init__()
        self.db_collection = db_collection
        self.selected_day_th = selected_day_th  # จาก dropdown

    async def on_submit(self, interaction: discord.Interaction):
        day_th = self.selected_day_th
        day_en = DAY_TH_TO_EN.get(day_th, "")
        time = self.time_input.value
        subject = self.subject_input.value

        schedule_data = {
            "user_id": interaction.user.id,
            # เก็บทั้งฟิลด์ใหม่และฟิลด์เดิม เพื่อไม่พังกับข้อมูลเก่า
            "day_th": day_th,
            "day_en": day_en,
            "day": day_th.lower(),  # legacy (เดิมเก็บไทยตัวเล็ก)
            "time": time,
            "subject": subject,
        }
        self.db_collection.insert_one(schedule_data)

        label_day = f"{day_th} ({day_en})" if day_en else day_th
        await interaction.response.send_message(
            f"✅ บันทึกวิชา **{subject}** ในวัน **{label_day}** เรียบร้อยแล้ว!",
            ephemeral=True
        )

# --------------------------
# Dropdown ให้เลือกวัน
# --------------------------
class DaySelect(ui.Select):
    def __init__(self, db_collection):
        options = [
            discord.SelectOption(label=f"{th} ({en})", value=th, emoji="🗓️")
            for th, en in DAYS_TH_EN
        ]
        super().__init__(
            placeholder="เลือกวันของคาบเรียน…",
            min_values=1, max_values=1, options=options
        )
        self.db_collection = db_collection

    async def callback(self, interaction: discord.Interaction):
        selected_day_th = self.values[0]
        # เปิด Modal ที่เหลือ (เวลา + วิชา) โดยส่งวันเข้าไป
        modal = TwoFieldModal(self.db_collection, selected_day_th)
        await interaction.response.send_modal(modal)

# --------------------------
# View หลัก: ใส่ Dropdown อย่างเดียว
# --------------------------
class AddClassView(ui.View):
    def __init__(self, author: discord.Member, db_collection):
        super().__init__(timeout=180)
        self.author = author
        self.db_collection = db_collection
        self.add_item(DaySelect(self.db_collection))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("ปุ่มนี้ไม่ใช่ของคุณนะ!", ephemeral=True)
            return False
        return True

# --------------------------
# Helper: แปลง key จัดกลุ่มวัน & sort เวลา
# --------------------------
def normalize_day_key(item):
    """
    รับเอกสาร 1 ตัวจาก Mongo แล้วคืนวันภาษาไทย (สำหรับใช้เป็น key) ให้คงรูปแบบเดียว
    """
    # รองรับทั้งเอกสารใหม่ (day_th) และเก่า (day=ไทยตัวเล็ก)
    if "day_th" in item:
        return item["day_th"]
    d = item.get("day", "")
    # แปลงเป็นชื่อไทยปกติ (ตัวพิมพ์เดิม)
    for th in DAY_TH_TO_EN:
        if d == th or d == th.lower():
            return th
    return d  # ถ้าไม่รู้จัก ก็คืนค่าดิบ (จะไปอยู่กลุ่ม "อื่นๆ")

def get_day_label_th_en(day_th: str) -> str:
    en = DAY_TH_TO_EN.get(day_th, "")
    return f"{day_th} ({en})" if en else day_th

def time_sort_key(time_range: str):
    """
    รับสตริงเวลาเช่น '09:00-12:00' แล้วคืน key สำหรับ sort (ใช้เวลาเริ่ม)
    """
    if not isinstance(time_range, str):
        return "00:00"
    parts = time_range.split("-")
    start = parts[0].strip() if parts else time_range.strip()
    # บังคับรูปแบบ HH:MM ให้ปลอดภัย
    # ถ้าไม่ใช่รูปแบบมาตรฐาน จะตกมา default '00:00'
    return start if re.match(r"^\d{1,2}:\d{2}$", start) else "00:00"

# --------------------------
# Cog หลัก
# --------------------------
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

    @commands.command(name="addclass", aliases=["asch", "ac"])
    async def add_class_interactive(self, ctx: commands.Context):
        """
        เปิด View ให้เลือกวัน (ไทย + อังกฤษในวงเล็บ) แล้วตามด้วย Modal รับช่วงเวลา/ชื่อวิชา
        """
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        view = AddClassView(author=ctx.author, db_collection=self.collection)
        await ctx.send("เลือกวันจากเมนูด้านล่าง แล้วระบบจะถามช่วงเวลาและชื่อวิชาต่อให้จบในขั้นตอนเดียว 👇", view=view)

    @commands.command(name="myschedule", aliases=["mysch", "sch"])
    async def my_schedule(self, ctx: commands.Context):
        """
        แสดงตารางเรียนของผู้ใช้ โดยหัวข้อวันจะแสดงเป็น ไทย + อังกฤษในวงเล็บ เช่น 'จันทร์ (Mon)'
        """
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        user_schedules = self.collection.find({"user_id": ctx.author.id})

        schedule_by_day = {}
        for item in user_schedules:
            day_th = normalize_day_key(item)  # คืนชื่อวันภาษาไทย
            schedule_by_day.setdefault(day_th, []).append(item)

        if not schedule_by_day:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียนนะ! ลองใช้ `baddclass` เพื่อเพิ่มวิชาเรียนสิ")
            return

        embed = discord.Embed(
            title=f"📅 ตารางเรียนของ {ctx.author.display_name}",
            color=discord.Color.teal(),
        )

        # แสดงตามลำดับวันมาตรฐาน
        for day_th in DAYS_ORDER_TH:
            if day_th in schedule_by_day:
                items = schedule_by_day[day_th]
                # sort ตามเวลาเริ่ม
                items_sorted = sorted(items, key=lambda x: time_sort_key(x.get("time", "")))

                day_info_lines = []
                for s in items_sorted:
                    # แสดงเวลา + ชื่อวิชา
                    t = s.get("time", "-")
                    subj = s.get("subject", "(ไม่ระบุชื่อวิชา)")
                    day_info_lines.append(f"`{t}` - **{subj}**")

                embed.add_field(
                    name=f"🗓️ {get_day_label_th_en(day_th)}",
                    value="\n".join(day_info_lines) if day_info_lines else "—",
                    inline=False
                )

        # กรณีมีวันอื่นๆ ที่ไม่อยู่ในรายการ (ข้อมูลเก่า/สะกดแปลก)
        others = [k for k in schedule_by_day.keys() if k not in DAYS_ORDER_TH]
        for day_th in others:
            items = schedule_by_day[day_th]
            items_sorted = sorted(items, key=lambda x: time_sort_key(x.get("time", "")))
            day_info_lines = [f"`{s.get('time','-')}` - **{s.get('subject','(ไม่ระบุชื่อวิชา)')}**" for s in items_sorted]
            embed.add_field(
                name=f"🗓️ {get_day_label_th_en(day_th)}",
                value="\n".join(day_info_lines) if day_info_lines else "—",
                inline=False
            )

        await ctx.send(embed=embed)


    # --- โค้ด delclass (ปรับปรุงให้รับชื่อเว้นวรรคได้) ---


    @commands.command(name="delclass", aliases=["dsch", "dc"])
    async def delete_class(self, ctx, *, subject_to_delete: str):
        """
        ลบวิชาออกจากตารางเรียนของผู้ใช้
        รองรับชื่อวิชาที่มีการเว้นวรรค
        ตัวอย่าง: !delclass GEN101 General Physics
        """
        if not self.client:
            await ctx.send("❌ ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return

        # ปรับรูปแบบชื่อวิชาให้คงที่: ตัดช่องว่างหัวท้ายและยุบหลายช่องว่าง
        normalized = re.sub(r"\s+", " ", subject_to_delete.strip())

        result = self.collection.delete_many({
            "user_id": ctx.author.id,
            "subject": {
                "$regex": f"^{re.escape(normalized)}$",
                "$options": "i"
            }
        })

        if result.deleted_count > 0:
            await ctx.send(f"✅ **ลบสำเร็จ!** วิชา **{normalized}** ถูกลบ {result.deleted_count} รายการ")
        else:
            await ctx.send(f"🤔 **ไม่พบข้อมูล** วิชา **{normalized}** ในตารางเรียนของคุณ")

async def setup(bot):
    await bot.add_cog(Schedule(bot))
