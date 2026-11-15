import io
import json
import logging
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.crew import CrewMember
from app.models.events import HealthEvent
from app.models.reports import MissionReport

logger = logging.getLogger(__name__)

async def generate_mission_report(session: AsyncSession, mission_day: int = 1) -> MissionReport:
    # 1. Fetch crew members
    crew_res = await session.execute(select(CrewMember))
    crew_list = crew_res.scalars().all()

    # 2. Fetch health events
    events_res = await session.execute(
        select(HealthEvent).order_by(desc(HealthEvent.created_at)).limit(50)
    )
    events = events_res.scalars().all()

    emergency_count = sum(1 for e in events if e.to_status == "EMERGENCY")
    anomaly_count = sum(1 for e in events if e.to_status == "ANOMALY")
    total_events = len(events)

    summary_text = (
        f"Mission Health Report Day {mission_day}. Total Events: {total_events}. "
        f"Emergencies: {emergency_count}, Anomalies: {anomaly_count}. "
        f"All crew vitals evaluated under NASA Space Apps telemetry rules."
    )

    report_payload = {
        "mission_day": mission_day,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_events": total_events,
        "emergency_count": emergency_count,
        "anomaly_count": anomaly_count,
        "crew_summary": [
            {"id": str(c.id), "name": c.name, "role": c.role, "responder": c.responder_name}
            for c in crew_list
        ],
        "recent_events": [
            {
                "crew_id": str(e.crew_member_id),
                "from_status": e.from_status,
                "to_status": e.to_status,
                "triggered_by": e.triggered_by,
                "guidance": e.guidance_text,
                "acknowledged": e.acknowledged,
                "timestamp": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events[:15]
        ]
    }

    # Generate PDF in-memory buffer
    pdf_filename = f"mission_report_day_{mission_day}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
    
    report = MissionReport(
        mission_day=mission_day,
        total_events=total_events,
        emergency_count=emergency_count,
        anomaly_count=anomaly_count,
        summary_text=summary_text,
        pdf_filename=pdf_filename,
        report_data=report_payload,
    )

    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report

def build_pdf_buffer(report: MissionReport) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14
    )
    elements.append(Paragraph("🚀 CrewWatch — Astronaut Mission Health Report", title_style))
    elements.append(Paragraph(f"<b>Mission Day:</b> {report.mission_day} | <b>Generated:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # Overview Metrics Table
    data_summary = [
        ["Total Events Logged", "Emergency Incidents", "Anomaly Events"],
        [str(report.total_events), str(report.emergency_count), str(report.anomaly_count)]
    ]
    t_summary = Table(data_summary, colWidths=[180, 180, 180])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t_summary)
    elements.append(Spacer(1, 20))

    # Narrative Summary
    elements.append(Paragraph("<b>Executive Summary:</b>", styles['Heading3']))
    elements.append(Paragraph(report.summary_text or "No summary available.", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Events Table
    elements.append(Paragraph("<b>Recent Health & Anomaly Log:</b>", styles['Heading3']))
    events_data = [["Status", "Trigger", "Guidance", "Acknowledged"]]
    
    recent_events = (report.report_data or {}).get("recent_events", [])
    if recent_events:
        for ev in recent_events[:10]:
            ack_str = "Yes" if ev.get("acknowledged") else "Pending"
            events_data.append([
                ev.get("to_status", "NOMINAL"),
                ev.get("triggered_by", "—"),
                Paragraph(ev.get("guidance", "—")[:90] + "...", styles['Normal']),
                ack_str
            ])
    else:
        events_data.append(["NOMINAL", "None", "All vitals stable across mission.", "N/A"])

    t_events = Table(events_data, colWidths=[80, 90, 290, 80])
    t_events.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_events)

    doc.build(elements)
    buffer.seek(0)
    return buffer
