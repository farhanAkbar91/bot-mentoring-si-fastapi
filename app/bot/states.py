from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    waiting_for_nim = State()
    waiting_for_reason = State()
