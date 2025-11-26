import discord, re, asyncio
from discord import ui

# --- Configuration ---
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

async def _validate_time_room(interaction: discord.Interaction, time: str, room: str) -> tuple[str, str] | None:
    time_pattern = r"^([0-1]?\d|2[0-3]):([0-5]\d)\s*-\s*([0-1]?\d|2[0-3]):([0-5]\d)$"
    if not re.match(time_pattern, time):
        await interaction.response.send_message(
            "❌ **รูปแบบเวลาไม่ถูกต้อง**\nกรุณาใช้รูปแบบ `HH:MM-HH:MM` (เช่น 09:00-12:00)", 
            ephemeral=True
        )
        return None

    room_final = "ไม่ระบุ"
    if room and room != "ไม่ระบุ":
        room_pattern = r"(^\d{0,2}-\d{3,5}$)|^-$"
        if not re.match(room_pattern, room):
            await interaction.response.send_message(
                "❌ **รหัสห้องไม่ถูกต้อง**\nกรุณาใช้รูปแบบเช่น `72-405`(ตัวเลข 0-2 หลัก - ตัวเลข 3-5 หลัก)\nหรือ - หากไม่มีห้องเรียน",
                ephemeral=True
            )
            return None
        room_final = room
        
    return time, room_final

async def generate_options(db, user_id):
    doc = await db.find_one({"user_id": user_id})
    if not doc:
        return []

    options = []
    for date_key, subjects_list in doc.items():
        if date_key in ["_id", "user_id"] or not subjects_list: continue
        
        day_th = DAY_EN_TO_TH.get(date_key, date_key)
        
        for sub in subjects_list:
            name = sub.get("name")
            room = sub.get("room", "ไม่ระบุ")
            value_id = f"{date_key}-{name}"
            
            options.append(discord.SelectOption(
                label=name[:100], 
                description=f"{day_th} - ห้อง {room}",
                value=value_id[:100],
                emoji="📚"
            ))
    return options

async def _regenerate_view(db_collection, user, original_msg, SelectorClass):
    new_options = await generate_options(db_collection, user.id)
    
    if new_options:
        new_selector = SelectorClass(db_collection, user, options=new_options[:25]) 
        new_view = AddClassView(user, db_collection, new_selector)
        await original_msg.edit(view=new_view)
    else:
        await original_msg.edit(content="✅ คุณจัดการวิชาเรียนหมดแล้ว!", view=None)

