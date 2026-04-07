from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum


class TipoFattura(str, enum.Enum):
    ATTIVA = "attiva"
    PASSIVA = "passiva"


class StatoFattura(str, enum.Enum):
    EMESSA = "emessa"
    PAGATA = "pagata"
    SCADUTA = "scaduta"


class Fattura(Base):
    __tablename__ = "fatture"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    tipo = Column(String(10), nullable=False, default=TipoFattura.ATTIVA.value)
    numero = Column(String(50), nullable=False, unique=True)
    importo = Column(Float, nullable=False)
    iva = Column(Float, nullable=False, default=22.0)
    importo_totale = Column(Float, nullable=False)
    data_emissione = Column(DateTime(timezone=True), server_default=func.now())
    data_scadenza = Column(DateTime(timezone=True), nullable=False)
    stato = Column(String(20), nullable=False, default=StatoFattura.EMESSA.value)
    fornitore_o_cliente = Column(String(200), nullable=False)
    note = Column(Text, nullable=True)
    data_pagamento = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contract = relationship("Contract", backref="fatture")
