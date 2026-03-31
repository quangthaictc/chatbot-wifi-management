import logging
import asyncio
import httpx

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import F
from aiogram.types import CallbackQuery, Message
import aiohttp
from aiogram.types import BufferedInputFile
from config.settings import TELEGRAM_API_TOKEN, FAST_API_URL

from services.gemini_api import GeminiService
from middlewares.auth import AuthMiddleware

bot = Bot(
    token=TELEGRAM_API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
)
dp = Dispatcher()
gemini = GeminiService()

dp.message.middleware(AuthMiddleware())


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "*QuackWF Bot - SDN Controller Assistant* \nWelcome, Sir! I am QuackWF, your AI assistant dedicated to managing your internal Wi-Fi network."
    )


@dp.message(Command("map"))
async def send_network_map(message: Message):
    await message.answer("Đang lấy tọa độ vệ tinh và vẽ sơ đồ mạng...")

    # Gọi xuống API của Backend
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{FAST_API_URL}/network/diagram") as resp:
            if resp.status == 200:
                # Đọc byte của tấm ảnh
                image_bytes = await resp.read()

                # Đóng gói ảnh cho Telegram
                photo = BufferedInputFile(image_bytes, filename="map.png")

                # Gửi ảnh bùm!
                await message.answer_photo(
                    photo=photo,
                    caption="Báo cáo Sếp, đây là sơ đồ hạ tầng mạng hiện tại!",
                )
            else:
                await message.answer("Lỗi: Không thể tạo sơ đồ mạng lúc này.")


@dp.message()
async def gemini_handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    user_text = message.text or ""

    if not user_text:
        await message.answer("Please, using text in this chat!")
        return

    response = await gemini.received_message(user_text)

    reply_text = response or "Please try again later."
    await message.answer(reply_text, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("secblock_"))
async def handle_sec_block(callback: CallbackQuery):

    if not callback.data or not isinstance(callback.message, Message):
        return

    _, dpid, mac = callback.data.split("_")

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{FAST_API_URL}/access/block", json={"dpid": int(dpid), "mac_address": mac}
        )

        await client.post(
            f"{FAST_API_URL}/security/resolve/{dpid}/{mac}/blocked_by_admin"
        )

    callback_text = callback.message.text or ""

    await callback.message.edit_text(
        callback_text + f"\n\n*Updated:* MAC {mac} has been blocked.",
        parse_mode="Markdown",
    )

    await callback.answer("Blocked successfully!")


@dp.callback_query(F.data.startswith("secignore_"))
async def handle_sec_ignore(callback: CallbackQuery):
    if not callback.data or not isinstance(callback.message, Message):
        return

    _, dpid, mac = callback.data.split("_")

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{FAST_API_URL}/security/resolve/{dpid}/{mac}/ignored_by_admin"
        )

    callback_text = callback.message.text or ""

    await callback.message.edit_text(
        callback_text + "\n\n*Update:* The admin has chosen to ignore this warning!",
        parse_mode="Markdown",
    )
    await callback.answer("Cancelled!")


async def main():
    logging.basicConfig(level=logging.DEBUG)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
