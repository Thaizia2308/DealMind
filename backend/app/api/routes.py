from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Customer, Interaction
from app.schemas import schemas as s
from app.services import hindsight_service as hs
from app.services import intelligence
from app.services.demo_data import DEMO

router = APIRouter(prefix="/api")


# ---------- helpers ----------
def _customer_or_404(db: Session, customer_id: int) -> Customer:
    c = db.get(Customer, customer_id)
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")
    return c


def _count(db: Session, customer_id: int) -> int:
    return db.scalar(select(func.count(Interaction.id)).where(Interaction.customer_id == customer_id)) or 0


def _customer_out(db: Session, c: Customer) -> s.CustomerOut:
    out = s.CustomerOut.model_validate(c)
    out.interaction_count = _count(db, c.id)
    return out


def _try_retain(c: Customer, i: Interaction) -> None:
    """Send an interaction to Hindsight; record success/failure on the row."""
    try:
        hs.retain_interaction(
            bank_id=c.bank_id,
            name=c.name,
            company=c.company,
            industry=c.industry,
            interaction_id=i.id,
            kind=i.kind,
            content=i.content,
            occurred_at=i.occurred_at,
        )
        i.retained = True
        i.retain_error = ""
    except (hs.HindsightNotConfigured, hs.HindsightError) as exc:
        i.retained = False
        i.retain_error = str(exc)


# ---------- health ----------
@router.get("/health")
def health():
    return {"status": "ok", "service": "dealmind-backend"}


@router.get("/memory/status", response_model=s.MemoryStatus)
def memory_status():
    return hs.status()


# ---------- customers ----------
@router.get("/customers", response_model=List[s.CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    rows = db.scalars(select(Customer).order_by(Customer.created_at.desc())).all()
    return [_customer_out(db, c) for c in rows]


@router.post("/customers", response_model=s.CustomerOut, status_code=201)
def create_customer(body: s.CustomerCreate, db: Session = Depends(get_db)):
    c = Customer(name=body.name.strip(), company=body.company.strip(), industry=body.industry.strip())
    db.add(c)
    db.commit()
    db.refresh(c)
    # Best effort: create the customer's memory bank now. It is also created lazily on first retain.
    try:
        hs.ensure_bank(c.bank_id, c.name, c.company, c.industry)
    except (hs.HindsightNotConfigured, hs.HindsightError):
        pass
    return _customer_out(db, c)


@router.get("/customers/{customer_id}", response_model=s.CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return _customer_out(db, _customer_or_404(db, customer_id))


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    try:
        hs.delete_bank(c.bank_id)  # also remove the customer's memory in Hindsight
    except (hs.HindsightNotConfigured, hs.HindsightError):
        pass
    db.delete(c)
    db.commit()


# ---------- interactions ----------
@router.get("/customers/{customer_id}/interactions", response_model=List[s.InteractionOut])
def list_interactions(customer_id: int, db: Session = Depends(get_db)):
    _customer_or_404(db, customer_id)
    return db.scalars(
        select(Interaction).where(Interaction.customer_id == customer_id).order_by(Interaction.occurred_at)
    ).all()


@router.post("/customers/{customer_id}/interactions", response_model=s.InteractionOut, status_code=201)
def add_interaction(customer_id: int, body: s.InteractionCreate, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    when = body.occurred_at or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    i = Interaction(customer_id=c.id, kind=body.kind, content=body.content.strip(), occurred_at=when)
    db.add(i)
    db.commit()
    db.refresh(i)
    _try_retain(c, i)
    db.commit()
    db.refresh(i)
    return i


@router.post("/interactions/{interaction_id}/retry", response_model=s.InteractionOut)
def retry_interaction(interaction_id: int, db: Session = Depends(get_db)):
    i = db.get(Interaction, interaction_id)
    if not i:
        raise HTTPException(status_code=404, detail="Interaction not found")
    _try_retain(i.customer, i)
    db.commit()
    db.refresh(i)
    return i


# ---------- memory + intelligence ----------
@router.post("/customers/{customer_id}/memory/recall", response_model=s.RecallOut)
def recall_memory(customer_id: int, body: s.RecallRequest, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    return {"memories": hs.recall(c.bank_id, body.query)}


@router.post("/customers/{customer_id}/ask", response_model=s.AnswerOut)
def ask_customer(customer_id: int, body: s.AskRequest, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    return intelligence.ask(c, body.question)


@router.post("/customers/{customer_id}/prepare", response_model=s.AnswerOut)
def prepare_meeting(customer_id: int, body: s.PrepareRequest, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    return intelligence.prepare(c, body.use_memory, body.meeting_goal, _count(db, c.id))


@router.post("/customers/{customer_id}/followup", response_model=s.AnswerOut)
def generate_followup(customer_id: int, body: s.FollowupRequest, db: Session = Depends(get_db)):
    c = _customer_or_404(db, customer_id)
    return intelligence.followup(c, body.channel, body.tone, body.instructions, _count(db, c.id))


# ---------- demo ----------
@router.get("/demo/script", response_model=s.DemoScript)
def demo_script():
    return DEMO


@router.post("/demo/customer", response_model=s.CustomerOut, status_code=201)
def create_demo_customer(db: Session = Depends(get_db)):
    """Create (or return) the demo customer Rahul / ABC Corp / SaaS - with NO interactions yet."""
    existing = db.scalars(select(Customer).where(Customer.is_demo.is_(True)).order_by(Customer.id)).first()
    if existing:
        return _customer_out(db, existing)
    c = Customer(name=DEMO["name"], company=DEMO["company"], industry=DEMO["industry"], is_demo=True)
    db.add(c)
    db.commit()
    db.refresh(c)
    try:
        hs.ensure_bank(c.bank_id, c.name, c.company, c.industry)
    except (hs.HindsightNotConfigured, hs.HindsightError):
        pass
    return _customer_out(db, c)
