from __future__ import annotations

from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class FatturaCreate(BaseModel):
    contract_id: Optional[int] = None
    tipo: str = "attiva"
    numero: str
    importo: float
    iva: float = 22.0
    data_emissione: Optional[str] = None
    data_scadenza: str
    fornitore_o_cliente: str
    note: Optional[str] = None


class FatturaUpdate(BaseModel):
    stato: Optional[str] = None
    data_pagamento: Optional[str] = None
    note: Optional[str] = None


class FatturaResponse(BaseModel):
    id: int
    contract_id: Optional[int]
    tipo: str
    numero: str
    importo: float
    iva: float
    importo_totale: float
    data_emissione: Optional[datetime]
    data_scadenza: Optional[datetime]
    stato: str
    fornitore_o_cliente: str
    note: Optional[str]
    data_pagamento: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CashFlowItem(BaseModel):
    mese: str
    entrate: float
    uscite: float
    saldo: float


class ReportMensile(BaseModel):
    mese: str
    entrate: float
    uscite: float
    saldo: float
    fatture_emesse: int
    fatture_pagate: int
    fatture_scadute: int
    variazione_entrate: Optional[float] = None
    variazione_uscite: Optional[float] = None
