from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.core.auth import auth_bearer
from app.schemas.limit import Limit, LimitCreate, LimitUpdate, LimitActivePatch

router = APIRouter()

# In-memory placeholder
_LIMITS = {}
_NEXT_LIMIT_ID = 1


@router.get("/limits", response_model=List[Limit])
def list_limits(
    portfolio_id: Optional[int] = None,
    limit_type: Optional[str] = None,
    active: Optional[bool] = None,
    user=Depends(auth_bearer),
):
    results = list(_LIMITS.values())
    if portfolio_id is not None:
        results = [lim for lim in results if lim.portfolio_id == portfolio_id]
    if limit_type:
        results = [lim for lim in results if lim.limit_type == limit_type]
    if active is not None:
        results = [lim for lim in results if lim.active == active]
    return results


@router.post("/limits", response_model=Limit, status_code=201)
def create_limit(body: LimitCreate, user=Depends(auth_bearer)):
    global _NEXT_LIMIT_ID
    new_id = _NEXT_LIMIT_ID
    _NEXT_LIMIT_ID += 1
    lim = Limit(id=new_id, **body.dict())
    _LIMITS[new_id] = lim
    return lim


@router.put("/limits/{limit_id}", response_model=Limit)
def update_limit(limit_id: int, body: LimitUpdate, user=Depends(auth_bearer)):
    if limit_id not in _LIMITS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Limit not found"})
    existing = _LIMITS[limit_id]
    updated = existing.copy(update=body.dict(exclude_unset=True))
    _LIMITS[limit_id] = updated
    return updated


@router.patch("/limits/{limit_id}/active", response_model=Limit)
def patch_limit_active(limit_id: int, body: LimitActivePatch, user=Depends(auth_bearer)):
    if limit_id not in _LIMITS:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Limit not found"})
    existing = _LIMITS[limit_id]
    updated = existing.copy(update={"active": body.active})
    _LIMITS[limit_id] = updated
    return updated
