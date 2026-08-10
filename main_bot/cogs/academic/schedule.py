# cogs/academic/schedule.py

import discord
import validation
from discord.ext import commands
from components.pagination_view import PaginationView, ExamEmbedStrategy, ClassEmbedStrategy
from components.schedule_components import * 
from validation import resolve_members 
import re, datetime , os
import requests
from bs4 import BeautifulSoup
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
    async def add_std_id(
        self,
        interaction: discord.Interaction,
        std_id: str
    ):
        if self.examdb is None:
            return await interaction.response.send_message(
                "❌ DB Error",
                ephemeral=True
            )
        if not std_id:
            return await interaction.response.send_message(
                "❌ กรุณาใส่รหัสนักศึกษา",
                ephemeral=True
            )
        user = interaction.user
        user_id = user.id
        doc = await self.examdb.find_one({"user_id": user_id})
        if doc and doc.get("std_id") is not None:
            return await interaction.response.send_message(
                f"รหัสนักศึกษาของ `{user.display_name}` ถูกเพิ่มไว้แล้ว",
                ephemeral=True
            )
        
        await self.examdb.update_one(
            {"user_id": user_id},
            {"$set": {"std_id": std_id}},
            upsert=True
        )
        await interaction.response.send_message(
            f"✅ เพิ่มรหัสนักศึกษา `{std_id}` เรียบร้อยแล้ว",
            ephemeral=True
        )
    @discord.app_commands.command(
            name="edit_stdid",
            description="Edit student ID to fetch exam schedule"
    )
    async def edit_std_id(
        self,
        interaction: discord.Interaction,
        std_id: str
    ):
        if self.examdb is None:
            return await interaction.response.send_message(
                "❌ DB Error",
                ephemeral=True
            )
        if not std_id:
            return await interaction.response.send_message(
                "❌ กรุณาใส่รหัสนักศึกษา",
                ephemeral=True
            )
        user = interaction.user
        user_id = user.id
        doc = await self.examdb.find_one({"user_id": user_id})
        if not doc or doc.get("std_id") is None:
            return await interaction.response.send_message(
                f"❌ รหัสนักศึกษาของ `{user.display_name}` ยังไม่มีในระบบ กรุณาใช้คำสั่ง `/addstdid` ก่อน",
                ephemeral=True
            )
        
        await self.examdb.update_one(
            {"user_id": user_id},
            {"$set": {"std_id": std_id}},
            upsert=True
        )
        await interaction.response.send_message(
            f"✅ แก้ไขรหัสนักศึกษาเป็น `{std_id}` เรียบร้อยแล้ว",
            ephemeral=True
        )

    @commands.command(name="examschedule", aliases=["ex", "exam"])
    @validation.guild_only()
    async def exam_schedule(self, ctx: commands.Context, user_handler: discord.Member | str = None):
        if self.examdb is None: return await ctx.send("❌ DB Error")
        
        user = ctx.author

        if user_handler:
            if isinstance(user_handler, (discord.Member, discord.User)):
                user = user_handler
            else:
                resolved = await resolve_members(ctx, user_handler)
                if resolved: user = resolved[0]

        main_cursor = await self.examdb.find_one({
            "guild_id": str(ctx.guild.id)
        })

        if main_cursor is None: 
            return await ctx.send("DB Error")
        
        doc = next((
            (item for item in main_cursor.get("member_id", []) if item["user_id"] == user.id)
        ), None)

        if not doc:
            return await ctx.send(f"🤔 {user.display_name} ยังไม่มีตารางสอบนะ!")

        # Scrape Data
        msg = await ctx.send("🔄 กำลังดึงข้อมูลจาก REG...")
        try:
            url = os.getenv("API_ENDPOINT","")
            if url == "":
                return await msg.edit(content="API Endpoint not found")

            params = {"IDcard": doc.get("std_id", "")}
            
            r = await self.bot.loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=5))
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.find_all("tr")
            
            if not rows:
                return await msg.edit(content="🤔 ไม่พบข้อมูลตารางสอบในระบบ")

            data_rows = []
            for tr in rows:
                cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cols: data_rows.append(cols)

            if not data_rows:
                return await msg.edit(content="🤔 ตารางเปล่า")

            headers = data_rows[0]
            exam_entries = data_rows[1:] 
            strategy = ExamEmbedStrategy(headers=headers)
            view = PaginationView(data=exam_entries,
                                  strategy=strategy, 
                                  user=user,
                                  invoke=ctx.author,
                                  sep=2)
            
            await msg.delete()
            view.message = await ctx.send(embed=view.get_current_embed(), view=view)

        except Exception as e:
            await msg.edit(content=f"⚠️ เกิดข้อผิดพลาด: ||{e}||")
        
    @commands.command(name="addclass", 
                      aliases=["asch", "ac"],
                      help="Add subject data to user's database")
    @validation.guild_only()
    async def add_class_interactive(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        
        selector=DaySelect(self.db)
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=selector)
        await ctx.send("เลือกวันเรียนเพื่อเพิ่มวิชา 👇", view=view)

    @commands.command(name="editclass",
                      aliases=["ec","esch"],
                      help="Edit the subject information")
    @validation.guild_only()
    async def edit_class_info(self,ctx :commands.Context):
        if self.db is None:
            return await ctx.send("❌ DB Error")
        option = await generate_options(self.db,ctx.guild.id, ctx.author.id)
        selector=editSubjectSelect(self.db,ctx.author,option)
        view = AddClassView(author=ctx.author,db_collection=self.db,Selector=selector)
        await ctx.send("เลือกวิชาที่ต้องการแก้ไข 👇", view=view)
        
    @commands.command(
            name="myschedule", 
            aliases=["msch", "mc"],
            help="Show the subjects list of provided user if none show self"
            )
    @validation.guild_only()
    async def my_schedule(self, ctx: commands.Context, user_handler: discord.Member | str = None, *params: str):

        if self.db is None: return await ctx.send("❌ DB Error")
    
        user = ctx.author
        if user_handler:
            if isinstance(user_handler, (discord.Member, discord.User)):
                user = user_handler
            elif not params and (':' in user_handler or '=' in user_handler):
                params = (user_handler,) + params
            else:
                resolved = await resolve_members(ctx, user_handler)
                if resolved: user = resolved[0]

        doc = await get_user_schedule(self.db, ctx.guild.id, user.id)
        if not doc:
            return await ctx.send(f"🤔 {user.display_name} ยังไม่มีตารางเรียนนะ! ลองใช้ `addclass` ดูสิ")

        active_days = []
        for day_th, day_en in DAY_TH_TO_EN.items():
            subjects = doc.get(day_en, [])
            if subjects:
                active_days.append((f"{day_th} ({day_en})", subjects))

        if not active_days:
            return await ctx.send("🤔 ตารางเรียนว่างเปล่า")
        strategy = ClassEmbedStrategy()
        view = PaginationView(data=active_days, 
                              strategy=strategy, 
                              user=user,
                              invoke=ctx.author,
                              sep=3)
        view.message = await ctx.send(embed=view.get_current_embed(), view=view)

    @commands.command(name="delclass", 
                      aliases=["delsch", "dc"],
                      help="Delete subject from user's database" 
                      )
    @validation.guild_only()
    async def delete_class(self, ctx: commands.Context):
        if self.db is None: return await ctx.send("❌ DB Error")
        doc = await get_user_schedule(self.db,ctx.guild.id, ctx.author.id)
        if not doc:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียน")
            return

        options = await generate_options(self.db, ctx.guild.id, ctx.author.id)

        if not options:
            await ctx.send("🤔 ตารางเรียนว่างเปล่า")
            return

        selector = delSubjectSelect(self.db, ctx.author, options[:25])
        view = AddClassView(author=ctx.author, db_collection=self.db, Selector=selector)

        await ctx.send("เลือกรายวิชาที่ต้องการจะลบ 👇", view=view)

async def setup(bot): 
    await bot.add_cog(Schedule(bot))
