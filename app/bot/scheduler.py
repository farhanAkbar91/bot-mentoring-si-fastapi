import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.models import Lomba, User
from app.bot.bot_instance import bot

scheduler = AsyncIOScheduler()

async def check_deadlines():
    """Checks for competitions ending in the next 3 days and notifies verified users."""
    today = datetime.now()
    three_days_later = today + timedelta(days=3)
    
    logging.info("Checking upcoming competition deadlines...")
    try:
        with SessionLocal() as db:
            # Query only active competitions
            semua_lomba = db.query(Lomba).filter(Lomba.is_active == True).all()
            users = db.query(User).filter(User.is_verified == 1).all()
    except SQLAlchemyError as e:
        logging.error(f"[Reminder] Gagal ambil data dari DB: {e}")
        return

    upcoming_lomba = []
    for l in semua_lomba:
        try:
            # Expected date format YYYY-MM-DD
            deadline_date = datetime.strptime(l.deadline, "%Y-%m-%d")
            if today <= deadline_date <= three_days_later:
                upcoming_lomba.append(l)
        except ValueError:
            continue

    if upcoming_lomba and users:
        for user in users:
            msg = "🔔 **PENGINGAT DEADLINE LOMBA** 🔔\n\n"
            for l in upcoming_lomba:
                msg += f"⚠️ **{l.nama_lomba}**\n📅 Deadline: {l.deadline}\n"
            msg += "\nSegera selesaikan progres Anda dan ajukan mentoring jika butuh bantuan!"
            try:
                await bot.send_message(user.telegram_id, msg, parse_mode="Markdown")
            except Exception as e:
                logging.error(f"[Reminder] Gagal kirim ke {user.telegram_id}: {e}")

def setup_scheduler():
    scheduler.add_job(check_deadlines, 'cron', hour=8, minute=0)
    scheduler.start()
    logging.info("APScheduler started successfully.")

def shutdown_scheduler():
    scheduler.shutdown()
    logging.info("APScheduler shut down successfully.")
