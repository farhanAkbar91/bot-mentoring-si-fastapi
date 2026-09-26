import logging
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import Lomba, FAQ, Mentor
from app.services.ai_service import ai_service
from app.bot.keyboards import main_menu

router = Router()

TEMPLATE_OUT_OF_CONTEXT = (
    "Maaf, pertanyaan tersebut berada di luar topik yang bisa saya bantu 🙏\n\n"
    "Saya adalah asisten khusus untuk mahasiswa Sistem Informasi yang bisa membantu soal:\n"
    "• 🏆 Informasi & deadline lomba\n"
    "• 👨‍🏫 Permintaan sesi mentoring\n"
    "• ❓ FAQ seputar himpunan & akademik\n\n"
    "Silakan gunakan menu di bawah atau ketik pertanyaan yang sesuai topik di atas."
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

TEMPLATE_DB_ERROR = (
    "⚠️ Maaf, terjadi gangguan koneksi ke database.\n"
    "Silakan coba kembali dalam beberapa saat."
)

@router.callback_query(F.data == "list_lomba")
async def show_lomba(callback: types.CallbackQuery):
    try:
        with SessionLocal() as db:
            # Query only active competitions
            semua_lomba = db.query(Lomba).filter(Lomba.is_active == True).all()
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal ambil data lomba: {e}")
        await callback.message.answer(TEMPLATE_DB_ERROR)
        await callback.answer()
        return
        
    if not semua_lomba:
        await callback.message.answer("Belum ada data lomba aktif bulan ini.")
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for l in semua_lomba:
        builder.row(types.InlineKeyboardButton(
            text=f"🏆 {l.nama_lomba}",
            callback_data=f"detail_lomba_{l.id}"
        ))
    
    await callback.message.answer(
        "📅 **DAFTAR LOMBA AKTIF**\nSilakan pilih lomba untuk melihat detail lebih lanjut:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("detail_lomba_"))
async def show_lomba_detail(callback: types.CallbackQuery):
    lomba_id = int(callback.data.split("_")[-1])
    try:
        with SessionLocal() as db:
            # Check only active lomba
            l = db.query(Lomba).filter(Lomba.id == lomba_id, Lomba.is_active == True).first()
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal ambil detail lomba {lomba_id}: {e}")
        await callback.answer(TEMPLATE_DB_ERROR[:200], show_alert=True)
        return
        
    if not l:
        await callback.answer("Data lomba tidak ditemukan atau sudah tidak aktif.")
        return

    text = (
        f"🏆 **{l.nama_lomba}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📁 **Kategori:** {l.kategori}\n"
        f"📅 **Deadline:** {l.deadline}\n\n"
        f"📝 **Deskripsi:**\n{l.deskripsi}\n\n"
        f"🔗 [Klik di sini untuk info lebih lanjut]({l.link_info})"
    )
    
    await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=False)
    await callback.answer()

@router.callback_query(F.data == "faq")
async def show_faq_list(callback: types.CallbackQuery):
    try:
        with SessionLocal() as db:
            # Query only active FAQ
            faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal ambil data FAQ: {e}")
        await callback.message.answer(TEMPLATE_DB_ERROR)
        await callback.answer()
        return
        
    if not faqs:
        await callback.message.answer("Database FAQ saat ini masih kosong.")
        await callback.answer()
        return

    text = "❓ **FREQUENTLY ASKED QUESTIONS** ❓\n\n"
    for f in faqs:
        text += f"📌 **{f.pertanyaan}**\n└ {f.jawaban}\n\n"
    
    text += "💡 _Anda juga bisa langsung mengetik pertanyaan spesifik untuk dijawab oleh AI._"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.message(F.text)
async def handle_faq(message: types.Message):
    # Ignore commands
    if message.text.startswith("/"):
        return

    try:
        with SessionLocal() as db:
            # Query only active data for context
            faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
            lombas = db.query(Lomba).filter(Lomba.is_active == True).all()
            mentors = db.query(Mentor).filter(Mentor.is_active == True).all()
    except SQLAlchemyError as e:
        logging.error(f"[DB] Gagal ambil knowledge base: {e}")
        await message.answer(TEMPLATE_DB_ERROR)
        return
    
    kb_faq = "\n".join([f"Q: {f.pertanyaan}\nA: {f.jawaban}" for f in faqs])
    kb_lomba = "\n".join([
        f"- {l.nama_lomba} ({l.kategori}): {l.deskripsi}. Deadline: {l.deadline}"
        for l in lombas
    ])
    kb_mentor = "\n".join([f"- {m.nama_mentor} (Ahli: {m.spesialisasi})" for m in mentors])
    
    sys_prompt = (
        "Kamu adalah asisten resmi Himpunan Mahasiswa Sistem Informasi (HIMA SI). "
        "Tugasmu HANYA menjawab pertanyaan seputar topik berikut:\n"
        "1. Informasi lomba yang ada di DATA LOMBA\n"
        "2. Informasi mentor yang ada di DATA MENTOR\n"
        "3. Pertanyaan umum yang ada di DATA FAQ\n"
        "4. Cara mengajukan mentoring\n"
        "5. Info umum tentang HIMA SI\n\n"
        "ATURAN PENTING:\n"
        "- Jika pertanyaan TIDAK berkaitan dengan topik di atas (misalnya: cuaca, politik, "
        "matematika umum, resep makanan, atau hal pribadi), balas PERSIS dengan token ini saja:\n"
        "__OUT_OF_CONTEXT__\n"
        "- Jangan tambahkan penjelasan apapun selain token tersebut untuk pertanyaan di luar topik.\n"
        "- Jika informasi ada tapi tidak lengkap, sampaikan yang ada dan arahkan ke admin HIMA.\n"
        "- Jawablah dengan ramah, singkat, dan informatif.\n\n"
        f"[DATA FAQ]\n{kb_faq or 'Belum ada data FAQ.'}\n\n"
        f"[DATA LOMBA]\n{kb_lomba or 'Belum ada data lomba aktif.'}\n\n"
        f"[DATA MENTOR]\n{kb_mentor or 'Belum ada data mentor.'}"
    )
    
    ai_response = await ai_service.chat_with_retry(
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": message.text}
        ]
    )

    if ai_response is None:
        await message.answer(TEMPLATE_AI_ERROR, reply_markup=main_menu())
        return

    if ai_response == "__RATE_LIMITED__":
        await message.answer(TEMPLATE_AI_RATE_LIMIT, reply_markup=main_menu())
        return

    if "__OUT_OF_CONTEXT__" in ai_response:
        await message.answer(TEMPLATE_OUT_OF_CONTEXT, reply_markup=main_menu())
        return

    await message.answer(ai_response)
