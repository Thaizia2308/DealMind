# DealMind API

Base URL (local): `http://localhost:8000` - all routes start with `/api`.
Interactive docs (Swagger UI): http://localhost:8000/docs  -  ReDoc: http://localhost:8000/redoc

All bodies are JSON. Timestamps are ISO-8601 UTC.

## Health and status

### `GET /api/health`
Simple liveness check. Use it to confirm the backend is running.
```json
{"status": "ok", "service": "dealmind-backend"}
```
PowerShell: `Invoke-RestMethod http://localhost:8000/api/health`

### `GET /api/memory/status`
Checks whether Hindsight is configured **and reachable** (calls the Hindsight server's version endpoint).
```json
{"configured": true, "reachable": true, "mode": "cloud", "base_url": "https://api.hindsight.vectorize.io",
 "server_version": "0.10.x", "error": null}
```
`mode` is `cloud`, `self-hosted` or `not-configured`. When something is wrong, `error` explains it.

## Customers (CRM records - stored in SQLite/Postgres, NOT memory)

| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `/api/customers` | - | newest first, includes `interaction_count` |
| POST | `/api/customers` | `{"name","company","industry"}` | also creates the customer's Hindsight memory bank (best effort) |
| GET | `/api/customers/{id}` | - | 404 if unknown |
| DELETE | `/api/customers/{id}` | - | 204. Also deletes the customer's Hindsight bank (best effort) |

Customer object:
```json
{"id": 1, "name": "Rahul", "company": "ABC Corp", "industry": "SaaS", "is_demo": true,
 "bank_id": "dealmind-3f9c2a1b7d6e4c80", "created_at": "2026-09-28T10:00:00Z", "interaction_count": 5}
```
`bank_id` is the customer's unique memory bank in Hindsight (it is random, not derived from `id`, so customers can never share memory).

## Interactions

### `GET /api/customers/{id}/interactions`
Chronological list.

### `POST /api/customers/{id}/interactions`
```json
{"content": "Rahul asked about SOC 2 compliance.", "kind": "email"}
```
`kind`: `note` (default), `call`, `meeting`, `email`, `demo`. Optional `occurred_at` (ISO timestamp).

The interaction is saved locally **and sent to Hindsight** (`retain`). Response (201):
```json
{"id": 4, "customer_id": 1, "kind": "email", "content": "...", "occurred_at": "...",
 "retained": true, "retain_error": ""}
```
If Hindsight fails or is not configured, the interaction is still saved, `retained` is `false` and `retain_error` says why. Call the retry endpoint once fixed.

### `POST /api/interactions/{interaction_id}/retry`
Re-sends an un-retained interaction to Hindsight. Returns the updated interaction.

## Memory and sales intelligence (all require Hindsight for memory-backed answers)

Answer object returned by `ask`, `prepare` and `followup`:
```json
{"answer": "markdown text", "memory_used": true, "source": "hindsight",
 "memories": [{"text": "...", "type": "world"}]}
```
`source` is `"hindsight"` for real memory-backed answers, or `"generic-template"` for the labelled no-memory baseline. It is never anything else, and a template is never presented as memory.

### `POST /api/customers/{id}/memory/recall`
`{"query": "security concerns"}` -> `{"memories": [{"text": "...", "type": "world"}]}` (Hindsight `recall`).

### `POST /api/customers/{id}/ask`
`{"question": "What is Rahul worried about?"}` -> answer object (Hindsight `reflect`, plus the recalled memories as evidence).

### `POST /api/customers/{id}/prepare`
`{"use_memory": true, "meeting_goal": "Agree on evaluation plan"}` (both optional) -> answer object: a meeting briefing (snapshot, priorities, objections, open questions, talking points, next step).
- `use_memory: false`, or a customer with **zero** interactions, returns the generic checklist with `source: "generic-template"`. This is the "before memory" baseline for demos.

### `POST /api/customers/{id}/followup`
`{"channel": "email", "tone": "professional", "instructions": "Offer a call Thursday"}` -> answer object with a draft that references what the customer actually said. `channel`: `email` | `message`; `tone`: `professional` | `friendly` | `concise`. With no interactions it returns a labelled generic template.

## Demo helpers

| Method | Path | Notes |
|---|---|---|
| GET | `/api/demo/script` | The Rahul / ABC Corp / SaaS steps and the closing question |
| POST | `/api/demo/customer` | Creates (or returns) the demo customer **with no interactions** |

## Errors

| Status | Body | Meaning |
|---|---|---|
| 404 | `{"detail": "Customer not found"}` | unknown id |
| 422 | `{"detail": [...]}` | validation error (e.g. empty name) |
| 502 | `{"detail": "Hindsight request failed: ...", "code": "hindsight_error"}` | Hindsight rejected/failed the call (bad key, timeout, server error) |
| 503 | `{"detail": "Hindsight is not configured. ...", "code": "hindsight_not_configured"}` | no `HINDSIGHT_API_KEY` / `HINDSIGHT_BASE_URL` |

There is **no authentication** on this API (see README > Known Limitations).
