from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

class BatchTriggerRequest(BaseModel):
    as_of_date: Optional[date] = None

class BatchStatus(BaseModel):
    batch_id: str
    status: str  # QUEUED / RUNNING / COMPLETED / FAILED
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    portfolios_total: int
    portfolios_completed: int
    errors: int
