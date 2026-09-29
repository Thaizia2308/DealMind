"""Pre-share safety check: make sure no secrets are in the project.

Run from the project root:   python scripts/check_secrets.py
Exit code 0 = clean, 1 = problems found.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"node_modules", "venv", ".venv", "__pycache__", "dist", ".git", ".pytest_cache"}
SKIP_EXT = {".woff2", ".png", ".jpg", ".ico", ".db", ".sqlite", ".zip", ".pyc"}
PLACEHOLDER = re.compile(r"(your[_-]?key[_-]?here|changeme|example|placeholder|xxxx|<.*>|test-key-not-real)", re.I)
ASSIGNMENT = re.compile(r"""(?i)(api[_-]?key|secret|token|password|passwd)\s*[=:]\s*['"]?((?=[A-Za-z_\-/+=]*\d)[A-Za-z0-9_\-/+=]{20,})""")
KNOWN = [re.compile(p) for p in (r"sk-[A-Za-z0-9]{20,}", r"AKIA[0-9A-Z]{16}", r"ghp_[A-Za-z0-9]{30,}", r"xox[baprs]-[A-Za-z0-9-]{10,}")]

problems = []

if os.path.exists(os.path.join(ROOT, ".env")):
    problems.append(".env exists in the project root - it must NOT be shared or committed (delete it before zipping).")

gi = os.path.join(ROOT, ".gitignore")
gi_text = open(gi, encoding="utf-8").read() if os.path.exists(gi) else ""
for rule in (".env", ".env.*", "!.env.example"):
    if rule not in gi_text.split():
        problems.append(f".gitignore is missing the rule: {rule}")
if not os.path.exists(os.path.join(ROOT, ".env.example")):
    problems.append(".env.example is missing")

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if os.path.splitext(fn)[1].lower() in SKIP_EXT or fn == os.path.basename(__file__):
            continue
        path = os.path.join(dirpath, fn)
        rel = os.path.relpath(path, ROOT)
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for pat in KNOWN:
                if pat.search(line):
                    problems.append(f"{rel}:{n}: looks like a real credential")
            m = ASSIGNMENT.search(line)
            if m and not PLACEHOLDER.search(line):
                problems.append(f"{rel}:{n}: possible hard-coded secret ({m.group(1)})")

if problems:
    print("PROBLEMS FOUND:")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("OK: no .env file, .gitignore rules present, and no hard-coded secrets found.")
