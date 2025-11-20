import discord, re, asyncio
from discord import ui


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
        
        day_th = DAY_EN_TO_TH.get(date_key, date_key)
        
        for sub in subjects_list:
            name = sub.get("name")
            room = sub.get("room", "-")
            options.append(discord.SelectOption(
                label=name[:100], 
                description=f"{day_th} - ห้อง {room}",
                value=name[:100],
                emoji="🗑️"
            ))
    return options

class ConfirmDeleteView(ui.View):
    def __init__(self, db, user_id, day_key, subject_name, subject_room,original_msg):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.day_key = day_key
        self.subject_name = subject_name
        self.subject_room = subject_room
        self.original_message = original_msg

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
            await self.original_message.edit(view=new_view)
        else:
            await self.original_message.edit(content="✅ คุณลบวิชาเรียนหมดแล้ว!", view=None)
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
        time_pattern = r"^([0-1]?\d|2[0-3]):([0-5]\d)\s*-\s*([0-1]?\d|2[0-3]):([0-5]\d)$"
        if not re.match(time_pattern, time):
            await interaction.response.send_message(
                "❌ **รูปแบบเวลาไม่ถูกต้อง**\nกรุณาใช้รูปแบบ `HH:MM` หรือ `HH:MM-HH:MM` (เช่น 09:00-12:00)", 
                ephemeral=True
            )
            return

        room_final=""
        if room:
            room_pattern = r"^\d{0,2}-\d{3,5}$"
            if not re.match(room_pattern, room):
                await interaction.response.send_message(
                    "❌ **รหัสห้องไม่ถูกต้อง**\nกรุณาใช้รูปแบบเช่น `72-405`(ตัวเลข 0-2 หลัก - ตัวเลข 3-5 หลัก)",
                    ephemeral=True
                )
                return
            room_final = room
        else:
            room_final = "ไม่ระบุ"


        new_class = {
            "name": subject,
            "time": time,
            "room": room_final
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
        modal = AddClassModal(self.db_collection, selected_day_th)
        # Generate new dropdown
        new_selector = DaySelect(self.db_collection)
        new_view = AddClassView(interaction.user,self.db_collection,new_selector)
        await interaction.response.send_modal(modal)
        await asyncio.sleep(0.5)
        await interaction.message.edit(view=new_view)

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
                subject_room=target_subject.get("room"),
                original_msg=interaction.message
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
