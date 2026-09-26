import logging
from aiogram import Router, types
from aiogram.filters import Command
from app.config import settings
from app.database import SessionLocal
from app.services.sheet_service import sync_data

router = Router()

@router.message(Command("sync"))
async def cmd_sync(message: types.Message):
    if str(message.from_user.id) not in settings.admin_ids:
        await message.answer("⚠️ Maaf, perintah ini khusus untuk akses Admin/Staf HIMA.")
        return

    m = await message.answer("🔄 Sedang menyinkronkan data Lomba, Mentor, dan FAQ dari Google Sheets...")
    
    try:
        with SessionLocal() as db:
            hasil = sync_data(db)
        if hasil:
            await m.edit_text("✅ Sinkronisasi berhasil! Database kini menggunakan data terbaru (dan menonaktifkan data lama yang terhapus).")
        else:
            await m.edit_text("❌ Sinkronisasi gagal. Cek log server untuk detailnya.")
    except Exception as e:
        logging.error(f"[Sync] Gagal sync via command: {e}")
        await m.edit_text(f"❌ Terjadi kesalahan sistem saat sinkronisasi:\n`{str(e)[:200]}`", parse_mode="Markdown")
