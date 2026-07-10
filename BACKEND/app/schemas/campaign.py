from pydantic import BaseModel
from typing import List

from app.schemas.contact import ContactCreate


class CampaignCreate(BaseModel):
    campaign_name: str
    agent: str
    script: str
    schedule_date: str
    schedule_time: str

    contacts: List[ContactCreate]