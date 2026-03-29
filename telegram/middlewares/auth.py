import os
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from config.settings import ALLOWED_USERS


class AuthMiddleware(BaseMiddleware):
    def __init__(self):
        self.allowed_users = {
            uid.strip() for uid in ALLOWED_USERS.split(",") if uid.strip()
        }
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return

        user_id = str(event.from_user.id)

        if user_id not in self.allowed_users:
            await event.answer(
                "**Access Denied**\n\nYou do not have permission to control the QuackWF system."
            )
            return

        return await handler(event, data)
