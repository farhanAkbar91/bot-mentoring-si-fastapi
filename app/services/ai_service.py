import logging
import asyncio
import traceback
from groq import AsyncGroq
from groq import APIConnectionError, APITimeoutError, RateLimitError, APIStatusError
from app.config import settings

class AIService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=20.0)
        self.model = settings.GROQ_MODEL
        self.max_retries = 3
        self.retry_delay = 2.0

    async def chat_with_retry(self, messages: list, model: str = None) -> str:
        model = model or self.model
        delay = self.retry_delay
        for attempt in range(1, self.max_retries + 1):
            try:
                completion = await self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                )
                return completion.choices[0].message.content

            except RateLimitError as e:
                logging.warning(f"[Groq] Rate limit (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(delay * 2)
                    delay *= 2
                else:
                    logging.error("[Groq] Rate limit: semua retry habis.")
                    return "__RATE_LIMITED__"

            except (APIConnectionError, APITimeoutError) as e:
                logging.warning(f"[Groq] Koneksi/Timeout (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logging.error("[Groq] Koneksi gagal: semua retry habis.")
                    return None

            except APIStatusError as e:
                if e.status_code >= 500:
                    logging.warning(f"[Groq] Server error {e.status_code} (attempt {attempt}/{self.max_retries}): {e}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logging.error("[Groq] Server error: semua retry habis.")
                        return None
                else:
                    logging.error(f"[Groq] Client error {e.status_code}: {e}")
                    return None

            except Exception as e:
                logging.error(f"[Groq] Unexpected error (attempt {attempt}/{self.max_retries}): {e}\n{traceback.format_exc()}")
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    return None
        return None

    async def evaluate_mentoring_reason(self, reason: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Kamu adalah Koordinator Lomba HIMA Sistem Informasi. "
                    "Nilailah alasan permintaan mentoring berikut. "
                    "Kriteria utama: mahasiswa harus menunjukkan progres minimal 50% "
                    "(ada tim, ada lomba yang dituju, ada draf/ide). "
                    "Balas dengan format: [SETUJU] atau [TOLAK], diikuti alasan singkat."
                )
            },
            {"role": "user", "content": reason}
        ]
        return await self.chat_with_retry(messages)

    async def categorize_lomba(self, reason: str) -> str:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Dari teks berikut, tentukan kategori lomba yang paling sesuai.\n"
                    f"Teks: '{reason}'\n"
                    f"Pilih SATU dari: UI/UX, WEB, ESAI, DATA\n"
                    f"Balas hanya dengan 1 kata kategorinya saja."
                )
            }
        ]
        response = await self.chat_with_retry(messages)
        if response and response != "__RATE_LIMITED__":
            raw_cat = response.strip().upper()
            kategori_valid = ["UI/UX", "WEB", "ESAI", "DATA"]
            return next((k for k in kategori_valid if k in raw_cat), "WEB")
        return "WEB"

ai_service = AIService()
