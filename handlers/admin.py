from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import database as db
from config import ADMIN_IDS
from keyboards import admin_menu_keyboard, cancel_keyboard

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AddMovie(StatesGroup):
    code = State()
    title = State()
    year = State()
    genre = State()
    duration = State()
    language = State()
    quality = State()
    file = State()


class Broadcast(StatesGroup):
    waiting = State()


class DeleteMovie(StatesGroup):
    waiting = State()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🔧 Admin panel:", reply_markup=admin_menu_keyboard())


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    users = db.get_user_count()
    movies = db.get_movie_count()
    await callback.message.answer(f"👥 Foydalanuvchilar: {users}\n🎬 Kinolar: {movies}")
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Bekor qilindi.")
    await callback.answer()


@router.callback_query(F.data == "admin_add")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AddMovie.code)
    await callback.message.answer("Kino kodini kiriting (raqam):", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(AddMovie.code)
async def add_movie_code(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Kod faqat raqamlardan iborat bo'lishi kerak.")
        return
    await state.update_data(code=int(message.text))
    await state.set_state(AddMovie.title)
    await message.answer("Kino nomini kiriting:")


@router.message(AddMovie.title)
async def add_movie_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddMovie.year)
    await message.answer("Yilini kiriting:")


@router.message(AddMovie.year)
async def add_movie_year(message: Message, state: FSMContext):
    await state.update_data(year=message.text)
    await state.set_state(AddMovie.genre)
    await message.answer("Janrini kiriting:")


@router.message(AddMovie.genre)
async def add_movie_genre(message: Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await state.set_state(AddMovie.duration)
    await message.answer("Davomiyligini kiriting (masalan: 1soat 40daq):")


@router.message(AddMovie.duration)
async def add_movie_duration(message: Message, state: FSMContext):
    await state.update_data(duration=message.text)
    await state.set_state(AddMovie.language)
    await message.answer("Tilini kiriting:")


@router.message(AddMovie.language)
async def add_movie_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    await state.set_state(AddMovie.quality)
    await message.answer("Sifatini kiriting (masalan: HD):")


@router.message(AddMovie.quality)
async def add_movie_quality(message: Message, state: FSMContext):
    await state.update_data(quality=message.text)
    await state.set_state(AddMovie.file)
    await message.answer("Endi kino video faylini yuboring:")


@router.message(AddMovie.file, F.video)
async def add_movie_file(message: Message, state: FSMContext):
    data = await state.get_data()
    db.add_movie(
        data["code"], data["title"], data["year"], data["genre"],
        data["duration"], data["language"], data["quality"],
        message.video.file_id,
    )
    await state.clear()
    await message.answer(f"✅ Kino qo'shildi! Kodi: {data['code']}")


@router.message(AddMovie.file)
async def add_movie_file_invalid(message: Message):
    await message.answer("Iltimos, video fayl yuboring.")


@router.callback_query(F.data == "admin_delete")
async def delete_movie_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(DeleteMovie.waiting)
    await callback.message.answer("O'chirmoqchi bo'lgan kino kodini yuboring:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(DeleteMovie.waiting)
async def delete_movie_process(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Kod raqam bo'lishi kerak.")
        return
    code = int(message.text)
    if not db.code_exists(code):
        await message.answer("Bunday kodli kino topilmadi.")
        return
    db.delete_movie(code)
    await state.clear()
    await message.answer(f"🗑 {code} kodli kino o'chirildi.")


@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(Broadcast.waiting)
    await callback.message.answer("Yubormoqchi bo'lgan xabaringizni yuboring:", reply_markup=cancel_keyboard())
    await callback.answer()


@router.message(Broadcast.waiting)
async def broadcast_process(message: Message, state: FSMContext):
    await state.clear()
    user_ids = db.get_all_user_ids()
    sent, failed = 0, 0
    status = await message.answer(f"⏳ Yuborilmoqda... (0/{len(user_ids)})")
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            failed += 1
    await status.edit_text(f"✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}")
