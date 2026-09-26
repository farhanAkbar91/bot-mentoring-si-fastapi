from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏆 Info Lomba", callback_data="list_lomba"))
    builder.row(types.InlineKeyboardButton(text="👨‍🏫 Minta Mentoring", callback_data="req_mentor"))
    builder.row(types.InlineKeyboardButton(text="❓ FAQ", callback_data="faq"))
    return builder.as_markup()

def cancel_mentoring_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="❌ Batalkan Permintaan", callback_data="cancel_request"))
    return builder.as_markup()
