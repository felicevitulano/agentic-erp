from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.models.database import Base
import enum


class TipoCollaboratore(str, enum.Enum):
    DIPENDENTE = "dipendente"
    CONSULENTE = "consulente"


class StatoCollaboratore(str, enum.Enum):
    ATTIVO = "attivo"
    INATTIVO = "inattivo"


class TipoAssenza(str, enum.Enum):
    FERIE = "ferie"
    PERMESSO = "permesso"
    MALATTIA = "malattia"


class StatoAssenza(str, enum.Enum):
    RICHIESTA = "richiesta"
    APPROVATA = "approvata"
    RIFIUTATA = "rifiutata"


class Collaboratore(Base):
    __tablename__ = "collaboratori"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False, default=TipoCollaboratore.CONSULENTE.value)
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    tariffa_giornaliera = Column(Float, nullable=True)
    competenze = Column(JSON, nullable=True)  # list of strings
    data_inizio_contratto = Column(DateTime, nullable=True)
    data_fine_contratto = Column(DateTime, nullable=True)
    stato = Column(String(20), default=StatoCollaboratore.ATTIVO.value)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Presenza(Base):
    __tablename__ = "presenze"

    id = Column(Integer, primary_key=True, index=True)
    collaboratore_id = Column(Integer, nullable=False)
    data = Column(DateTime, nullable=False)
    ore = Column(Float, nullable=False, default=8.0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Assenza(Base):
    __tablename__ = "assenze"

    id = Column(Integer, primary_key=True, index=True)
    collaboratore_id = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False, default=TipoAssenza.FERIE.value)
    data_inizio = Column(DateTime, nullable=False)
    data_fine = Column(DateTime, nullable=False)
    stato = Column(String(20), default=StatoAssenza.RICHIESTA.value)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
