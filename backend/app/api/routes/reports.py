from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from app.database import get_db
from app.models.reports import MissionReport
from app.schemas.reports import ReportGenerateRequest, ReportResponse
from app.core.report_generator import generate_mission_report, build_pdf_buffer

router = APIRouter(prefix="/api/reports", tags=["Mission Health Reports"])

@router.post("/generate", response_model=ReportResponse, status_code=201)
async def trigger_report(
    req: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    report = await generate_mission_report(db, mission_day=req.mission_day)
    return report

@router.get("", response_model=list[ReportResponse])
async def list_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MissionReport).order_by(desc(MissionReport.generated_at))
    )
    return result.scalars().all()

@router.get("/{report_id}")
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    report = await db.get(MissionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Mission report not found")
    return report

@router.get("/{report_id}/download")
async def download_pdf_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    report = await db.get(MissionReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Mission report not found")

    pdf_buffer = build_pdf_buffer(report)
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={report.pdf_filename or 'mission_report.pdf'}"
        }
    )
