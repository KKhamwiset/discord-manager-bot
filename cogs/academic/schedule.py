# cogs/academic/schedule.py

import os
import re
import discord
from discord import ui
from discord.ext import commands


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
DAY_EN_TO_TH = {en: th for th, en in DAYS_TH_EN}
DAY_TH_LOWER_TO_EN = {th.lower(): en for th, en in DAYS_TH_EN}
DAY_LOWER_TH_TO_TH = {th.lower(): th for th, en in DAYS_TH_EN}
# --------------------------------------------------

async def generate_delete_options(db, user_id):
    doc = await db.find_one({"user_id": user_id})
    if not doc:
        return []

    options = []
    for date_key, subjects_list in doc.items():
        if date_key in ["_id", "user_id"] or not subjects_list: continue
        
        # Convert "Monday" -> "จันทร์"
        day_th = DAY_EN_TO_TH.get(date_key, date_key)
        
        for sub in subjects_list:
            name = sub.get("name")
            room = sub.get("room", "-")
            # Create Option
            options.append(discord.SelectOption(
                label=name[:100], 
                description=f"{day_th} - ห้อง {room}",
                value=name[:100],
                emoji="🗑️"
            ))
    return options

class ConfirmDeleteView(ui.View):
    def __init__(self, db, user_id, day_key, subject_name, subject_room):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.day_key = day_key
        self.subject_name = subject_name
        self.subject_room = subject_room

    @ui.button(label="ยืนยันลบ", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await self.db.update_one(
            {"user_id": self.user_id},
            {"$pull": {self.day_key: {"name": self.subject_name}}}
        )
        
        await interaction.response.edit_message(
            content=f"✅ ลบวิชา **{self.subject_name}** (วัน{DAY_EN_TO_TH.get(self.day_key, self.day_key)}) เรียบร้อยแล้ว!",
            view=None
        )
        new_options = await generate_delete_options(self.db, self.user_id)
        if new_options:
            new_selector = SubjectSelect(self.db, interaction.user, new_options[:25])
            new_view = AddClassView(interaction.user, self.db, new_selector)
            await self.original_msg.edit(view=new_view)
        else:
            await self.original_msg.edit(content="✅ คุณลบวิชาเรียนหมดแล้ว!", view=None)
        self.stop()

    @ui.button(label="ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="❌ ยกเลิกการลบแล้ว", view=None)
        self.value = False
        self.stop()

class AddClassModal(ui.Modal, title="เพิ่มวิชาในตารางเรียน"):
    time_input = ui.TextInput(
        label="ช่วงเวลา (เช่น 09:00-12:00)", 
        placeholder="09:00-12:00", 
        required=True,
        max_length=20
    )
    subject_input = ui.TextInput(
        label="ชื่อวิชา หรือ รหัสวิชา", 
        placeholder="GEN101 General Physics", 
        required=True,
        max_length=100
    )
    room_input = ui.TextInput(
        label="ห้องเรียน (ระบุหรือไม่ก็ได้)", 
        placeholder="72-405", 
        required=False,
        max_length=50
    )

    def __init__(self, db_collection, selected_day_th: str):
        super().__init__()
        self.db_collection = db_collection
        self.selected_day_th = selected_day_th

    async def on_submit(self, interaction: discord.Interaction):
        day_en = DAY_TH_TO_EN.get(self.selected_day_th)
        if not day_en:
            await interaction.response.send_message("❌ เกิดข้อผิดพลาดเกี่ยวกับวัน", ephemeral=True)
            return


        time = self.time_input.value.strip()
        subject_raw = self.subject_input.value
        subject = re.sub(r"\s+", " ", subject_raw.strip())
        room = self.room_input.value.strip() or "ไม่ระบุ"


        new_class = {
            "name": subject,
            "time": time,
            "room": room
        }

        await self.db_collection.update_one(
            {"user_id": interaction.user.id},
            {"$push": {day_en: new_class}},
            upsert=True
        )

        await interaction.response.send_message(
            f"✅ บันทึกวิชา **{subject}** \n🗓️ วัน**{self.selected_day_th}** เวลา `{time}` ห้อง `{room}`",
            ephemeral=True
        )

class DaySelect(ui.Select):
    def __init__(self, db):
        self.db_collection = db
        options = [
            discord.SelectOption(label=f"{th}", value=th, emoji="🗓️")
            for th, en in DAYS_TH_EN
        ]
        super().__init__(
            placeholder="เลือกวันที่จะเรียน...",
            min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_day_th = self.values[0]
        # เปิด Modal ใหม่ที่แก้แล้ว
        modal = AddClassModal(self.db_collection, selected_day_th)
        await interaction.response.send_modal(modal)

class SubjectSelect(ui.Select):
    def __init__(self, db, author, options):
        self.db_collection = db
        self.author = author
        super().__init__(
            placeholder="เลือกวิชาที่จะลบ...",
            min_values=1, max_values=1, options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        doc = await self.db_collection.find_one({"user_id": self.author.id})
        if not doc:
            await interaction.response.send_message("❌ ไม่พบข้อมูล", ephemeral=True)
            return

        target_subject = None
        target_day_key = None
        for date, subjects in doc.items():
            if date in ["_id", "user_id"]: continue
            for sub in subjects:
                if sub.get("name") == selected_value:
                    target_subject = sub
                    target_day_key = date
                    break
            if target_subject: break
        
        if target_subject:
            view = ConfirmDeleteView(
                db=self.db_collection,
                user_id=self.author.id,
                day_key=target_day_key,
                subject_name=target_subject.get("name"),
                subject_room=target_subject.get("room")
            )
            await interaction.response.send_message(
                f"⚠️ **ยืนยันการลบ?**\nคุณต้องการลบวิชา **{target_subject.get('name')}** (วัน{DAY_EN_TO_TH.get(target_day_key, target_day_key)}) ใช่หรือไม่?", 
                view=view, 
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ หาวิชาไม่เจอ (อาจถูกลบไปแล้ว)", ephemeral=True)

# --------------------------------------------------
# Main View
# --------------------------------------------------
class AddClassView(ui.View):
    def __init__(self, author: discord.Member, db_collection, Selector: ui.Select):
        super().__init__(timeout=180)
        self.author = author
        self.db_collection = db_collection
        self.add_item(Selector)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("ปุ่มนี้ไม่ใช่ของคุณนะ!", ephemeral=True)
            return False
        return True

# --------------------------------------------------
#Cog Logic
# --------------------------------------------------
class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            if self.db is not None:
                print("✅ Schedule Cog connection, OK.")
        except Exception as e:
            print(f"❌ Schedule Cog connection failed: {e}")

    @property
    def db(self):
        return self.bot.db["schedules"]

    @commands.command(name="addclass", aliases=["asch", "ac"])
    async def add_class_interactive(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        
        
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=DaySelect(self.db))
        await ctx.send("เลือกวันเรียนเพื่อเพิ่มวิชา 👇", view=view)


    @commands.command(name="myschedule", aliases=["msch", "mc"])
    async def my_schedule(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")

        doc = await self.db.find_one({"user_id": ctx.author.id})
        
        if not doc:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียนนะ! ลองใช้ `baddclass` ดูสิ")
            return

        embed = discord.Embed(
            title=f"📅 ตารางเรียนของ {ctx.author.display_name}",
            color=discord.Color.teal(),
        )

        has_data = False
        for day_th, day_en in DAYS_TH_EN:
            subjects = doc.get(day_en, [])
            
            if subjects:
                has_data = True
                subjects_sorted = sorted(subjects, key=lambda x: x.get("time", "00:00"))
                
                lines = []
                for sub in subjects_sorted:
                    t = sub.get("time", "-")
                    n = sub.get("name", "???")
                    r = sub.get("room", "")
                    room_txt = f" (ห้อง **{r}**)" if r and r != "ไม่ระบุ" else ""
                    lines.append(f"`{t}` **{n}**{room_txt}")
                
                embed.add_field(name=f"🗓️ {day_th}", value="\n".join(lines), inline=False)

        if not has_data:
             await ctx.send("🤔 คุณมีชื่อในระบบ แต่ยังไม่ได้เพิ่มวิชาเรียนเลย")
        else:
             await ctx.send(embed=embed)

    @commands.command(name="delclass", aliases=["delsch", "dc"])
    async def delete_class(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        
        doc = await self.db.find_one({"user_id" : ctx.author.id})
        if not doc:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียน")
            return
            
        options = await generate_delete_options(self.db,ctx.author.id)
        
        if not options:
            await ctx.send("🤔 ตารางเรียนว่างเปล่า")
            return

        selector = SubjectSelect(self.db, ctx.author, options[:25])
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=selector)

        await ctx.send("เลือกรายวิชาที่ต้องการจะลบ 👇", view=view)

async def setup(bot):
    await bot.add_cog(Schedule(bot))