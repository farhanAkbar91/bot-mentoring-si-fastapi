import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from aiogram import types
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base, engine, get_db
# Import bot to run its __init__.py registering the router
from app.bot import bot, dp
from app.bot.scheduler import setup_scheduler, shutdown_scheduler
from app.services.sheet_service import sync_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Webhook endpoint mapping
WEBHOOK_PATH = f"/webhook/{settings.TELEGRAM_TOKEN}"
WEBHOOK_URL = f"{settings.clean_webhook_host}{WEBHOOK_PATH}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logging.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    logging.info(f"Setting Telegram webhook to: {WEBHOOK_URL}")
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)

    logging.info("Setting up scheduler...")
    setup_scheduler()
    
    yield

    # --- SHUTDOWN ---
    logging.info("Stopping scheduler...")
    shutdown_scheduler()

    logging.info("Closing bot session...")
    await bot.session.close()

app = FastAPI(
    title="AI Mentoring Bot - FastAPI Backend",
    description="FastAPI migration of Telegram Bot Mentoring SI project",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "app": app.title,
        "version": app.version
    }

@app.post(f"/webhook/{{token}}")
async def telegram_webhook(token: str, request: Request):
    if token != settings.TELEGRAM_TOKEN:
        logging.warning("Unauthorized webhook access attempt!")
        raise HTTPException(status_code=403, detail="Invalid token")
    
    try:
        update_json = await request.json()
        update = types.Update.model_validate(update_json, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Error handling Telegram update: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/sync")
def trigger_sync(
    x_sync_key: str = Header(None, alias="X-Sync-Key"),
    db: Session = Depends(get_db)
):
    """
    Trigger Google Sheets synchronization manually via API.
    Protected by API_SYNC_KEY from .env.
    """
    if settings.API_SYNC_KEY and x_sync_key != settings.API_SYNC_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized - Invalid Sync Key")
    
    success = sync_data(db)
    if success:
        return {"status": "success", "message": "Google Sheets data successfully synchronized"}
    else:
        raise HTTPException(status_code=500, detail="Google Sheets synchronization failed")

if __name__ == "__main__":
    import uvicorn
    # Start web server
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
