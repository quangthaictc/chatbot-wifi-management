import logging
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from config.settings import TELEGRAM_API_TOKEN

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


async def main():
    logging.basicConfig(level=logging.DEBUG)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
