from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum


class StatoProgetto(str, enum.Enum):
    PIANIFICATO = "pianificato"
    ATTIVO = "attivo"
    COMPLETATO = "completato"
    SOSPESO = "sospeso"


class PrioritaTask(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BASSA = "bassa"


class StatoTask(str, enum.Enum):
    DA_FARE = "da_fare"
    IN_CORSO = "in_corso"
    COMPLETATO = "completato"
    BLOCCATO = "bloccato"


class Progetto(Base):
    __tablename__ = "progetti"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    nome = Column(String(200), nullable=False)
    cliente = Column(String(200), nullable=True)
    data_inizio = Column(DateTime, nullable=True)
    data_fine_prevista = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    stato = Column(String(20), default=StatoProgetto.PIANIFICATO.value)
    percentuale_avanzamento = Column(Float, default=0)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tasks = relationship("Task", back_populates="progetto")
    timesheet_entries = relationship("Timesheet", back_populates="progetto")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    progetto_id = Column(Integer, ForeignKey("progetti.id"), nullable=False)
    collaboratore_id = Column(Integer, nullable=True)
    titolo = Column(String(200), nullable=False)
    descrizione = Column(Text, nullable=True)
    priorita = Column(String(10), default=PrioritaTask.MEDIA.value)
    stato = Column(String(20), default=StatoTask.DA_FARE.value)
    data_scadenza = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    progetto = relationship("Progetto", back_populates="tasks")


class Timesheet(Base):
    __tablename__ = "timesheet"

    id = Column(Integer, primary_key=True, index=True)
    collaboratore_id = Column(Integer, nullable=False)
    progetto_id = Column(Integer, ForeignKey("progetti.id"), nullable=False)
    data = Column(DateTime, nullable=False)
    ore = Column(Float, nullable=False)
    descrizione_attivita = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    progetto = relationship("Progetto", back_populates="timesheet_entries")
