from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String,
        default="queued",
    )

    total_contacts: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    completed_contacts: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    failed_contacts: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    campaign = relationship(
        "Campaign",
        back_populates="jobs",
    )