# DealMind

## What is DealMind?
DealMind is an AI sales assistant that **remembers every customer**. You log what customers say; DealMind stores it in **Hindsight** (persistent agent memory) and uses that memory to prepare your meetings, answer questions about a customer, and write follow-ups.

## Problem
Sales conversations are scattered across calls, emails and notes. Before each meeting a rep re-reads old notes (or forgets), so they miss objections, promises and what the customer actually cares about.

## Solution
Every interaction is retained in a per-customer Hindsight memory bank. When you ask for a meeting briefing, Hindsight recalls the relevant facts and reasons over them, so the answer reflects the whole relationship, not just the last note.

## Features
- Customers and a memory timeline (each item shows whether it is **stored in Hindsight**, with Retry on failure)
- **Meeting prep** ("Prepare me for Rahul's meeting"), with a side-by-side **without memory / with memory** view
- **Ask about customer** (free-form questions answered from memory)
- **Follow-up** email or message drafts that reference what the customer said
- **Judge demo** button (Rahul / ABC Corp / SaaS) that walks the exact demo
- Clear loading, error and "Hindsight not configured" states

## Architecture
```
React + Tailwind  --HTTP-->  FastAPI  --hindsight-client-->  Hindsight (Cloud or self-hosted)
   (frontend)                (backend)                        retain / recall / reflect
                                 |
                          SQLite / Postgres
                       (customer + timeline records only)
```
- **Hindsight** holds all memory. One memory bank per customer (random unique bank id).
- **SQLite/Postgres** holds only the CRM list and activity log shown in the UI. **It is not memory and is never used as a substitute for it.**

## Tech Stack
React 18, Vite 5, Tailwind CSS 3, FastAPI, SQLAlchemy 2, SQLite (Postgres supported), `hindsight-client` (official Python SDK).

