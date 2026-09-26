import logging
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import Mentor, PermintaanMentoring
from app.services.ai_service import ai_service
from app.bot.states import BotStates
from app.bot.keyboards import main_menu, cancel_mentoring_menu

router = Router()

TEMPLATE_DB_ERROR = (
    "⚠️ Maaf, terjadi gangguan koneksi ke database.\n"
    "Silakan coba kembali dalam beberapa saat."
)

TEMPLATE_AI_ERROR = (
    "⚠️ Maaf, sistem AI sedang tidak dapat diakses saat ini.\n\n"
    "Kamu tetap bisa menggunakan fitur berikut:\n"
    "• Ketuk *🏆 Info Lomba* untuk melihat lomba aktif\n"
    "• Ketuk *👨‍🏫 Minta Mentoring* untuk menghubungi mentor\n"
    "• Ketuk *❓ FAQ* untuk pertanyaan umum\n\n"
    "Coba lagi beberapa saat kemudian ya 🙂"
)

TEMPLATE_AI_RATE_LIMIT = (
    "⏳ Sistem sedang sibuk, mohon coba lagi dalam beberapa menit.\n\n"
    "Sementara itu, kamu bisa menggunakan menu utama di bawah."
)

@router.callback_query(F.data == "req_mentor")
async def start_mentoring(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_reason)
    await callback.message.answer(
        "📝 **Formulir Mentoring**\n\nJelaskan progres tim Anda (Lomba apa, tim, draf idea). "
        "AI akan mengevaluasi kelayakan Anda mendapatkan mentor.",
        reply_markup=cancel_mentoring_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_request")
async def process_cancel_click(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Permintaan mentoring telah dibatalkan.")
    await callback.message.answer("Ada hal lain yang bisa saya bantu?", reply_markup=main_menu())
    await callback.answer()

@router.message(BotStates.waiting_for_reason)
async def process_mentoring_reason(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    
    # Anti-Spam check (30 minutes cooldown)
    try:
        with SessionLocal() as db:
            last_req = (
                db.query(PermintaanMentoring)
                .filter_by(user_id_telegram=user_id)
                .order_by(PermintaanMentoring.timestamp.desc())
                .first()
            )
            if last_req and (datetime.utcnow() - last_req.timestamp < timedelta(minutes=30)):
                await message.answer("⚠️ Mohon tunggu 30 menit sebelum mengajukan kembali.")
                return
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal cek anti-spam: {e}")
        await message.answer(TEMPLATE_DB_ERROR)
        return

    if len(message.text) < 30:
        await message.answer("⚠️ Alasan terlalu singkat (min. 30 karakter).")
        return

    thinking_msg = await message.answer("🔍 Mengevaluasi alasan dengan AI...")

    # Evaluate reason with AI Service
    ai_response = await ai_service.evaluate_mentoring_reason(message.text)

    # Handle AI Service errors
    if ai_response is None:
        await thinking_msg.delete()
        await message.answer(TEMPLATE_AI_ERROR, reply_markup=main_menu())
        await state.clear()
        return

    if ai_response == "__RATE_LIMITED__":
        await thinking_msg.delete()
        await message.answer(TEMPLATE_AI_RATE_LIMIT, reply_markup=main_menu())
        await state.clear()
        return

    log_status = "TOLAK"
    if "[SETUJU]" in ai_response.upper():
        log_status = "SETUJU"
        
        # Categorize competition category using AI
        cat = await ai_service.categorize_lomba(message.text)

        try:
            with SessionLocal() as db:
                # Find matching active mentor
                mentor = (
                    db.query(Mentor)
                    .filter(Mentor.spesialisasi.ilike(f"%{cat}%"), Mentor.is_active == True)
                    .first()
                    or db.query(Mentor).filter(Mentor.is_active == True).first()
                )
            
            if mentor:
                res_text = (
                    f"✅ **DISETUJUI**\n\n{ai_response}\n\n"
                    f"Hubungi: **{mentor.nama_mentor}**\n"
                    f"WA: https://wa.me/{mentor.kontak}"
                )
            else:
                res_text = (
                    f"✅ **DISETUJUI**\n\n{ai_response}\n\n"
                    "Silakan hubungi admin HIMA untuk mendapatkan mentor yang tersedia."
                )
        except SQLAlchemyError as e:
            logging.error(f"[DB] Gagal ambil mentor: {e}")
            res_text = (
                f"✅ **DISETUJUI**\n\n{ai_response}\n\n"
                "⚠️ Data mentor tidak dapat diambil saat ini. Hubungi admin HIMA."
            )

        await thinking_msg.delete()
        await message.answer(res_text, parse_mode="Markdown")
    else:
        await thinking_msg.delete()
        await message.answer(f"❌ **DITOLAK**\n\n{ai_response}", parse_mode="Markdown")

    # Save request log into DB
    try:
        with SessionLocal() as db:
            new_log = PermintaanMentoring(
                user_id_telegram=user_id,
                nama_mahasiswa=message.from_user.full_name,
                alasan=message.text,
                status_ai=log_status,
                analisis_ai=ai_response
            )
            db.add(new_log)
            db.commit()
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal simpan log mentoring: {e}")

    await state.clear()
