# DealMind - Windows + Visual Studio Code setup (from absolute zero)

This guide assumes you have a fresh Windows 10/11 PC and have never run this project. Every command is for **Windows PowerShell**.

You will end up with two programs running side by side:

| Program | URL |
|---|---|
| Frontend (the website) | http://localhost:5173 |
| Backend (the API) | http://localhost:8000 |
| Backend API docs (Swagger) | http://localhost:8000/docs |

---

## 1. Required software

| Software | Version | Why |
|---|---|---|
| **Node.js** | 20 LTS or 22 LTS (the project was built and tested with Node 22) | runs the frontend |
| **Python** | 3.11 or 3.12 (tested with 3.12) | runs the backend |
| **Git** | any recent version | only needed if you want to push to GitHub / deploy (see step 4) |
| **Visual Studio Code** | latest | your editor and terminal |

### 2. Node.js version

Install Node.js 20 LTS or 22 LTS.

Easiest way (PowerShell):

```powershell
winget install OpenJS.NodeJS.LTS
```

Or download the "LTS" installer from https://nodejs.org and click through it (keep "Add to PATH" ticked).

**Close and re-open PowerShell**, then check:

```powershell
node --version     # should print v20.x or v22.x
npm --version
```

### 3. Python version

```powershell
winget install Python.Python.3.12
```

Or download from https://www.python.org/downloads/windows/ . **Tick "Add python.exe to PATH"** on the first installer screen.

Close and re-open PowerShell, then check:

```powershell
python --version   # should print Python 3.12.x (3.11 also works)
```

If `python` is not recognised, try `py --version`. If `py` works, use `py` instead of `python` in the commands below.

### 4. Git installation (only if needed)

You do **not** need Git to run DealMind locally. You need it if you want to deploy (see DEPLOYMENT.md).

```powershell
winget install Git.Git
```

Close and re-open PowerShell, then `git --version`.

### Install Visual Studio Code

```powershell
winget install Microsoft.VisualStudioCode
```

