import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_bank_id() -> str:
    """Random, globally unique Hindsight bank id.

    Deliberately NOT derived from the row id: if the local database is ever reset, row ids restart
    at 1 and a new customer would otherwise inherit an old customer's memories.
    """
    return f"{get_settings().hindsight_bank_prefix}-{uuid.uuid4().hex[:16]}"


class Customer(Base):
    """CRM record. This is NOT memory - memory lives in Hindsight."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str] = mapped_column(String(200), default="")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_id: Mapped[str] = mapped_column(String(100), unique=True, default=new_bank_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", order_by="Interaction.occurred_at"
    )


class Interaction(Base):
    """Activity log row. `retained` says whether it was sent to Hindsight."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(50), default="note")
    content: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    retained: Mapped[bool] = mapped_column(Boolean, default=False)
    retain_error: Mapped[str] = mapped_column(Text, default="")

    customer: Mapped[Customer] = relationship(back_populates="interactions")
