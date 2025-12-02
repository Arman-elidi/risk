from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.core.auth import auth_bearer
from app.schemas.portfolio import Portfolio, PortfolioCreate, PortfolioUpdate, PortfolioStatusPatch

router = APIRouter()

# In-memory placeholder
_PORTFOLIOS = {
    1: Portfolio(
        id=1,
        name="RISK_BOND_BOOK",
        portfolio_type="BOND_DEALER",
        base_currency="USD",
        status="ACTIVE",
    )
}
_NEXT_ID = 2


@router.get("/portfolios", response_model=List[Portfolio])
def list_portfolios(
    status: Optional[str] = None,
    portfolio_type: Optional[str] = None,
    user=Depends(auth_bearer),
):
    results = list(_PORTFOLIOS.values())
    if status:
        results = [p for p in results if p.status == status]
    if portfolio_type:
        results = [p for p in results if p.portfolio_type == portfolio_type]
    return results


@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
def get_portfolio(portfolio_id: int, user=Depends(auth_bearer)):
    if portfolio_id not in _PORTFOLIOS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Portfolio not found"})
    return _PORTFOLIOS[portfolio_id]


@router.post("/portfolios", response_model=Portfolio, status_code=201)
def create_portfolio(body: PortfolioCreate, user=Depends(auth_bearer)):
    global _NEXT_ID
    new_id = _NEXT_ID
    _NEXT_ID += 1
    p = Portfolio(id=new_id, **body.dict())
    _PORTFOLIOS[new_id] = p
    return p


@router.put("/portfolios/{portfolio_id}", response_model=Portfolio)
def update_portfolio(portfolio_id: int, body: PortfolioUpdate, user=Depends(auth_bearer)):
    if portfolio_id not in _PORTFOLIOS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Portfolio not found"})
    existing = _PORTFOLIOS[portfolio_id]
    updated = existing.copy(update=body.dict(exclude_unset=True))
    _PORTFOLIOS[portfolio_id] = updated
    return updated


@router.patch("/portfolios/{portfolio_id}/status", response_model=Portfolio)
def patch_portfolio_status(portfolio_id: int, body: PortfolioStatusPatch, user=Depends(auth_bearer)):
    if portfolio_id not in _PORTFOLIOS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Portfolio not found"})
    existing = _PORTFOLIOS[portfolio_id]
    updated = existing.copy(update={"status": body.status})
    _PORTFOLIOS[portfolio_id] = updated
    return updated