(or download from https://code.visualstudio.com). Optional extension: **Python** (by Microsoft).

---

## 5. Open the project in VS Code

1. Extract `DealMind.zip` (right-click -> *Extract All*), for example to `C:\Projects\DealMind`.
2. Open VS Code -> **File -> Open Folder...** -> choose the **DealMind** folder (the one that contains `frontend`, `backend`, and `README.md`).
3. If VS Code asks *"Do you trust the authors?"* click **Yes, I trust the authors**.

## 6. Open the terminal

In VS Code press **Ctrl + `** (the backtick key, left of the `1` key), or use the menu **Terminal -> New Terminal**.

Make sure it says **PowerShell** at the top right of the terminal panel. You need **two terminals**: click the **+** icon in the terminal panel to open a second one later.

Confirm you are in the project folder:

```powershell
dir
```

You should see `backend`, `frontend`, `README.md`, `.env.example`, ...

---

## 7. Create the .env file (do this once)

From the project root (the folder that contains `.env.example`):

```powershell
Copy-Item .env.example .env
```

Then open `.env` in VS Code and fill it in (step 12 below explains every value).

## 8. Backend: create the Python virtual environment (Terminal 1)

```powershell
cd backend
python -m venv venv
```

## 9. Activate the virtual environment in PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

Your prompt now starts with `(venv)`.

> **If you see "running scripts is disabled on this system"** run this once, then activate again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> (answer `Y`). This only affects your own user account.

## 10. Install backend dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 11. Frontend: install dependencies (Terminal 2)

Open a **second** terminal (the **+** button), then:

```powershell
cd frontend
npm install
```

(The first install takes 1-2 minutes.)

---

## 12. Where each API key goes

All keys go in the single file **`.env`** in the project root (`DealMind\.env`). Never put keys in the code.

| Variable | What to put | Required? |
|---|---|---|
| `HINDSIGHT_API_KEY` | Your Hindsight **Cloud** API key. Get one by signing up at https://ui.hindsight.vectorize.io/signup and creating an API key in the dashboard. | **Yes**, unless you self-host (next row) |
| `HINDSIGHT_BASE_URL` | Leave **empty** for Hindsight Cloud. For a self-hosted Hindsight server use e.g. `http://localhost:8888`. | Only for self-hosting |
| `HINDSIGHT_BANK_PREFIX` | Leave as `dealmind` | No |
| `HINDSIGHT_RETAIN_ASYNC` | `false` (recommended for demos) | No |
| `DATABASE_URL` | Leave as `sqlite:///./dealmind.db` locally. The file is created automatically. | No |
| `FRONTEND_URL` | Leave as `http://localhost:5173` locally | No |
| `VITE_API_URL` | Leave **empty** locally | No |

DealMind needs **no OpenAI / Anthropic key**. (If you self-host Hindsight, the Hindsight *server* needs its own LLM key - see README > "Setting up Hindsight".)

Example finished `.env` for Hindsight Cloud (paste YOUR key; the value below is only a placeholder):

```
HINDSIGHT_API_KEY=paste_the_key_from_your_hindsight_dashboard
HINDSIGHT_BASE_URL=
HINDSIGHT_BANK_PREFIX=dealmind
HINDSIGHT_RETAIN_ASYNC=false
HINDSIGHT_TIMEOUT=120
DATABASE_URL=sqlite:///./dealmind.db
FRONTEND_URL=http://localhost:5173
VITE_API_URL=
```

Save the file. **Restart the backend after any change to `.env`.**

## 13. Check that Hindsight is really connected (recommended)

In Terminal 1 (venv active), go back to the project root and run the memory test:

```powershell
cd ..
python scripts\test_memory.py
```

You want to see `PASS: Hindsight returned N remembered fact(s). Memory is working.` If you see `FAIL`, the message tells you exactly what is missing. Then return to the backend folder: `cd backend`.

## 14. Start the backend (Terminal 1, inside `backend`, venv active)

```powershell
uvicorn main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`. The SQLite database and tables are created automatically on first start - nothing to set up.

## 15. Start the frontend (Terminal 2, inside `frontend`)

```powershell
npm run dev
```

You should see `Local: http://localhost:5173/`.

## 16. Verify the application

1. Backend health check - open http://localhost:8000/api/health in your browser. You should see:
   ```json
   {"status":"ok","service":"dealmind-backend"}
   ```
   or in PowerShell: `Invoke-RestMethod http://localhost:8000/api/health`
2. Hindsight status - open http://localhost:8000/api/memory/status . You want `"configured": true` and `"reachable": true`.
3. API docs - http://localhost:8000/docs
4. The app - open **http://localhost:5173**. In the bottom-left of the sidebar you should see a green **"Hindsight connected"** box.
5. Click **Start judge demo (Rahul)** and follow DEMO.md.

## 17. Stop the application

In each terminal press **Ctrl + C**. To leave the Python environment type `deactivate`.

To start again later you only need steps 14 and 15 (activate the venv first: `cd backend` then `.\venv\Scripts\Activate.ps1`).

## Run the automated tests (optional)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m pytest -q
```

---

## 18. Common errors and their fixes

| Problem | Fix |
|---|---|
| `python` / `node` / `npm` "is not recognized" | Close **all** PowerShell/VS Code windows and reopen them (PATH only updates for new windows). If still failing, reinstall and tick "Add to PATH". For Python you can also try `py`. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` then activate again. |
| `ModuleNotFoundError: No module named 'fastapi'` (or similar) | The venv is not active or dependencies were not installed. Run `.\venv\Scripts\Activate.ps1` then `pip install -r requirements.txt`. |
| `uvicorn is not recognized` | Same as above - activate the venv first. Or run `python -m uvicorn main:app --reload --port 8000`. |
| `Error: [Errno 10048] ... address already in use` / port 8000 or 5173 busy | Find the process: `netstat -ano \| findstr :8000` then `taskkill /PID <number> /F`. Or use another port: `uvicorn main:app --port 8010` (and set the Vite proxy / `VITE_API_URL` accordingly). |
| Website shows **"DealMind cannot reach its backend"** | The backend is not running, or it crashed. Look at Terminal 1 for the error. Check http://localhost:8000/api/health . |
| Sidebar shows **"Hindsight not configured"** | `.env` is missing or `HINDSIGHT_API_KEY` is still `your_key_here`. Edit `.env`, save, **restart the backend**. |
| Sidebar shows **"Hindsight unreachable"** or errors mention `401 Unauthorized` | Wrong/expired API key, or wrong `HINDSIGHT_BASE_URL`. Re-copy the key from the Hindsight dashboard (no spaces or quotes). |
| An interaction shows **"Not stored in Hindsight"** | Hindsight failed at that moment. Fix the cause (see message next to it), then click **Retry**. |
| "Prepare me..." takes a long time | Hindsight uses an LLM to recall and reason; a first response can take many seconds. Wait for the spinner. If it exceeds 2 minutes, raise `HINDSIGHT_TIMEOUT` in `.env`. |
| Browser console shows a **CORS** error | `FRONTEND_URL` in `.env` must exactly match the address in your browser (`http://localhost:5173`, no trailing slash). Restart the backend. |
| `npm install` fails with `EACCES`/network errors | Check your internet/proxy. Delete `frontend\node_modules` and run `npm install` again. Make sure Node is 20 or 22 (`node --version`). |
| `pip install` fails building a package | Upgrade pip (`python -m pip install --upgrade pip`) and make sure you use Python 3.11 or 3.12 (`python --version`). |
| You edited `.env` but nothing changed | The backend only reads `.env` at start. Press Ctrl+C and start it again. For `VITE_API_URL` restart `npm run dev` too. |
| You want to reset all local data | Stop the backend, delete `backend\dealmind.db`, start again. (Memories in Hindsight are separate; the app's **Delete customer** button removes a customer's Hindsight memory bank too.) |
