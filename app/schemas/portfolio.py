from datetime import date
from typing import Optional
from pydantic import BaseModel

class Portfolio(BaseModel):
    id: int
    name: str
    portfolio_type: str  # BOND_DEALER / DERIVATIVES_CLIENT / PROPRIETARY / MIXED
    base_currency: str
    status: str  # ACTIVE/FROZEN/CLOSED
    counterparty_id: Optional[int] = None

class PortfolioCreate(BaseModel):
    name: str
    portfolio_type: str
    base_currency: str
    status: str = "ACTIVE"
    counterparty_id: Optional[int] = None

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    portfolio_type: Optional[str] = None
    base_currency: Optional[str] = None
    status: Optional[str] = None
    counterparty_id: Optional[int] = None

class PortfolioStatusPatch(BaseModel):
    status: str
