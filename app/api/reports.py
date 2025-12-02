from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import auth_bearer
from app.db.session import get_db
from app.services.pdf_report import generate_daily_pdf

router = APIRouter()


@router.post("/reports/pdf/generate")
async def generate_pdf_report(
    report_date: date = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(auth_bearer),
):
    """
    Generate PDF report on-demand
    
    Args:
        report_date: Date for report (default: today)
    
    Returns:
        File path to generated PDF
    """
    if report_date is None:
        report_date = date.today()
    
    file_path = await generate_daily_pdf(db, report_date)
    
    return {"file_path": file_path, "report_date": str(report_date)}


@router.get("/reports/pdf/download")
async def download_pdf_report(
    report_date: date,
    user=Depends(auth_bearer),
):
    """Download PDF report for specific date"""
    import os
    file_path = f"/tmp/risk_reports/risk_report_{report_date}.pdf"
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Report for {report_date} not found"}
        )
    
    return FileResponse(
        file_path,
        media_type='application/pdf',
        filename=f"risk_report_{report_date}.pdf"
    )
