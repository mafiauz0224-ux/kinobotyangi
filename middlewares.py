import time
from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.7):
        self.limit = limit
        self.last_time = {}

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id if event.from_user else None
        if user_id:
            now = time.monotonic()
            last = self.last_time.get(user_id, 0)
            if now - last < self.limit:
                return
            self.last_time[user_id] = now
        return await handler(event, data)
