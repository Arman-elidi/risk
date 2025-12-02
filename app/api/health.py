from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"]) 
def health():
    return {"status": "OK", "version": "2.1"}
