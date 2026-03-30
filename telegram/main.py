import logging
import asyncio
import httpx

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram import F
from aiogram.types import CallbackQuery, Message
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

    # Tach du lieu tu nut bam (Vi du: secblock_1_AA:BB:CC:DD:EE:FF)
    _, dpid, mac = callback.data.split("_")

    async with httpx.AsyncClient() as client:
        # 1. Goi API gui lenh chan xuong he thong mang
        await client.post(
            f"{FAST_API_URL}/access/block", json={"dpid": int(dpid), "mac_address": mac}
        )
        # 2. Bao cho FastAPI biet Admin da xu ly de HUY dem nguoc 5 phut
        await client.post(
            f"{FAST_API_URL}/security/resolve/{dpid}/{mac}/blocked_by_admin"
        )

    callback_text = callback.message.text or ""
    # Sua lai tin nhan hien tai: Xoa nut bam va them dong chu xac nhan
    await callback.message.edit_text(
        callback_text + "\n\n*Cap nhat:* Admin da xac nhan CHAN thanh cong.",
        parse_mode="Markdown",
    )
    # Hien pop-up nho tren man hinh dien thoai bao hieu da nhan lenh
    await callback.answer("Da thuc thi lenh chan mang!")


@dp.callback_query(F.data.startswith("secignore_"))
async def handle_sec_ignore(callback: CallbackQuery):
    if not callback.data or not isinstance(callback.message, Message):
        return

    # Tach du lieu tu nut bam
    _, dpid, mac = callback.data.split("_")

    async with httpx.AsyncClient() as client:
        # Bao cho FastAPI biet Admin bo qua de HUY tien trinh chan tu dong
        await client.post(
            f"{FAST_API_URL}/security/resolve/{dpid}/{mac}/ignored_by_admin"
        )

    callback_text = callback.message.text or ""
    # Sua lai tin nhan hien tai: Xoa nut bam
    await callback.message.edit_text(
        callback_text + "\n\n*Cap nhat:* Admin da chon BO QUA canh bao nay.",
        parse_mode="Markdown",
    )
    await callback.answer("Da huy bo dong thai chan mang.")


async def main():
    logging.basicConfig(level=logging.DEBUG)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
