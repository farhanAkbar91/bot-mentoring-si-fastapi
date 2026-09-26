from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True)
    nim = Column(String)
    nama = Column(String)
    is_verified = Column(Integer, default=0) # 0: Belum, 1: Terverifikasi

class FAQ(Base):
    __tablename__ = "faq"
    id = Column(Integer, primary_key=True, index=True)
    pertanyaan = Column(String)
    jawaban = Column(Text)
    is_active = Column(Boolean, default=True) # Soft delete flag

class Lomba(Base):
    __tablename__ = "lomba"
    id = Column(Integer, primary_key=True, index=True)
    nama_lomba = Column(String, index=True)
    kategori = Column(String) # Contoh UI/UX, Web Dev, Esai, dll
    deskripsi = Column(Text)
    deadline = Column(String)
    link_info = Column(String)
    is_active = Column(Boolean, default=True) # Soft delete flag

class Mentor(Base):
    __tablename__ = "mentor"
    id = Column(Integer, primary_key=True, index=True)
    nama_mentor = Column(String)
    spesialisasi = Column(String) # Bidang keahlian
    kontak = Column(String) # Nomor WA atau ID Telegram
    is_active = Column(Boolean, default=True) # Soft delete flag

class PermintaanMentoring(Base):
    __tablename__ = "permintaan_mentoring"
    id = Column(Integer, primary_key=True, index=True)
    user_id_telegram = Column(String) # ID pengirim di Telegram
    nama_mahasiswa = Column(String)
    alasan = Column(Text)
    status_ai = Column(String) # 'SETUJU' atau 'TOLAK'
    analisis_ai = Column(Text) # Penjelasan mengapa AI setuju/menolak
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
