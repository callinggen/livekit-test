from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.call import Call
from app.models.contact import Contact
from app.models.campaign import Campaign
from app.services.call_service import CallService

router = APIRouter()


class CallCompleteRequest(BaseModel):
    """All fields are optional so the endpoint works with an empty body too."""
    transcript: Optional[str] = None
    customer_name: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None


def _fmt_duration(seconds: int) -> str:
    """Convert integer seconds → 'MM:SS' string."""
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"


def _parse_transcript(raw: Optional[str]) -> list:
    """
    Convert flat transcript string  →  [{speaker, text}] list the frontend expects.
    Format stored in DB:  "assistant: Hello\nuser: Hi there"
    """
    if not raw:
        return []
    lines = []
    for line in raw.strip().splitlines():
        if ": " in line:
            speaker, _, text = line.partition(": ")
            lines.append({"speaker": speaker.strip(), "text": text.strip()})
    return lines


# ── POST /api/calls/{call_id}/complete ─────────────────────────────────────

@router.post("/calls/{call_id}/complete")
async def complete_call(
    call_id: int,
    body: Optional[CallCompleteRequest] = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    call = await CallService.complete_call(
        db=db,
        call_id=call_id,
        transcript=body.transcript if body else None,
        customer_name=body.customer_name if body else None,
        appointment_date=body.appointment_date if body else None,
        appointment_time=body.appointment_time if body else None,
    )

    if call is None:
        return {"success": False, "message": "Call not found"}

    return {"success": True, "call_id": call.id}


# ── GET /api/calls ──────────────────────────────────────────────────────────

@router.get("/calls")
async def list_calls(db: AsyncSession = Depends(get_db)):
    """
    Return all calls joined with their contact and campaign info.
    Used by the Responses page.
    """
    result = await db.execute(
        select(Call, Contact, Campaign)
        .join(Contact, Call.contact_id == Contact.id)
        .join(Campaign, Contact.campaign_id == Campaign.id)
        .order_by(Call.id.desc())
    )
    rows = result.all()

    calls = []
    for call, contact, campaign in rows:
        calls.append({
            "id": str(call.id),
            "name": contact.customer_name or contact.name,
            "phone": contact.phone,
            "status": call.status.capitalize(),
            "response": contact.response or "—",
            "datetime": call.started_at.strftime("%Y-%m-%d %H:%M") if call.started_at else "",
            "campaign": campaign.campaign_name,
            "duration": _fmt_duration(call.duration or 0),
            "transcript": _parse_transcript(call.transcript),
            "summary": "",
            "notes": f"Appointment: {contact.appointment_date or '—'} at {contact.appointment_time or '—'}",
            "appointment_date": contact.appointment_date or "",
            "appointment_time": contact.appointment_time or "",
            "customer_name": contact.customer_name or contact.name,
        })
    return calls