## Hindsight Integration
See **Setting up Hindsight** below. Summary of calls (all from the official SDK, https://hindsight.vectorize.io/sdks/python):

| DealMind action | Hindsight call |
|---|---|
| New customer | `create_bank(bank_id, name, mission)` |
| Save interaction | `retain(bank_id, content, context, timestamp, document_id)` |
| Show recalled memories | `recall(bank_id, query)` |
| Ask / Prepare / Follow-up | `reflect(bank_id, query, context)` |
| Status | `get_version()` |
| Delete customer | `delete_bank(bank_id)` |

### REAL HINDSIGHT MEMORY vs DEMO/FALLBACK DATA
| | Real Hindsight memory | Not memory |
|---|---|---|
| What | Facts retained and recalled through the Hindsight server | SQLite/Postgres rows (customer list, timeline text) |
| Badge in UI | **"Built from Hindsight memory"** / **"Stored in Hindsight"** | **"Generic template - no memory used"** / **"Not stored in Hindsight"** |

There is no local-JSON or SQLite "memory" fallback. If Hindsight is missing, memory features fail with a clear message. The only non-Hindsight content is the fixed generic checklist used for the "before memory" comparison, always labelled as such.

### Setting up Hindsight
1. **What it does here:** it is DealMind's long-term memory. It extracts facts from each interaction, links them per customer, and answers queries over them.
2. **Get credentials (Cloud):** sign up at https://ui.hindsight.vectorize.io/signup and create an API key in the dashboard. (Or self-host, see below.)
3. **Where to put them:** `.env` in the project root:
   ```
   HINDSIGHT_API_KEY=<your key>
   HINDSIGHT_BASE_URL=          # empty = Hindsight Cloud (https://api.hindsight.vectorize.io)
   ```
   If your dashboard shows a different API URL, put it in `HINDSIGHT_BASE_URL`.
4. **Sending memories:** saving an interaction calls `retain` with text like *"Sales interaction with Rahul from ABC Corp (SaaS). Interaction type: email. Note: ..."* into that customer's bank.
5. **Retrieving memories:** "Show recalled memories" uses `recall`; Ask/Prepare/Follow-up use `reflect`, which recalls and reasons.
6. **Verify it works:**
   ```powershell
   python scripts\test_memory.py            # add --cleanup to delete the test bank
   ```
   Creates a Rahul test bank, retains the 5 demo interactions, recalls, reflects, prints results, and prints `PASS`/`FAIL`. With missing credentials it stops and says what is missing. In the app, the sidebar shows **"Hindsight connected"** and `GET /api/memory/status` returns `"reachable": true`. You can also open the bank in the Hindsight dashboard using the bank id shown under the customer's name.

**Self-hosting (optional, external service):** Hindsight publishes a Docker image `ghcr.io/vectorize-io/hindsight:latest` (API on port 8888, UI on 9999). The *server* needs its own LLM API key and model, e.g. `-e HINDSIGHT_API_LLM_API_KEY=... -e HINDSIGHT_API_LLM_MODEL=...`; check https://hindsight.vectorize.io/developer/installation for the current variables (including the provider setting) before running it. Then set `HINDSIGHT_BASE_URL=http://localhost:8888`. I did not run the self-hosted server while building DealMind.

## Project Structure
```
DealMind/
  frontend/   React app (src/components, src/lib/api.js)
  backend/    FastAPI (app/api, models, schemas, services, db, core), tests/, main.py
  scripts/    test_memory.py, check_secrets.py
  .env.example  README.md  SETUP-WINDOWS.md  DEPLOYMENT.md  API.md  DEMO.md  docker-compose.yml
```

## Prerequisites
Node.js 20 or 22, Python 3.11 or 3.12, a Hindsight API key (or a self-hosted Hindsight). Windows users: follow **SETUP-WINDOWS.md**.

## Installation
```powershell
Copy-Item .env.example .env          # then edit .env
cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
cd ..\frontend; npm install
```

## Environment Variables
Documented line by line in `.env.example`. Key ones: `HINDSIGHT_API_KEY`, `HINDSIGHT_BASE_URL`, `DATABASE_URL`, `FRONTEND_URL` (CORS), `VITE_API_URL` (frontend -> backend URL, build time).

## Run Locally
Terminal 1: `cd backend`, activate venv, `uvicorn main:app --reload --port 8000`
Terminal 2: `cd frontend`, `npm run dev`

| | URL |
|---|---|
| **Frontend (open this)** | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Health check | http://localhost:8000/api/health |
| Swagger | http://localhost:8000/docs |

## Demo
See **DEMO.md** (2-4 minutes, Rahul / ABC Corp / SaaS, before vs after memory).

## API Endpoints
Full reference in **API.md**. Main ones: `GET /api/health`, `GET /api/memory/status`, `POST /api/customers`, `POST /api/customers/{id}/interactions`, `POST /api/customers/{id}/memory/recall`, `.../ask`, `.../prepare`, `.../followup`.

## Testing
```powershell
cd backend; .\venv\Scripts\Activate.ps1; python -m pytest -q     # offline unit tests (Hindsight is faked)
cd ..; python scripts\test_memory.py                              # REAL Hindsight check (needs credentials)
python scripts\check_secrets.py                                   # no secrets / .env in the project
```
The unit tests use a fake Hindsight client and prove DealMind's own logic only. `test_memory.py` is the real integration check.

## Deployment
See **DEPLOYMENT.md** (Vercel frontend + Render backend + hosted Postgres + Hindsight Cloud). A Docker option is in `docker-compose.yml`.

## Troubleshooting
See the last section of **SETUP-WINDOWS.md**.

## Known Limitations
- **No authentication / multi-user support.** Anyone who can reach the API can read customers and spend your Hindsight quota. Do not expose a public deployment with real customer data. Add auth before real use.
- Meeting prep, ask and follow-up quality and latency depend on Hindsight and its LLM (often 10-30 s). Answers are not fact-checked beyond what Hindsight returns.
- The integration was verified against a stand-in server during development and unit tests; run `scripts/test_memory.py` with your own key to confirm the live service. The Hindsight Cloud default URL came from third-party integration docs; override with `HINDSIGHT_BASE_URL` if yours differs.
- `docker-compose.yml` was written but not run during development.
- Deleting the local database does not delete Hindsight banks (only the in-app Delete customer button does).
- Free hosting tiers sleep and can lose data (see DEPLOYMENT.md).

## Future Improvements
Authentication and per-user banks, Hindsight tags/mental models for deal stage, calendar and email import, streaming answers, CRM integrations.
