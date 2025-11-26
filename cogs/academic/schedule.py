# cogs/academic/schedule.py

import discord
from discord.ext import commands
from components.schedule_components import *

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
    async def my_schedule(self, ctx: commands.Context, user : discord.Member | discord.User | str = None):
        if self.db is None: return await ctx.send("❌ DB Error")

        try:
            user = ctx.guild.get_member(user.id)

        except:
            user = str(user)
            user = user.lower() if user.isalpha() else user
            username = [i.name.lower() for i in ctx.guild.members]
            display_name = [i.display_name.lower() if i.display_name.isalpha() else i.display_name for i in ctx.guild.members]
            username.extend(display_name)
            all_name = username
            filter_member = list(filter(lambda i: i.startswith(user), all_name))
            await ctx.send('\n'.join(filter_member))
            if not filter_member:
                await ctx.send("🤔 ไม่พบผู้ใช้")
                return
            user = str(filter_member[0])
        type_converter = discord.utils.get(ctx.guild.members, name=user) or discord.utils.get(ctx.guild.members, display_name=user)
        true_user = ctx.guild.get_member(type_converter.id)
        target_user = true_user.id if true_user is not None else ctx.author.id
        target_display_name = true_user.display_name if true_user is not None else ctx.author.display_name
        doc = await self.db.find_one({"user_id": target_user})
        
        if not doc:
            await ctx.send("🤔 คุณยังไม่มีตารางเรียนนะ! ลองใช้ `baddclass` ดูสิ")
            return

        embed = discord.Embed(
            title=f"📅 ตารางเรียนของ {target_display_name}",
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
                    p = sub.get("professor", "-")
                    room_txt = f"**{r}**" if r and r != "ไม่ระบุ" else ""
                    prof_txt = f"**{p}**" if p and p != "ไม่ระบุ" else ""
                    lines.append(f"`{t}`\n**{n}**\n{room_txt} | {prof_txt}\n")
                
                embed.add_field(name=f"🗓️ {day_th}", value="\n".join(lines), inline=False)

        if not has_data:
             await ctx.send("🤔 คุณมีชื่อในระบบ แต่ยังไม่ได้เพิ่มวิชาเรียนเลย")
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