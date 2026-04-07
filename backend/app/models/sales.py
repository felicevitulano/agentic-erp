from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum


class PipelineState(str, enum.Enum):
    LEAD = "lead"
    QUALIFICATO = "qualificato"
    PROPOSTA = "proposta"
    NEGOZIAZIONE = "negoziazione"
    VINTO = "vinto"
    PERSO = "perso"


VALID_TRANSITIONS = {
    PipelineState.LEAD: [PipelineState.QUALIFICATO, PipelineState.PERSO],
    PipelineState.QUALIFICATO: [PipelineState.PROPOSTA, PipelineState.PERSO],
    PipelineState.PROPOSTA: [PipelineState.NEGOZIAZIONE, PipelineState.PERSO],
    PipelineState.NEGOZIAZIONE: [PipelineState.VINTO, PipelineState.PERSO],
    PipelineState.VINTO: [],
    PipelineState.PERSO: [],
}


class LossReason(str, enum.Enum):
    COMPETITOR = "competitor"
    PREZZO = "prezzo"
    TIMING = "timing"
    BUDGET = "budget"
    ALTRO = "altro"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cognome = Column(String(100), nullable=False)
    azienda = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    ruolo = Column(String(100), nullable=True)
    fonte = Column(String(100), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    opportunities = relationship("Opportunity", back_populates="contact")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    titolo = Column(String(200), nullable=False)
    valore_stimato = Column(Float, nullable=False)
    stato = Column(String(20), default=PipelineState.LEAD.value)
    probabilita_chiusura = Column(Integer, default=10)
    data_chiusura_prevista = Column(DateTime, nullable=True)
    motivo_perdita = Column(String(20), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contact = relationship("Contact", back_populates="opportunities")
    contract = relationship("Contract", back_populates="opportunity", uselist=False)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    titolo = Column(String(200), nullable=False)
    valore_totale = Column(Float, nullable=False)
    data_inizio = Column(DateTime, nullable=True)
    data_fine = Column(DateTime, nullable=True)
    stato = Column(String(20), default="attivo")  # attivo, completato, sospeso
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="contract")
    sal_entries = relationship("SAL", back_populates="contract", order_by="SAL.numero_sal")


class SAL(Base):
    __tablename__ = "sal"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    numero_sal = Column(Integer, nullable=False)
    descrizione = Column(Text, nullable=True)
    percentuale_avanzamento = Column(Float, nullable=False)
    importo_maturato = Column(Float, nullable=False)
    data_sal = Column(DateTime(timezone=True), server_default=func.now())
    note = Column(Text, nullable=True)

    contract = relationship("Contract", back_populates="sal_entries")
