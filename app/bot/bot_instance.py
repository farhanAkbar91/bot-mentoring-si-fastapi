from aiogram import Bot, Dispatcher
from app.config import settings

bot = Bot(token=settings.TELEGRAM_TOKEN)
dp = Dispatcher()
