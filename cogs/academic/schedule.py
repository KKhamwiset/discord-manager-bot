# cogs/academic/schedule.py

import discord
from discord.ext import commands
from flask import ctx
from components.schedule_components import *
from validation import resolve_members, role
import re,datetime
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
    
    @property
    def examdb(self):   
        return self.bot.db["std_id"]
    
    @discord.app_commands.command(
    name="addstdid",
    description="Add student ID to fetch exam schedule"
    )
    @role()
    async def add_std_id(
        self,
        interaction: discord.Interaction,
        user_handler: discord.User | None,
        std_id: str
    ):
        if self.examdb is None:
            return await interaction.response.send_message(
                "❌ DB Error",
                ephemeral=True
            )
        # Validate student ID
        if not std_id:
            return await interaction.response.send_message(
                "❌ กรุณาใส่รหัสนักศึกษา",
                ephemeral=True
            )
        user = user_handler or interaction.user
        user_id = user.id
        await self.examdb.update_one(
            {"user_id": user_id},
            {"$set": {"std_id": std_id}},
            upsert=True
        )
        await interaction.response.send_message(
            f"✅ เพิ่มรหัสนักศึกษา `{std_id}` เรียบร้อยแล้ว"
        )

    @commands.command(
            name="examschedule", 
            aliases=["ex", "exam"],
            help="Show exam schedule of provided user if none show self"
    )
    async def exam_schedule(self, ctx: commands.Context, user_handler : discord.Member | str = None):
        if self.examdb is None:
            return await ctx.send("❌ DB Error")
        user = None
        if user_handler is None:
            user = ctx.author
        else:
            if isinstance(user_handler, (discord.Member, discord.User)):
                user = user_handler
            else:
                user = await resolve_members(ctx, user_handler)
                user = user[0]
        doc = await self.examdb.find_one({"user_id": user.id})
        if not doc:
            return await ctx.send(f"🤔 {user.display_name} ยังไม่มีตารางสอบนะ!")
        embed = discord.Embed(
            title=f"🗓️ ตารางสอบของ {user.display_name}",
            color=discord.Color.teal(),
        )
        import requests
        from bs4 import BeautifulSoup

        url = "http://www.scibase.kmutnb.ac.th/examroom/datatrain.php"
        params = {"IDcard": doc.get("std_id","")}
        r = requests.get(url, params=params)
        r.encoding = "utf-8"
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        data = []
        rows = soup.find_all("tr")
        if not rows:
            await ctx.send("🤔 ไม่พบข้อมูลตารางสอบ")
        else:
            for tr in rows:
                text = tr.get_text(strip=True, separator='|')
                data.append(text)
        print(data)
        header = data[0]
        for i in range(1,len(data)):
            data[i] = data[i].split('|')
            field = []
            for j in range(len(data[i])):
                field.append(f"**{header.split('|')[j]}**: {data[i][j]}")
            embed.add_field(name=f"📄 รายการที่ {i}", value="\n".join(field), inline=False)
        await ctx.send(embed=embed)
        
        
    @commands.command(name="addclass", 
                      aliases=["asch", "ac"],
                      help="Add subject data to user's database")
    async def add_class_interactive(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        
        selector=DaySelect(self.db)
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=selector)
        await ctx.send("เลือกวันเรียนเพื่อเพิ่มวิชา 👇", view=view)

    @commands.command(name="editclass",
                      aliases=["ec","esch"],
                      help="Edit the subject information")
    async def edit_class_info(self,ctx :commands.Context):
        if self.db is None:
            return await ctx.send("❌ DB Error")
        option = await generate_options(self.db, ctx.author.id)
        selector=editSubjectSelect(self.db,ctx.author,option)
        view = AddClassView(author=ctx.author,db_collection=self.db,Selector=selector)
        await ctx.send("เลือกวิชาที่ต้องการแก้ไข 👇", view=view)
        
    @commands.command(
            name="myschedule", 
            aliases=["msch", "mc"],
            help="Show the subjects list of provided user if none show self"
            )
    async def my_schedule(self, ctx: commands.Context, user_handler : discord.Member | str = None ,*params: str):

        if self.db is None:
            return await ctx.send("❌ DB Error")
    
        user = None
        filters = [i for i in params] if params else []

        if user_handler is None:
            user = ctx.author
        else:
            if isinstance(user_handler, (discord.Member, discord.User)):
                user = user_handler
            else:
                if not params and ':' in user_handler or '=' in user_handler:
                    filters += [user_handler]
                    user = ctx.author
                elif params and ':' in user_handler or '=' in user_handler:
                    filters = []
                    filters += [user_handler]
                    user = ctx.author
                else:
                    user = await resolve_members(ctx, user_handler)
                    user = user[0]

        doc = await self.db.find_one({"user_id": user.id})
        if not doc:
            return await ctx.send(f"🤔 {user.display_name} ยังไม่มีตารางเรียนนะ! ลองใช้ `baddclass` ดูสิ")

        day_filter = None
        for f in filters:
            if ":" in f or "=" in f:
                key, value = re.split(r"[:=]", f, maxsplit=1)
                key = key.lower()
                value = value.lower()

                if key in ["d", "day", "date"]:
                    if value in ["today", "td", "n", "now"]:
                        today_index = datetime.datetime.today().weekday()
                        day_filter = [DAYS_TH_EN[today_index][1]]
                    else:
                        for en_day, aliases in DAY_ALIASES.items():
                            if value in aliases or en_day.startswith(value):
                                day_filter = [en_day.capitalize()]
                                break
                        if not day_filter:
                            return await ctx.send(f"❌ ไม่พบวัน '{value}'")
                else:
                    day_filter = None
                
 
        embed = discord.Embed(
            title=f"📅 ตารางเรียนของ {user.display_name}",
            color=discord.Color.teal(),
        )

        has_data = False
        for day_th, day_en in DAYS_TH_EN:
            if day_filter and day_en not in day_filter:
                continue

            subjects = doc.get(day_en, [])
            if not subjects:
                continue

            has_data = True
            subjects_sorted = sorted(subjects, key=lambda x: x.get("time", "00:00"))
            lines = []
            for sub in subjects_sorted:
                t = sub.get("time", "-")
                n = sub.get("name", "???")
                r = sub.get("room", "")
                p = sub.get("professor", "-")
                room_txt = f"**{r}**" if r and r != "ไม่ระบุ" else ""
                prof_txt = f"**{p}**" if p and p != "ไม่ระบุ" else ""
                lines.append(f"`{t}`\n**{n}**\n{room_txt} | {prof_txt}\n")

            embed.add_field(name=f"🗓️ {day_th}", value="\n".join(lines), inline=False)

        if not has_data:
            await ctx.send("🤔 ไม่มีวิชาในวันที่ระบุหรือยังไม่ได้เพิ่มวิชาเรียนเลย")
        else:
            await ctx.send(embed=embed)

    @commands.command(name="delclass", 
                      aliases=["delsch", "dc"],
                      help="Delete subject from user's database" 
                      )
    async def delete_class(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        
        doc = await self.db.find_one({"user_id" : ctx.author.id})
        if not doc:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียน")
            return
            
        options = await generate_options(self.db,ctx.author.id)
        
        if not options:
            await ctx.send("🤔 ตารางเรียนว่างเปล่า")
            return

        selector = delSubjectSelect(self.db, ctx.author, options[:25])
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=selector)

        await ctx.send("เลือกรายวิชาที่ต้องการจะลบ 👇", view=view)

async def setup(bot): 
    await bot.add_cog(Schedule(bot))