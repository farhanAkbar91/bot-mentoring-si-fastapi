import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Lomba, Mentor, FAQ

def sync_data(db: Session) -> bool:
    try:
        # Load Google Sheets Credentials (env vs credentials.json file)
        creds_json_str = settings.GOOGLE_CREDS_JSON or os.getenv("GOOGLE_CREDS_JSON")
        
        if not creds_json_str:
            # Fallback to local credentials.json file
            cred_file = "credentials.json"
            if os.path.exists(cred_file):
                with open(cred_file, "r") as f:
                    creds_info = json.load(f)
            else:
                logging.error("Google Sheets credentials not found in environment variables or credentials.json file!")
                return False
        else:
            creds_info = json.loads(creds_json_str)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("data bot-aa")

        # --- Sync Lomba ---
        logging.info("Syncing Lomba data...")
        lomba_sheet = sheet.worksheet("Lomba").get_all_records()
        db_lombas = db.query(Lomba).all()
        db_lomba_dict = {l.nama_lomba.strip().lower(): l for l in db_lombas}
        active_lomba_keys = set()

        for row in lomba_sheet:
            name = row.get('Nama Lomba', '').strip()
            if not name:
                continue
            key = name.lower()
            active_lomba_keys.add(key)

            if key in db_lomba_dict:
                # Update existing record and make sure it is active
                l = db_lomba_dict[key]
                l.kategori = row.get('Kategori', '')
                l.deskripsi = row.get('Deskripsi', '')
                l.deadline = str(row.get('Deadline', ''))
                l.link_info = row.get('Link Info', '')
                l.is_active = True
            else:
                # Create a new record
                new_lomba = Lomba(
                    nama_lomba=name,
                    kategori=row.get('Kategori', ''),
                    deskripsi=row.get('Deskripsi', ''),
                    deadline=str(row.get('Deadline', '')),
                    link_info=row.get('Link Info', ''),
                    is_active=True
                )
                db.add(new_lomba)

        # Deactivate Lomba not in the sheet
        for key, l in db_lomba_dict.items():
            if key not in active_lomba_keys:
                l.is_active = False

        # --- Sync Mentor ---
        logging.info("Syncing Mentor data...")
        mentor_sheet = sheet.worksheet("Mentor").get_all_records()
        db_mentors = db.query(Mentor).all()
        db_mentor_dict = {m.nama_mentor.strip().lower(): m for m in db_mentors}
        active_mentor_keys = set()

        for row in mentor_sheet:
            name = row.get('Nama Mentor', '').strip()
            if not name:
                continue
            key = name.lower()
            active_mentor_keys.add(key)

            if key in db_mentor_dict:
                m = db_mentor_dict[key]
                m.spesialisasi = row.get('Spesialisasi', '')
                m.kontak = str(row.get('Kontak', ''))
                m.is_active = True
            else:
                new_mentor = Mentor(
                    nama_mentor=name,
                    spesialisasi=row.get('Spesialisasi', ''),
                    kontak=str(row.get('Kontak', '')),
                    is_active=True
                )
                db.add(new_mentor)

        # Deactivate Mentor not in the sheet
        for key, m in db_mentor_dict.items():
            if key not in active_mentor_keys:
                m.is_active = False

        # --- Sync FAQ ---
        logging.info("Syncing FAQ data...")
        faq_sheet = sheet.worksheet("FAQ").get_all_records()
        db_faqs = db.query(FAQ).all()
        db_faq_dict = {f.pertanyaan.strip().lower(): f for f in db_faqs}
        active_faq_keys = set()

        for row in faq_sheet:
            question = row.get('Pertanyaan', '').strip()
            if not question:
                continue
            key = question.lower()
            active_faq_keys.add(key)

            if key in db_faq_dict:
                f = db_faq_dict[key]
                f.jawaban = row.get('Jawaban', '')
                f.is_active = True
            else:
                new_faq = FAQ(
                    pertanyaan=question,
                    jawaban=row.get('Jawaban', ''),
                    is_active=True
                )
                db.add(new_faq)

        # Deactivate FAQ not in the sheet
        for key, f in db_faq_dict.items():
            if key not in active_faq_keys:
                f.is_active = False

        db.commit()
        logging.info("Sync completed successfully!")
        return True

    except Exception as e:
        logging.error(f"Error during Google Sheets synchronization: {e}")
        db.rollback()
        return False
