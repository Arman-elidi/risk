from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from datetime import datetime
from app.core.auth import auth_bearer
from app.schemas.batch import BatchTriggerRequest, BatchStatus

router = APIRouter()

# In-memory placeholder
_BATCHES = {}


@router.post("/batch/nightly/trigger", response_model=BatchStatus, status_code=201)
def trigger_nightly_batch(body: BatchTriggerRequest, user=Depends(auth_bearer)):
    batch_id = f"batch_{uuid4().hex[:8]}"
    batch = BatchStatus(
        batch_id=batch_id,
        status="QUEUED",
        started_at=datetime.utcnow(),
        finished_at=None,
        portfolios_total=0,
        portfolios_completed=0,
        errors=0,
    )
    _BATCHES[batch_id] = batch
    # In a real implementation, enqueue nightly batch job
    return batch


@router.get("/batch/{batch_id}", response_model=BatchStatus)
def get_batch_status(batch_id: str, user=Depends(auth_bearer)):
    if batch_id not in _BATCHES:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Batch not found"})
    return _BATCHES[batch_id]


@router.get("/batch/{batch_id}/snapshots")
def get_batch_snapshots(batch_id: str, user=Depends(auth_bearer)):
    if batch_id not in _BATCHES:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Batch not found"})
    # Return snapshot headers for the batch (placeholder)
    return []
