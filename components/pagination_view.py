import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import datetime


class ScheduleEmbedStrategy(ABC):
    @abstractmethod
    def create_embed(self, data_chunk: list, current_page: int, total_pages: int, user: discord.Member) -> discord.Embed:
        pass

class ExamEmbedStrategy(ScheduleEmbedStrategy):
    def __init__(self, headers):
        self.headers = headers

    def _get_emoji(self, header_text):
        h = header_text.lower()
        if "วัน" in h or "date" in h: return "📅"
        if "เวลา" in h or "time" in h: return "⏰"
        if "ห้อง" in h or "room" in h: return "📍"
        if "วิชา" in h or "subj" in h: return "📚"
        if "ที่นั่ง" in h or "seat" in h: return "🪑"
        if "กลุ่ม" in h or "sec" in h: return "👥"
        return "🔹"

    def create_embed(self, data_chunk: list, current_page: int, total_pages: int, user: discord.Member) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎓 ตารางสอบ: {user.display_name}",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Page {current_page + 1}/{total_pages} • Data from SCIBase KMUTNB")

        if not data_chunk:
            embed.description = "ไม่พบข้อมูลการสอบในหน้านี้"
            return embed

        for i, row in enumerate(data_chunk):
            if len(row) != len(self.headers): continue

            field_title = f"Exam Item"
            field_details = []
            subject_found = False

            for head, val in zip(self.headers, row):
                emoji = self._get_emoji(head)
                
                if ("วิชา" in head or "รหัส" in head) and not subject_found:
                    field_title = f"{emoji} {val}"
                    subject_found = True
                else:
                    val_fmt = f"**{val}**" if head == "วิชาที่สอบ" else val
                    field_details.append(f"> {emoji} **{head}:** {val_fmt}")

            embed.add_field(
                name=field_title,
                value="\n".join(field_details),
                inline=False
            )
        
        return embed

class ClassEmbedStrategy(ScheduleEmbedStrategy):
    def create_embed(self, data_chunk: list, current_page: int, total_pages: int, user: discord.Member) -> discord.Embed:
        
        embed = discord.Embed(
            title=f"📅 ตารางเรียน: {user.display_name}",
            color=discord.Color.teal(),
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")

        if not data_chunk:
            embed.description = "🌴 วันนี้ไม่มีเรียน!"
            return embed

        for day_name, subjects in data_chunk:
            lines = []
            subjects_sorted = sorted(subjects, key=lambda x: x.get("time", "00:00"))
            
            for sub in subjects_sorted:
                t = sub.get("time", "-")
                n = sub.get("name", "???")
                r = sub.get("room", "")
                p = sub.get("professor", "-")
                
                room_txt = f"**{r}**" if r and r != "ไม่ระบุ" else ""
                prof_txt = f"**{p}**" if p and p != "ไม่ระบุ" else ""
                lines.append(f"` ⏰ {t} ` **{n}**\n╚ {room_txt} | 👨‍🏫 {prof_txt}\n")

            embed.add_field(name=f"🗓️ {day_name}", value="\n".join(lines) if lines else "ไม่มีเรียน", inline=False)

        return embed

# ==========================================
# 4. The Pagination View (Context)
# ==========================================
class PaginationView(discord.ui.View):
    def __init__(self, data, strategy: ScheduleEmbedStrategy, user: discord.Member, invoke: discord.Member, sep=5):
        super().__init__(timeout=60)
        self.data = data
        self.strategy = strategy
        self.user = user
        self.invoke = invoke
        self.sep = sep
        self.current_page = 0
        self.total_pages = (len(data) + sep - 1) // sep
        self.update_buttons()

    def get_current_embed(self):
        start = self.current_page * self.sep
        end = start + self.sep
        data_chunk = self.data[start:end]
        return self.strategy.create_embed(data_chunk, self.current_page, self.total_pages, self.user)

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page == self.total_pages - 1
        # Disable both if there is only 1 page
        if self.total_pages <= 1:
            self.children[0].disabled = True
            self.children[1].disabled = True

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.invoke != interaction.user:
            return await interaction.response.defer()
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.invoke != interaction.user:
            return await interaction.response.defer()
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass