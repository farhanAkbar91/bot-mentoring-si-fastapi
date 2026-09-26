import logging
import re
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import User
from app.bot.states import BotStates
from app.bot.keyboards import main_menu

router = Router()

TEMPLATE_DB_ERROR = (
    "⚠️ Maaf, terjadi gangguan koneksi ke database.\n"
    "Silakan coba kembali dalam beberapa saat."
)

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        with SessionLocal() as db:
            user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()

        if not user:
            await state.set_state(BotStates.waiting_for_nim)
            await message.answer(
                f"Halo {message.from_user.first_name}! 👋\n\n"
                "Silakan masukkan **NIM** Anda (khusus mahasiswa SI) untuk verifikasi:"
            )
        else:
            await message.answer(
                f"Selamat datang kembali, {user.nama}! Ada yang bisa dibantu?",
                reply_markup=main_menu()
            )
    except SQLAlchemyError as e:
        logging.error(f"[DB] Error pada /start: {e}")
        await message.answer(TEMPLATE_DB_ERROR)

@router.message(BotStates.waiting_for_nim)
async def process_nim(message: types.Message, state: FSMContext):
    nim = message.text.strip()
    # Check NIM format:
    # - Angkatan sebelumnya: starts with 1872, digit for year [3-6], then 4 digits (9 digits total)
    # - Angkatan 2026 baru: starts with 626108112, followed by 3 unique digits (12 digits total)
    if re.match(r"^(1872[3-6]\d{4}|626108112\d{3})$", nim):
        try:
            with SessionLocal() as db:
                new_user = User(
                    telegram_id=str(message.from_user.id),
                    nim=nim,
                    nama=message.from_user.full_name,
                    is_verified=1
                )
                db.add(new_user)
                db.commit()
            await state.clear()
            await message.answer("✅ Verifikasi Berhasil!", reply_markup=main_menu())
        except SQLAlchemyError as e:
            logging.error(f"[DB] Gagal menyimpan user baru: {e}")
            await message.answer(TEMPLATE_DB_ERROR)
    else:
        await message.answer("❌ Format NIM salah. Pastikan Anda mahasiswa Sistem Informasi.")
