import logging
import asyncio
import httpx

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.types import FSInputFile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import TELEGRAM_API_TOKEN, FAST_API_URL
from datetime import datetime

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


@dp.message(F.text.lower().in_({"map", "bản đồ", "sơ đồ", "topology"}))
async def send_map(message: types.Message):
    await message.answer("Capturing network topology...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"topology_{timestamp}.png"

    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(options=options)
        driver.get("http://127.0.0.1:5000/")

        await asyncio.sleep(5)

        driver.save_screenshot(f"/app/topologies/{filename}")
        driver.quit()

        photo = FSInputFile(f"/app/topologies/{filename}")
        await message.answer_photo(
            photo=photo,
            caption=f"Network Topology at {datetime.now().strftime('%H:%M:%S')}",
            parse_mode=None,
        )
    except Exception as e:
        await message.answer(f"Error capturing network topology!")


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
