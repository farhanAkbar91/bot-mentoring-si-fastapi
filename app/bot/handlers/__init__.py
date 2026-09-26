from aiogram import Router
from .base import router as base_router
from .admin import router as admin_router
from .faq import router as faq_router
from .mentoring import router as mentoring_router

bot_router = Router()
bot_router.include_router(base_router)
bot_router.include_router(admin_router)
bot_router.include_router(faq_router)
bot_router.include_router(mentoring_router)