class EditInfoModal(ui.Modal,title="แก้ไขข้อมูลรายวิชา"):
    
    def __init__(self,db_collection,time_,subject_,room_,date_,prof_,original_msg):
        super().__init__()
        self.db_collection = db_collection
        self.time = time_
        self.subject = subject_ 
        self.room = room_
        self.date = date_
        self.prof = prof_
        self.original_msg = original_msg

        time_input = ui.TextInput(
            label="ช่วงเวลา (เช่น 09:00-12:00)", 
            placeholder="09:00-12:00", 
            required=True,
            max_length=20,
            default=self.time
        )
        subject_input = ui.TextInput(
            label="ชื่อวิชา หรือ รหัสวิชา", 
            placeholder="GEN101 General Physics", 
            required=True,
            max_length=100,
            default=self.subject
        )
        room_input = ui.TextInput(
            label="ห้องเรียน (หากไม่มีให้ใส่ -)", 
            placeholder="72-405", 
            required=True,
            max_length=50,
            default=self.room
        )
        prof_input = ui.TextInput(
            label="อาจารย์ (หากไม่มีให้ใส่ -)", 
            placeholder="Prof. John Doe", 
            required=True,
            max_length=50,
            default=self.prof
        )
        
        self.time_input = time_input
        self.subject_input = subject_input
        self.room_input = room_input
        self.prof_input = prof_input

        self.add_item(self.time_input)
        self.add_item(self.subject_input)
        self.add_item(self.room_input)
        self.add_item(self.prof_input)

    async def on_submit(self, interaction: discord.Interaction):
        time = self.time_input.value.strip()
        subject_raw = self.subject_input.value
        subject = re.sub(r"\s+", " ", subject_raw.strip())
        room = self.room_input.value.strip()

        validation_result = await _validate_time_room(interaction, time, room)
        if validation_result is None:
            return
        time, room_final = validation_result

        prof = self.prof_input.value.strip()

        filter_ = {
            "user_id" : interaction.user.id,
            f"{self.date}.name" : self.subject 
        }
        update_operation = {
            "$set": {
                f"{self.date}.$.name": subject,
                f"{self.date}.$.time": time,
                f"{self.date}.$.room": room_final,
                f"{self.date}.$.professor": prof
            }
        }
        
        await self.db_collection.update_one(filter_, update_operation)

        await interaction.response.send_message(
            f"✅ แก้ไขวิชา **{subject}** \n🗓️ วัน**{DAY_EN_TO_TH.get(self.date)}** เวลา `{time}` ห้อง `{room_final}` \nอาจารย์ `{prof}`",
            ephemeral=True
        )
        
        await _regenerate_view(self.db_collection, interaction.user, self.original_msg, editSubjectSelect)


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
        label="ห้องเรียน (หากไม่มีให้ใส่ -)", 
        placeholder="72-405", 
        required=True,
        max_length=50
    )
    prof_input = ui.TextInput(
        label="อาจารย์ (หากไม่มีให้ใส่ -)", 
        placeholder="Prof. John Doe", 
        required=True,
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
        room = self.room_input.value.strip()
        prof = self.prof_input.value.strip()

        validation_result = await _validate_time_room(interaction, time, room)
        if validation_result is None:
            return
        time, room_final = validation_result
        
        new_class = {
            "name": subject,
            "time": time,
            "room": room_final,
            "professor" : prof
        }

        await self.db_collection.update_one(
            {"user_id": interaction.user.id},
            {"$push": {day_en: new_class}},
            upsert=True
        )

        await interaction.response.send_message(
            f"✅ บันทึกวิชา **{subject}** \n🗓️ วัน**{self.selected_day_th}** เวลา `{time}` ห้อง `{room_final}` \nอาจารย์ `{prof}`",
            ephemeral=True
        )

# --- Select Components Base & Classes ---
class BaseSubjectSelect(ui.Select):
    def __init__(self, db, author: discord.Member, options, placeholder: str):
        self.db_collection = db
        self.author = author
        super().__init__(
            placeholder=placeholder,
            min_values=1, max_values=1, options=options
        )

    async def _find_subject_data(self, selected_value: str):
        doc = await self.db_collection.find_one({"user_id": self.author.id})
        if not doc:
            return None, None, None, None , None
        try:
            day_key, subject_name_query = selected_value.split('-', 1)
        except ValueError:
            return None, None, None, None , None
        
        subjects = doc.get(day_key, [])
        for sub in subjects:
            if sub.get("name", "").strip() == subject_name_query.strip():
                return (
                    sub.get("name"),
                    day_key,
                    sub.get("time", "00:00"),
                    sub.get("room", "ไม่ระบุ"),
                    sub.get("professor", "ไม่ระบุ")
                )
                
        return None, None, None, None , None

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
        new_selector = DaySelect(self.db_collection)
        new_view = AddClassView(interaction.user,self.db_collection,new_selector)
        await interaction.response.send_modal(modal)
        await asyncio.sleep(0.5)
        await interaction.message.edit(view=new_view)

class delSubjectSelect(BaseSubjectSelect):
    def __init__(self, db, author, options):
        super().__init__(db, author, options, placeholder="เลือกวิชาที่จะลบ...")

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        name, day_key, time, room , prof= await self._find_subject_data(selected_value)

        if name:
            view = ConfirmView(
                db=self.db_collection,
                user_id=self.author.id,
                day_key=day_key,
                subject_name=name,
                subject_room=room,
                subject_professor=prof,
                original_msg=interaction.message
            )
            day_th = DAY_EN_TO_TH.get(day_key, day_key)
            await interaction.response.send_message(
                f"⚠️ **ยืนยันการลบ?**\nคุณต้องการลบวิชา **{name}** (วัน{day_th}) ใช่หรือไม่?", 
                view=view, 
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ หาวิชาไม่เจอ (อาจถูกลบไปแล้ว)", ephemeral=True)

class editSubjectSelect(BaseSubjectSelect):
    def __init__(self, db, author : discord.Member, options):
        super().__init__(db, author, options, placeholder="เลือกวิชาที่จะแก้ไข...")
        
    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        name, day_key, time, room, prof = await self._find_subject_data(selected_value)

        if not name:
            await interaction.response.send_message("❌ ไม่พบข้อมูล", ephemeral=True)
            return
            
        modal=EditInfoModal(db_collection=self.db_collection,
                            time_=time,
                            subject_=name,
                            room_=room,
                            date_=day_key,
                            prof_ = prof,
                            original_msg=interaction.message
                            ) 
        await interaction.response.send_modal(modal)


class ConfirmView(ui.View):
    def __init__(self, db, user_id, day_key, subject_name, subject_room,subject_professor,original_msg):
        super().__init__(timeout=60)
        self.db = db
        self.user_id = user_id
        self.day_key = day_key
        self.subject_name = subject_name
        self.subject_room = subject_room
        self.subject_professor = subject_professor
        self.original_message = original_msg

    @ui.button(label="ยืนยันลบ", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await self.db.update_one(
            {"user_id": self.user_id},
            {"$pull": {self.day_key: {"name": self.subject_name,"room": self.subject_room,"professor": self.subject_professor}}}
        )
        
        await interaction.response.edit_message(
            content=f"✅ ลบวิชา **{self.subject_name}** (วัน{DAY_EN_TO_TH.get(self.day_key, self.day_key)}) เรียบร้อยแล้ว!",
            view=None
        )
        await _regenerate_view(self.db, interaction.user, self.original_message, delSubjectSelect)
        self.stop()

    @ui.button(label="ยกเลิก", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content="❌ ยกเลิกการลบแล้ว", view=None)
        self.value = False
        self.stop()


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