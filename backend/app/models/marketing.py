from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.models.database import Base
import enum


class TipoContenuto(str, enum.Enum):
    POST_LINKEDIN = "post_linkedin"
    ARTICOLO_BLOG = "articolo_blog"
    CASE_STUDY = "case_study"


class StatoContenuto(str, enum.Enum):
    BOZZA = "bozza"
    IN_REVISIONE = "in_revisione"
    PUBBLICATO = "pubblicato"


class Contenuto(Base):
    __tablename__ = "contenuti"

    id = Column(Integer, primary_key=True, index=True)
    titolo = Column(String(300), nullable=False)
    tipo = Column(String(30), nullable=False, default=TipoContenuto.POST_LINKEDIN.value)
    stato = Column(String(20), nullable=False, default=StatoContenuto.BOZZA.value)
    data_pubblicazione = Column(DateTime, nullable=True)
    autore = Column(String(100), nullable=True)
    contenuto_testo = Column(Text, nullable=True)
    metriche = Column(JSON, nullable=True)  # {views, likes, comments, shares}
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContattoEvento(Base):
    __tablename__ = "contatti_evento"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    azienda = Column(String(200), nullable=True)
    evento = Column(String(200), nullable=False)
    data_evento = Column(DateTime, nullable=True)
    interesse = Column(String(200), nullable=True)
    note = Column(Text, nullable=True)
    convertito_a_contatto_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
