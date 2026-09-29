# Deploying DealMind

Recommended stack (all have a free tier; checked against provider docs in September 2026, confirm current terms before relying on them):

| Part | Service | Cost note |
|---|---|---|
| Frontend (static build) | **Vercel** (Netlify/Cloudflare Pages work the same way) | free Hobby plan; Vercel's Hobby plan is for non-commercial use, check current terms |
| Backend (FastAPI) | **Render** web service (Python) | Free tier **sleeps after 15 min idle, ~1 min to wake**. Filesystem is **ephemeral** |
| Database | **Render Postgres** | Free Postgres **expires 30 days** after creation; paid plans start at a few dollars/month. Alternative: any hosted Postgres (Neon, Supabase, ...) |
| Memory | **Hindsight Cloud** | see Hindsight's pricing |

**Do not use SQLite on Render's free tier:** its disk is wiped on every redeploy, restart and spin-down, so customers would vanish (memories stay in Hindsight but the app would not know the customers). The backend supports Postgres via `DATABASE_URL` and already includes the driver.

## 1. Push to GitHub
```powershell
git init; git add .; git commit -m "DealMind"
```
Create an empty repo on github.com, then `git remote add origin <url>; git branch -M main; git push -u origin main`. `.gitignore` already excludes `.env`; run `python scripts\check_secrets.py` first.

## 2. Database (Render Postgres)
Render dashboard -> **New -> Postgres** -> Free (or paid) -> create. Copy the **Internal Database URL** (use it if backend and DB are in the same region; otherwise the External URL).

## 3. Backend (Render web service)
1. **New -> Web Service** -> connect your GitHub repo.
2. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3 (set env var `PYTHON_VERSION=3.12.3` if needed)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path (Advanced):** `/api/health`
3. **Environment variables:**
   | Key | Value |
   |---|---|
   | `HINDSIGHT_API_KEY` | your Hindsight Cloud key |
   | `HINDSIGHT_BASE_URL` | leave unset for Cloud |
   | `DATABASE_URL` | the Postgres URL from step 2 |
   | `FRONTEND_URL` | your Vercel URL (set after step 4; e.g. `https://dealmind.vercel.app`, no trailing slash) |
   | `HINDSIGHT_RETAIN_ASYNC` | `false` |
4. Deploy. Note the URL, e.g. `https://dealmind-api.onrender.com`. Test: open `<url>/api/health`.

## 4. Frontend (Vercel)
1. **Add New -> Project** -> import the repo.
2. **Root Directory:** `frontend`. Framework preset **Vite** (auto-detected): build `npm run build`, output `dist`.
3. **Environment Variable:** `VITE_API_URL` = your Render backend URL (no trailing slash). Vite bakes this in **at build time**, so if you change it, redeploy.
4. Deploy. Copy the resulting URL.

## 5. CORS
Go back to Render -> backend -> Environment -> set `FRONTEND_URL` to the exact Vercel URL (add several separated by commas, e.g. a custom domain). Save; Render redeploys. A CORS error in the browser console means this value does not match exactly.

## 6. Test production
1. `https://<backend>/api/health` -> `{"status":"ok",...}` (first hit may take ~1 min on the free tier).
2. `https://<backend>/api/memory/status` -> `"configured": true, "reachable": true`.
3. Hindsight in production: open the site, sidebar must show **Hindsight connected**; add an interaction and confirm **Stored in Hindsight**.
4. Full flow: run DEMO.md end to end. Confirm no requests go to `localhost` (browser dev tools -> Network).

## Security before sharing a public URL
The API has **no authentication**. Anyone with the link can view customers and use your Hindsight quota. Use it for demos with fake data only, or add authentication first.

## Docker alternative (untested)
`docker compose up --build` after creating `.env` runs both services locally on http://localhost:5173. Written but not run during development.
