from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import CHANNEL_LINK
import database as db


def subscribe_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Kanalga o'tish", url=CHANNEL_LINK or "https://t.me")
    builder.button(text="✅ A'zo bo'ldim", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Janrlar"), KeyboardButton(text="🔝 Top kinolar")],
            [KeyboardButton(text="🔍 Qidirish"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def genres_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for genre in db.get_genres():
        builder.button(text=genre, callback_data=f"genre:{genre}:0")
    builder.adjust(2)
    return builder.as_markup()


def movies_list_keyboard(movies, base_callback, offset, total) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for movie in movies:
        builder.button(text=f"{movie['code']} - {movie['title']}", callback_data=f"get:{movie['code']}")
    builder.adjust(1)
    nav_row = []
    if offset > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{base_callback}:{max(0, offset - 10)}"))
    if offset + 10 < total:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{base_callback}:{offset + 10}"))
    if nav_row:
        builder.row(*nav_row)
    return builder.as_markup()


def rating_keyboard(code) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for star in range(1, 6):
        builder.button(text="⭐" * star, callback_data=f"rate:{code}:{star}")
    builder.adjust(5)
    return builder.as_markup()


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kino qo'shish", callback_data="admin_add")
    builder.button(text="🗑 Kino o'chirish", callback_data="admin_delete")
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="📢 Xabar yuborish", callback_data="admin_broadcast")
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Bekor qilish", callback_data="cancel")
    return builder.as_markup()
