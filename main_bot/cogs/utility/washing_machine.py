from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

STORE_API_URL = "https://route.uy-iot.ai/artemis/public/fun/getStoreInfo"
DEFAULT_STORE_NAME = "c09092_10"
TAIPEI_TIMEZONE = timezone(timedelta(hours=8))
REQUEST_TIMEOUT_SECONDS = 10


@dataclass
class Machine:
    slot: str
    status: str
    last_run: str | None = None


@dataclass
class FloorMachines:
    floor: str
    washers: list[Machine] = field(default_factory=list)
    dryers: list[Machine] = field(default_factory=list)


@dataclass
class StoreStatus:
    store_name: str
    store_alias: str
    query_time: str
    floors: dict[str, FloorMachines] = field(default_factory=dict)


async def fetch_store_status(store_name: str = DEFAULT_STORE_NAME) -> StoreStatus:
    """Fetch laundry and dryer status asynchronously from the store IoT API."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            STORE_API_URL,
            json={"storeName": store_name},
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
        ) as response:
            response.raise_for_status()
            data = await response.json()

    store_alias = data.get("store_alias", "Unknown Store")
    query_time = data.get("queryTime", "N/A")
    raw_machines = data.get("notDtcMachines", []) + data.get("dtcMachines", [])

    floors: dict[str, FloorMachines] = {}

    for machine in raw_machines:
        alias = machine.get("alias", "")
        type_code = machine.get("type_code", "")
        status = machine.get("status", "UNKNOWN")
        last_run_raw = machine.get("lastRun")

        formatted_time = None
        if last_run_raw:
            formatted_time = datetime.fromtimestamp(
                int(last_run_raw) / 1000, tz=TAIPEI_TIMEZONE
            ).strftime("%H:%M")

        floor = alias[0] if alias else "?"
        slot = alias[-1] if alias else "?"

        if floor not in floors:
            floors[floor] = FloorMachines(floor=floor)

        item = Machine(slot=slot, status=status, last_run=formatted_time)
        if type_code == "dryer":
            floors[floor].dryers.append(item)
        else:
            floors[floor].washers.append(item)

    return StoreStatus(
        store_name=store_name,
        store_alias=store_alias,
        query_time=query_time,
        floors=floors,
    )


def create_laundry_embed(
    store_status: StoreStatus,
    target_floor: str | None = None,
    author_name: str = "User",
) -> discord.Embed:
    """Create a formatted Discord Embed displaying machine statuses."""
    embed = discord.Embed(
        title=f"🧺 {store_status.store_alias} 洗烘衣機狀態",
        description=(
            f"🕒 **查詢時間 (Query Time):** `{store_status.query_time}`\n"
            f"🏢 **代碼 (Store ID):** `{store_status.store_name}`"
        ),
        color=discord.Color.from_rgb(52, 152, 219),
    )

    if target_floor and target_floor in store_status.floors:
        floors_to_display = {target_floor: store_status.floors[target_floor]}
    else:
        floors_to_display = store_status.floors

    for floor_num, floor_info in sorted(floors_to_display.items()):
        washer_lines = []
        for washer in sorted(floor_info.washers, key=lambda m: m.slot):
            if washer.status == "READY":
                washer_lines.append(f"• **W{washer.slot}:** 🟢 閒置 (Ready)")
            elif washer.status == "RUNNING":
                time_info = f" (開始於 {washer.last_run})" if washer.last_run else ""
                washer_lines.append(f"• **W{washer.slot}:** 🔴 使用中{time_info}")
            else:
                washer_lines.append(f"• **W{washer.slot}:** ⚪ {washer.status}")

        dryer_lines = []
        for dryer in sorted(floor_info.dryers, key=lambda m: m.slot):
            if dryer.status == "READY":
                dryer_lines.append(f"• **D{dryer.slot}:** 🟢 閒置 (Ready)")
            elif dryer.status == "RUNNING":
                time_info = f" (開始於 {dryer.last_run})" if dryer.last_run else ""
                dryer_lines.append(f"• **D{dryer.slot}:** 🔴 使用中{time_info}")
            else:
                dryer_lines.append(f"• **D{dryer.slot}:** ⚪ {dryer.status}")

        field_content = ""
        if washer_lines:
            field_content += "**洗衣機 (Washers):**\n" + "\n".join(washer_lines) + "\n"
        if dryer_lines:
            field_content += "**烘衣機 (Dryers):**\n" + "\n".join(dryer_lines)

        embed.add_field(
            name=f"🏢 {floor_num} 樓 (Floor {floor_num})",
            value=field_content or "無設備資訊 (No machines)",
            inline=False,
        )

    embed.set_footer(text=f"Requested by {author_name} • Mochi Laundry")
    return embed


class LaundryView(discord.ui.View):
    def __init__(self, store_name: str, floor: str | None = None, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.store_name = store_name
        self.floor = floor
        self.message: discord.Message | None = None

    @discord.ui.button(label="重新整理 (Refresh)", style=discord.ButtonStyle.primary, emoji="🔄")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            status_data = await fetch_store_status(self.store_name)
            embed = create_laundry_embed(
                status_data,
                target_floor=self.floor,
                author_name=interaction.user.display_name,
            )
            await interaction.edit_original_response(embed=embed, view=self)
        except Exception as exc:
            await interaction.followup.send(
                f"❌ 重新整理失敗 (Refresh failed): `{exc}`",
                ephemeral=True,
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class WashingMachine(commands.Cog):
    """Cog for querying dormitory laundry and dryer machine statuses."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_laundry_status(
        self,
        target,
        floor: str | None = None,
        store_name: str = DEFAULT_STORE_NAME,
        author_name: str = "User",
    ):
        try:
            status_data = await fetch_store_status(store_name)
        except Exception as exc:
            error_message = f"❌ 無法取得洗衣機資料 (Failed to fetch laundry data): `{exc}`"
            if isinstance(target, commands.Context):
                await target.send(error_message)
            else:
                await target.followup.send(error_message)
            return

        if floor and floor not in status_data.floors:
            available_floors = ", ".join(sorted(status_data.floors.keys()))
            message = f"⚠️ 找不到 {floor} 樓的資料。目前可用樓層：`{available_floors}`"
            if isinstance(target, commands.Context):
                await target.send(message)
            else:
                await target.followup.send(message)
            return

        embed = create_laundry_embed(
            status_data,
            target_floor=floor,
            author_name=author_name,
        )
        view = LaundryView(store_name=store_name, floor=floor)

        if isinstance(target, commands.Context):
            msg = await target.send(embed=embed, view=view)
            view.message = msg
        else:
            msg = await target.edit_original_response(embed=embed, view=view)
            view.message = msg

    @commands.hybrid_command(
        name="twash",
        aliases=["wash", "laundry"],
        help="Check dormitory washing machine and dryer status (e.g. twash, twash 2)",
    )
    @app_commands.describe(
        floor="Floor number to filter (optional, e.g. 2, 3, 4)",
        store_name="Store ID (default: c09092_10 - NCU Men's Dorm 7)",
    )
    async def twash(
        self,
        ctx: commands.Context,
        floor: str | None = None,
        store_name: str = DEFAULT_STORE_NAME,
    ):
        await ctx.defer()
        await self._send_laundry_status(
            target=ctx,
            floor=floor,
            store_name=store_name,
            author_name=ctx.author.display_name,
        )

    @app_commands.command(
        name="wash",
        description="Check dormitory washing machine and dryer status",
    )
    @app_commands.describe(
        floor="Floor number to filter (optional, e.g. 2, 3, 4)",
        store_name="Store ID (default: c09092_10 - NCU Men's Dorm 7)",
    )
    async def slash_wash(
        self,
        interaction: discord.Interaction,
        floor: str | None = None,
        store_name: str = DEFAULT_STORE_NAME,
    ):
        await interaction.response.defer()
        await self._send_laundry_status(
            target=interaction,
            floor=floor,
            store_name=store_name,
            author_name=interaction.user.display_name,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(WashingMachine(bot))
