"""Sales intelligence: ask, meeting prep, follow-up.

All memory-backed answers are produced by Hindsight (`reflect`), which recalls the
customer's memories and reasons over them. When the customer has no interactions
(or the caller asks for the no-memory baseline) we return a clearly labelled generic
template instead - it never pretends to be memory.
"""
from __future__ import annotations

from typing import Dict, List

from app.services import hindsight_service as hs

GENERIC_PREP = """**Generic meeting preparation (no customer memory used)**

DealMind has no remembered history for this customer, so this is only a standard checklist:

1. Research the company: size, product, recent news.
2. Prepare an agenda and confirm the meeting goal with the customer.
3. Have pricing and packaging options ready.
4. Prepare answers for common concerns (price, security, integration, support).
5. Decide on a clear next step to ask for at the end.

Add interactions to this customer and DealMind will replace this checklist with a briefing built from what the customer actually said."""

GENERIC_FOLLOWUP = """**Generic follow-up (no customer memory used)**

Hi,

Thanks for taking the time to speak with us. I wanted to follow up on our conversation and see whether you have any questions. Please let me know a good time for a next step.

Best regards

(No remembered interactions exist yet, so this message cannot reference anything the customer said.)"""

_SYSTEM_CONTEXT = (
    "You are DealMind, an AI sales assistant. Use ONLY what is remembered about this customer. "
    "If something is not in memory, say it is not known instead of guessing. Be specific and concise."
)


def _who(customer) -> str:
    industry = f", {customer.industry}" if customer.industry else ""
    return f"{customer.name} from {customer.company}{industry}"


def _recall_evidence(bank_id: str, query: str) -> List[Dict]:
    try:
        return hs.recall(bank_id, query)
    except hs.HindsightError:
        return []


def ask(customer, question: str) -> Dict:
    answer = hs.reflect(customer.bank_id, question, context=_SYSTEM_CONTEXT)
    return {
        "answer": answer or "Hindsight returned no answer. Add interactions for this customer first.",
        "memory_used": True,
        "source": "hindsight",
        "memories": _recall_evidence(customer.bank_id, question),
    }


def prepare(customer, use_memory: bool, meeting_goal: str, interaction_count: int) -> Dict:
    if not use_memory or interaction_count == 0:
        return {"answer": GENERIC_PREP, "memory_used": False, "source": "generic-template", "memories": []}

    goal = f" The goal of the meeting: {meeting_goal}." if meeting_goal.strip() else ""
    query = (
        f"Prepare me for my next meeting with {_who(customer)}.{goal} "
        "Write a briefing with these sections: "
        "1) Deal snapshot (what they are interested in). "
        "2) What matters most to them. "
        "3) Objections and risks. "
        "4) Open questions and requests we must answer. "
        "5) Recommended talking points and meeting agenda. "
        "6) Suggested next step / close. "
        "Only include facts from memory; mark anything unknown as unknown."
    )
    answer = hs.reflect(customer.bank_id, query, context=_SYSTEM_CONTEXT + " The user is preparing for a meeting.")
    return {
        "answer": answer or "Hindsight returned an empty briefing. Try again in a few seconds.",
        "memory_used": True,
        "source": "hindsight",
        "memories": _recall_evidence(customer.bank_id, f"everything about {customer.name}: interests, concerns, requests"),
    }


def followup(customer, channel: str, tone: str, instructions: str, interaction_count: int) -> Dict:
    if interaction_count == 0:
        return {"answer": GENERIC_FOLLOWUP, "memory_used": False, "source": "generic-template", "memories": []}

    extra = f" Extra instructions: {instructions}." if instructions.strip() else ""
    query = (
        f"Draft a {tone} follow-up {channel} to {_who(customer)}. "
        "Reference the specific things they said and asked for, address their concerns directly, "
        "and end with one clear next step. Do not invent facts that are not in memory."
        + extra
    )
    answer = hs.reflect(customer.bank_id, query, context=_SYSTEM_CONTEXT + " The user is writing to the customer.")
    return {
        "answer": answer or "Hindsight returned an empty draft. Try again in a few seconds.",
        "memory_used": True,
        "source": "hindsight",
        "memories": _recall_evidence(customer.bank_id, f"what {customer.name} asked for and worried about"),
    }
