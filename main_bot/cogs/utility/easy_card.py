from aiohappyeyeballs import types
import asyncio
import base64
import datetime
import json
import re
import requests
import discord
from bs4 import BeautifulSoup
from discord.ext import commands
import os

from dotenv import load_dotenv

load_dotenv()

try:
    from schema.schema import InjectPayload
except ImportError:
    from schema import InjectPayload

BASE_URL = os.getenv("EASYCARD_BASE")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
CAPTCHA_ENDPOINT = os.getenv("CAPTCHA_ENDPOINT")
CAPTCHA_CODE_GET_ENDPOINT = os.getenv("CAPTCHA_CODE_GET_ENDPOINT")
CAPTCHA_VERIFY_ENDPOINT = os.getenv("CAPTCHA_VERIFY_ENDPOINT")
CAPTCHA_WAIT_SECONDS = int(os.getenv("CAPTCHA_WAIT_SECONDS"))


class SessionManage:
    def __init__(self, ctx: commands.Context, status_message: discord.Message | None = None):
        self.ctx = ctx
        self.status_message = status_message
        self.session = requests.Session()
        self.card_id = ""
        self.birthday = ""
        self.date = "date3m"
        self.captcha = ""
        self.captcha_token = None
        self.start_date = None
        self.end_date = None
        self.date_calc()
        self.init_session()

    # --------------------------------------------------
    # Session & Init
    # --------------------------------------------------

    def init_session(self):
        r = self.session.get(f"{BASE_URL}{SEARCH_ENDPOINT}", timeout=20)
        r.raise_for_status()

    def set_card(self, card_number: str):
        self.card_id = card_number

    # --------------------------------------------------
    # CAPTCHA Processing
    # --------------------------------------------------

    async def get_captcha_json(self):
        r_captcha = self.session.get(f"{BASE_URL}{CAPTCHA_ENDPOINT}", timeout=20)
        r_captcha.raise_for_status()

        self.captcha_token = r_captcha.headers.get("X-Captcha-Token")
        if not self.captcha_token:
            raise ValueError("Captcha token not found")

        r_captcha_b64 = self.session.post(
            f"{BASE_URL}{CAPTCHA_CODE_GET_ENDPOINT}",
            json={"token": self.captcha_token},
            timeout=20,
        )
        r_captcha_b64.raise_for_status()

        data = r_captcha_b64.json()
        if "speakable" not in data:
            raise ValueError(f"Invalid captcha response: {data}")

        decoded = base64.b64decode(data["speakable"]).decode("utf-8")
        self.captcha = self.normalize_number(decoded)

        if self.status_message:
            await self.status_message.edit(
                content=f"✅ CAPTCHA พร้อมแล้ว — กำลังเริ่มนับถอยหลัง {CAPTCHA_WAIT_SECONDS} วินาที...",
                embed=None,
            )

    def normalize_number(self, number: str) -> str:
        if "::" not in number:
            raise ValueError(f"Unexpected captcha format: {number}")
        _, captcha_part = number.split("::", 1)
        return captcha_part.replace("-", "").strip()

    def verify_captcha(self):
        if not self.captcha or not self.captcha_token:
            raise ValueError("Captcha and Captcha token are required")

        r = self.session.post(
            f"{BASE_URL}{CAPTCHA_VERIFY_ENDPOINT}",
            json={"captcha": self.captcha, "token": self.captcha_token},
            timeout=20,
        )
        r.raise_for_status()

        data = r.json()
        if not data.get("success"):
            raise ValueError(f"Captcha verification failed: {data.get('message', data)}")
        return data

    # --------------------------------------------------
    # Date Calculation
    # --------------------------------------------------

    def date_calc(self):
        end = datetime.datetime.now() - datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=92)
        self.end_date = end.strftime("%Y-%m-%d")
        self.start_date = start.strftime("%Y-%m-%d")

    # --------------------------------------------------
    # Query Execution
    # --------------------------------------------------

    async def _post(self):
        if not self.start_date or not self.end_date:
            self.date_calc()

        if not self.captcha:
            raise ValueError("Captcha is required")

        for remaining in range(CAPTCHA_WAIT_SECONDS, 0, -1):
            if self.status_message:
                await self.status_message.edit(
                    content=f"⏳ กำลังรอระบบ CAPTCHA `{remaining}` วินาที",
                    embed=None,
                )
            await asyncio.sleep(1)

        if self.status_message:
            await self.status_message.edit(content="🔐 กำลังตรวจสอบ CAPTCHA...", embed=None)

        self.verify_captcha()

        if self.status_message:
            await self.status_message.edit(
                content="CAPTCHA ผ่านแล้ว กำลังดึงข้อมูล EasyCard...",
                embed=None,
            )

        payload = InjectPayload(
            card_id=self.card_id,
            captcha=self.captcha,
            birthday=self.birthday,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        payload_data = payload.to_dict()
        payload_data["thisPage"] = "1"

        r = self.session.post(
            f"{BASE_URL}{SEARCH_ENDPOINT}",
            data=payload_data,
            timeout=20,
        )
        r.raise_for_status()

     

        result = self.parse_result(r.text)
        embed = self.build_embed(result)

        # Single place where embed is attached to status_message
        if self.status_message:
            await self.status_message.edit(content=None, embed=embed)
        else:
            await self.ctx.send(embed=embed)

        return result

    # --------------------------------------------------
    # Parser
    # --------------------------------------------------

    def parse_result(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        transactions = []

        # Expiry date parsing
        expiry_date = None
        expiry_node = soup.select_one("#card_exp_date .card_exp_date")
        if expiry_node:
            expiry_text = expiry_node.get_text(" ", strip=True)
            expiry_match = re.search(r"\d{4}-\d{2}-\d{2}", expiry_text)
            if expiry_match:
                expiry_date = expiry_match.group(0)

        # Transaction rows parsing
        rows = soup.select("div[id^='pg'] tr.r1")
        for row in rows:
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if len(cells) < 5:
                continue

            transaction = {
                "datetime": cells[0],
                "category": cells[1],
                "location": cells[2],
                "amount": cells[3],
                "balance": cells[4],
                "operator": cells[9] if len(cells) > 9 else "",
            }
            transactions.append(transaction)

        balance = transactions[0].get("balance") if transactions else None

        return {
            "card_id": self.card_id,
            "balance": balance,
            "expiry_date": expiry_date,
            "transactions": transactions,
        }

    # --------------------------------------------------
    # Discord Embed Building
    # --------------------------------------------------

    def build_embed(self, result: dict) -> discord.Embed:
        if not isinstance(result, dict):
            raise TypeError("result must be dict")

        transactions = result.get("transactions", [])
        if not isinstance(transactions, list):
            transactions = []

        balance = result.get("balance")
        expiry_date = result.get("expiry_date")
        color = discord.Color.green() if balance is not None else discord.Color.orange()

        embed = discord.Embed(
            title="💳 EasyCard Transaction History",
            color=color,
            timestamp=datetime.datetime.now(),
        )

        # Balance & Expiry Fields
        balance_text = f"**NT$ {balance}**" if balance is not None else "No balance data"
        embed.add_field(name="💰 Balance", value=balance_text, inline=True)

        if expiry_date:
            embed.add_field(name="📅 Expiry", value=f"`{expiry_date}`", inline=True)

        # Card Number Masking
        card_id = str(result.get("card_id") or self.card_id or "")
        masked_card = f"{card_id[:4]} •••• •••• {card_id[-4:]}" if len(card_id) >= 8 else card_id
        embed.add_field(name="💳 Card", value=f"`{masked_card}`", inline=False)

        # Recent Transactions
        category_map = {"扣款": "Payment", "加值": "Top Up"}

        if transactions:
            recent = transactions[:5]
            for tx in recent:
                if not isinstance(tx, dict):
                    continue

                tx_datetime = str(tx.get("datetime", "Unknown time"))
                raw_category = str(tx.get("category", ""))
                category = category_map.get(raw_category, raw_category or "Transaction")
                location = str(tx.get("location", "Unknown") or "Unknown")
                amount = str(tx.get("amount", "-") or "-")
                balance_after = str(tx.get("balance", "-") or "-")
                operator = str(tx.get("operator", "") or "")

                if raw_category == "加值":
                    icon, amount_display = "➕", f"+{amount}"
                elif raw_category == "扣款":
                    icon, amount_display = "💸", f"-{amount}"
                else:
                    icon, amount_display = "💳", amount

                if len(location) > 70:
                    location = location[:67] + "..."

                details = (
                    f"**{category}**\n"
                    f"📍 {location}\n"
                    f"{icon} `{amount_display}` NTD\n"
                    f"💰 Balance: `{balance_after}` NTD"
                )
                if operator and operator != location:
                    details += f"\n🏢 {operator}"

                embed.add_field(name=f"🕒 {tx_datetime}", value=details, inline=False)
        else:
            embed.add_field(
                name="📋 Recent Activity",
                value="No transaction data returned by EasyCard.",
                inline=False,
            )

        embed.set_footer(text="EasyCard transaction records may not be real-time")
        return embed


# ==================================================
# Cog Definition
# ==================================================

class EasyCard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.collection = self.db["easycard"]

    @commands.hybrid_command(
        name="easycard",
        help="Check EasyCard transactions",
        aliases=["c", "card"],
    )
    async def easycard(self, ctx: commands.Context):
        status_message = None

        try:
            status_message = await ctx.send(
                "🔄 กำลังเชื่อมต่อ EasyCard..."
            )

            session = SessionManage(
                ctx,
                status_message=status_message
            )

            user = ctx.author

            find_user_card = await self.collection.find_one({
                "guild_id": str(ctx.guild.id),
                "easycards": {
                    "$elemMatch": {
                        "user_id": str(user.id)
                    }
                }
            })

            print(find_user_card)

            if not find_user_card:
                embed = discord.Embed(
                    title="❌ ไม่พบข้อมูล EasyCard ของคุณ",
                    description="กรุณาเพิ่มข้อมูล EasyCard ของคุณก่อน",
                    color=discord.Color.red(),
                )

                await status_message.edit(
                    content=None,
                    embed=embed
                )
                return

            user_info = next(
                (
                    card
                    for card in find_user_card.get("easycards", [])
                    if card.get("user_id") == str(user.id)
                ),
                None
            )

            if not user_info:
                raise ValueError(
                    "EasyCard entry not found for this user"
                )

            card_number = user_info.get("card_number")

            if not card_number:
                raise ValueError(
                    "Card number is missing"
                )

            session.set_card(card_number)

            await session.get_captcha_json()
            await session._post()

        except Exception as e:
            print(
                "EasyCard Error:",
                type(e).__name__,
                repr(e),
            )

        except Exception as e:
            error_text = f"❌ Something went wrong: `{type(e).__name__}: {e}`"
            if status_message:
                await status_message.edit(content=error_text, embed=None)
            else:
                await ctx.send(error_text)
    
    @commands.hybrid_command(
        name="addcard",
        help="Add EasyCard to your account",
    )
    async def addcard(self, ctx: commands.Context, card_number: str | None = None):
        user = ctx.author
        try:
            dm_message = await user.send(
                "💳 ส่งหมายเลข EasyCard 16 หลักมาได้เลย"
            )

        except discord.Forbidden:
            await ctx.send(
                "ส่ง DM ไม่ได้ เปิด DM จาก server นี้ก่อน"
            )
            return

        def check(message: discord.Message):
            return (
                message.author.id == user.id
                and isinstance(
                    message.channel,
                    discord.DMChannel,
                )
            )

        msg = await self.bot.wait_for("message", check=check, timeout=60.0)
        card_number = msg.content.strip()

        regex = "^[0-9]{10}$|^[0-9]{16}$"

        if not re.match(regex, card_number):
            await user.send("รูปแบบบัตรไม่ถูกต้อง")
            return
        await user.send(f"บัตรของคุณคือ `{card_number}`💳")

        user_guild = str(user.guild.id)
        existing = await self.collection.find_one({
            "guild_id": user_guild,
            "easycards.user_id": str(user.id),
        })

        if existing:
            await self.collection.update_one(
                {
                    "guild_id": user_guild,
                    "easycards.user_id": str(user.id),
                },
                {
                    "$set": {
                        "easycards.$.card_number": card_number
                    }
                }
            )
        else:
            await self.collection.update_one(
                {
                    "guild_id": user_guild
                },
                {
                    "$push": {
                        "easycards": {
                            "user_id": str(user.id),
                            "card_number": card_number
                        }
                    }
                },
                upsert=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(EasyCard(bot))