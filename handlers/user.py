from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

import database as db
from keyboards import (
    subscribe_keyboard, main_menu_keyboard, genres_keyboard,
    movies_list_keyboard, rating_keyboard,
)
from utils import is_subscribed

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, bot):
    db.add_user(message.from_user.id)
    if not await is_subscribed(bot, message.from_user.id):
        await message.answer(
            "Botdan foydalanish uchun kanalimizga a'zo bo'ling:",
            reply_markup=subscribe_keyboard(),
        )
        return
    await message.answer(
        "Assalomu alaykum! 🎬 Kino kodini yuboring yoki menyudan foydalaning.",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_handler(callback: CallbackQuery, bot):
    if await is_subscribed(bot, callback.from_user.id):
        await callback.message.delete()
        await callback.message.answer(
            "Rahmat! Endi botdan foydalanishingiz mumkin.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await callback.answer("Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)


@router.message(F.text == "🎬 Janrlar")
async def genres_handler(message: Message):
    genres = db.get_genres()
    if not genres:
        await message.answer("Hozircha janrlar mavjud emas.")
        return
    await message.answer("Janrni tanlang:", reply_markup=genres_keyboard())


@router.message(F.text == "🔝 Top kinolar")
async def top_handler(message: Message):
    movies = db.get_top_movies(10)
    if not movies:
        await message.answer("Hozircha kinolar mavjud emas.")
        return
    await message.answer(
        "🔝 Eng ko'p ko'rilgan kinolar:",
        reply_markup=movies_list_keyboard(movies, "top", 0, len(movies)),
    )


@router.message(F.text == "🔍 Qidirish")
async def search_prompt_handler(message: Message):
    await message.answer("Kino nomini yozib yuboring (masalan: Titanik)")


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    await message.answer(
        "🎬 Kino kodini yuboring — kino keladi.\n"
        "🔍 Qidirish — nomi bo'yicha kino topish.\n"
        "🔝 Top kinolar — eng ommabop kinolar."
    )


@router.callback_query(F.data.startswith("genre:"))
async def genre_movies_handler(callback: CallbackQuery):
    _, genre, offset = callback.data.split(":")
    offset = int(offset)
    movies = db.get_movies_by_genre(genre, offset, 10)
    total = db.count_movies_by_genre(genre)
    await callback.message.edit_text(
        f"🎬 {genre} janridagi kinolar:",
        reply_markup=movies_list_keyboard(movies, f"genre:{genre}", offset, total),
    )


@router.callback_query(F.data.startswith("top:"))
async def top_pagination_handler(callback: CallbackQuery):
    offset = int(callback.data.split(":")[1])
    movies = db.get_top_movies(10)
    await callback.message.edit_text(
        "🔝 Eng ko'p ko'rilgan kinolar:",
        reply_markup=movies_list_keyboard(movies, "top", offset, len(movies)),
    )


@router.callback_query(F.data.startswith("search:"))
async def search_pagination_handler(callback: CallbackQuery, state):
    data = await state.get_data()
    query = data.get("last_query", "")
    offset = int(callback.data.split(":")[1])
    movies = db.search_movies(query, offset, 10)
    total = db.count_search_movies(query)
    await callback.message.edit_text(
        f"'{query}' bo'yicha natijalar:",
        reply_markup=movies_list_keyboard(movies, "search", offset, total),
    )


@router.callback_query(F.data.startswith("get:"))
async def get_movie_handler(callback: CallbackQuery):
    code = int(callback.data.split(":")[1])
    await send_movie(callback.message, code)
    await callback.answer()


@router.message(F.text.regexp(r"^\d+$"))
async def code_lookup_handler(message: Message):
    code = int(message.text)
    if not db.code_exists(code):
        await message.answer("Bunday kodli kino topilmadi 😕")
        return
    await send_movie(message, code)


@router.message(F.text)
async def text_search_handler(message: Message, state):
    query = message.text.strip()
    movies = db.search_movies(query, 0, 10)
    total = db.count_search_movies(query)
    if not movies:
        await message.answer("Hech narsa topilmadi 😕. Kino kodini yoki nomini to'g'ri yozing.")
        return
    await state.update_data(last_query=query)
    await message.answer(
        f"'{query}' bo'yicha natijalar:",
        reply_markup=movies_list_keyboard(movies, "search", 0, total),
    )


@router.callback_query(F.data.startswith("rate:"))
async def rate_handler(callback: CallbackQuery):
    _, code, stars = callback.data.split(":")
    db.add_rating(callback.from_user.id, int(code), int(stars))
    avg, cnt = db.get_rating_info(int(code))
    await callback.answer(f"Bahoyingiz saqlandi! O'rtacha: {avg} ({cnt} ta baho)", show_alert=True)


async def send_movie(message: Message, code: int):
    movie = db.get_movie(code)
    if not movie:
        await message.answer("Kino topilmadi.")
        return
    db.increment_views(code)
    avg, cnt = db.get_rating_info(code)
    caption = (
        f"🎬 <b>{movie['title']}</b> ({movie['year']})\n"
        f"📁 Janr: {movie['genre']}\n"
        f"⏱ Davomiyligi: {movie['duration']}\n"
        f"🗣 Til: {movie['language']}\n"
        f"🎞 Sifat: {movie['quality']}\n"
        f"⭐ Reyting: {avg} ({cnt} ta baho)\n"
        f"👁 Ko'rishlar: {movie['views'] + 1}"
    )
    await message.answer_video(movie["file_id"], caption=caption, reply_markup=rating_keyboard(code))
