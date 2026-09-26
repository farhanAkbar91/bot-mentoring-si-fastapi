from .bot_instance import bot, dp
from .handlers import bot_router

# Include all command/event handlers into dispatcher
dp.include_router(bot_router)
