"""Thin wrapper around the official `hindsight-client` Python SDK.

Everything that touches memory goes through this module. There is deliberately NO
local fallback: if Hindsight is not configured or unreachable, the caller gets an
explicit error instead of fake memory.

SDK calls used (all documented at https://hindsight.vectorize.io/sdks/python):
  Hindsight(base_url, api_key, timeout)
  create_bank(bank_id, name, mission)
  retain(bank_id, content, context, timestamp, document_id, retain_async)
  recall(bank_id, query, max_tokens, budget)
  reflect(bank_id, query, budget, context)
  get_version()
  delete_bank(bank_id)
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings


class HindsightNotConfigured(Exception):
    """Raised when no Hindsight URL / API key has been provided."""


class HindsightError(Exception):
    """Raised when a call to Hindsight fails."""


_client = None
_client_lock = threading.Lock()
_ensured_banks: set[str] = set()


def _get_client():
    global _client
    settings = get_settings()
    if not settings.hindsight_configured:
        raise HindsightNotConfigured(
            "Hindsight is not configured. Set HINDSIGHT_API_KEY (Hindsight Cloud) or "
            "HINDSIGHT_BASE_URL (self-hosted) in your .env file, then restart the backend."
        )
    with _client_lock:
        if _client is None:
            from hindsight_client import Hindsight

            _client = Hindsight(
                base_url=settings.resolved_hindsight_url,
                api_key=settings.hindsight_api_key or None,
                timeout=settings.hindsight_timeout,
            )
        return _client


def reset_client() -> None:
    """Used by tests to swap the client."""
    global _client
    with _client_lock:
        _client = None
        _ensured_banks.clear()


def set_client_for_tests(client: Any) -> None:
    global _client
    with _client_lock:
        _client = client
        _ensured_banks.clear()


def _wrap(exc: Exception) -> HindsightError:
    return HindsightError(f"{type(exc).__name__}: {exc}")


def ensure_bank(bank: str, name: str, company: str, industry: str) -> str:
    """One Hindsight memory bank per customer (isolated memory)."""
    if bank in _ensured_banks:
        return bank
    client = _get_client()
    mission = (
        f"Sales memory for the customer {name} at {company}"
        + (f" ({industry})" if industry else "")
        + ". Remember what the customer wants, their objections, concerns, questions, "
        "requests and commitments so a salesperson can prepare for meetings and write follow-ups."
    )
    try:
        client.create_bank(bank_id=bank, name=f"{name} - {company}", mission=mission)
    except Exception as exc:  # noqa: BLE001
        raise _wrap(exc) from exc
    _ensured_banks.add(bank)
    return bank


def retain_interaction(
    *,
    bank_id: str,
    name: str,
    company: str,
    industry: str,
    interaction_id: int,
    kind: str,
    content: str,
    occurred_at: datetime,
) -> None:
    bank = ensure_bank(bank_id, name, company, industry)
    client = _get_client()
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)
    text = (
        f"Sales interaction with {name} from {company}"
        + (f" ({industry})" if industry else "")
        + f". Interaction type: {kind}. Note: {content}"
    )
    try:
        client.retain(
            bank_id=bank,
            content=text,
            context=f"sales {kind} with {name} ({company})",
            timestamp=occurred_at,
            document_id=f"interaction-{interaction_id}",
            retain_async=get_settings().hindsight_retain_async,
        )
    except Exception as exc:  # noqa: BLE001
        raise _wrap(exc) from exc


def recall(bank_id: str, query: str, max_tokens: int = 2048) -> List[Dict[str, Optional[str]]]:
    client = _get_client()
    try:
        res = client.recall(
            bank_id=bank_id, query=query, max_tokens=max_tokens, budget="mid"
        )
    except Exception as exc:  # noqa: BLE001
        raise _wrap(exc) from exc
    return [{"text": r.text, "type": getattr(r, "type", None)} for r in (res.results or [])]


def reflect(bank_id: str, query: str, context: Optional[str] = None) -> str:
    client = _get_client()
    try:
        res = client.reflect(
            bank_id=bank_id, query=query, budget="mid", context=context
        )
    except Exception as exc:  # noqa: BLE001
        raise _wrap(exc) from exc
    return (res.text or "").strip()


def delete_bank(bank_id: str) -> None:
    client = _get_client()
    try:
        client.delete_bank(bank_id=bank_id)
    except Exception as exc:  # noqa: BLE001
        raise _wrap(exc) from exc
    _ensured_banks.discard(bank_id)


def status() -> Dict[str, Any]:
    s = get_settings()
    out: Dict[str, Any] = {
        "configured": s.hindsight_configured,
        "reachable": False,
        "mode": s.hindsight_mode,
        "base_url": s.resolved_hindsight_url,
        "server_version": None,
        "error": None,
    }
    if not s.hindsight_configured:
        out["error"] = "Hindsight credentials are missing (see README > Setting up Hindsight)."
        return out
    try:
        v = _get_client().get_version()
        out["reachable"] = True
        out["server_version"] = getattr(v, "api_version", None)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def get_client():
    """Public accessor used by scripts/test_memory.py."""
    return _get_client()


def close_client() -> None:
    """Close the HTTP session on shutdown / at the end of scripts."""
    global _client
    with _client_lock:
        if _client is not None:
            try:
                _client.close()
            except Exception:  # noqa: BLE001
                pass
            _client = None
