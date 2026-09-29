"""Verify that DealMind can really talk to Hindsight.

What it does (against the Hindsight server configured in your .env):
  1. Creates a demo customer memory bank  (Rahul / ABC Corp / SaaS)
  2. Sends the 5 demo interactions to Hindsight   (retain)
  3. Retrieves memories about Rahul               (recall)
  4. Asks Hindsight to reason over them           (reflect)
  5. Prints everything and PASS / FAIL

Run from the project root with the backend virtual environment active:
    python scripts/test_memory.py            (add --cleanup to delete the test bank afterwards)
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)  # so backend/.env and ../.env are found the same way as when the server runs

from app.core.config import get_settings  # noqa: E402
from app.services import hindsight_service as hs  # noqa: E402
from app.services.demo_data import DEMO  # noqa: E402

BANK = f"{get_settings().hindsight_bank_prefix}-selftest-rahul"


def fail(msg: str, code: int = 1):
    print(f"\nFAIL: {msg}")
    sys.exit(code)


def main() -> None:
    cleanup = "--cleanup" in sys.argv
    settings = get_settings()

    print("== DealMind <-> Hindsight memory test ==")
    if not settings.hindsight_configured:
        fail(
            "Hindsight is not configured.\n"
            "  Missing: HINDSIGHT_API_KEY (for Hindsight Cloud)  OR  HINDSIGHT_BASE_URL (self-hosted server).\n"
            "  Fix: copy .env.example to .env in the project root, fill in the value, and run this again.\n"
            "  See README.md > 'Setting up Hindsight'.",
            code=2,
        )
    print(f"Mode:     {settings.hindsight_mode}")
    print(f"Base URL: {settings.resolved_hindsight_url}")
    print(f"API key:  {'set' if settings.hindsight_api_key else 'not set (fine for a local self-hosted server)'}")

    st = hs.status()
    if not st["reachable"]:
        fail(f"Cannot reach Hindsight: {st['error']}\n  Check the URL/API key in .env and your network.")
    print(f"Server:   reachable (version {st['server_version']})\n")

    client = hs.get_client()

    print(f"1) Creating memory bank '{BANK}' for {DEMO['name']} / {DEMO['company']} / {DEMO['industry']}")
    try:
        client.create_bank(
            bank_id=BANK,
            name=f"{DEMO['name']} - {DEMO['company']} (self-test)",
            mission="Sales memory for the DealMind self-test customer.",
        )
    except Exception as exc:  # noqa: BLE001
        fail(f"create_bank failed: {type(exc).__name__}: {exc}")

    print("2) Sending interactions to Hindsight (retain)")
    for n, step in enumerate(DEMO["steps"], 1):
        text = (
            f"Sales interaction with {DEMO['name']} from {DEMO['company']} ({DEMO['industry']}). "
            f"Interaction type: {step['kind']}. Note: {step['content']}"
        )
        try:
            client.retain(
                bank_id=BANK,
                content=text,
                context=f"sales {step['kind']} with {DEMO['name']}",
                document_id=f"selftest-interaction-{n}",
                retain_async=settings.hindsight_retain_async,
            )
        except Exception as exc:  # noqa: BLE001
            fail(f"retain #{n} failed: {type(exc).__name__}: {exc}")
        print(f"   retained: {step['content']}")

    print("\n3) Recalling memories: 'What does Rahul care about?'")
    memories = []
    for attempt in range(1, 13):  # asynchronous retain can take a while; poll up to ~60s
        try:
            res = client.recall(bank_id=BANK, query="What does Rahul care about?", max_tokens=2048)
        except Exception as exc:  # noqa: BLE001
            fail(f"recall failed: {type(exc).__name__}: {exc}")
        memories = res.results or []
        if memories:
            break
        print(f"   no memories yet (attempt {attempt}/12) - waiting 5s...")
        time.sleep(5)
    for m in memories:
        print(f"   - {m.text}")

    print("\n4) Reflecting: 'Prepare me for Rahul's meeting.'")
    try:
        answer = client.reflect(bank_id=BANK, query=DEMO["question"], budget="low")
        print("   " + (answer.text or "").strip().replace("\n", "\n   "))
    except Exception as exc:  # noqa: BLE001
        fail(f"reflect failed: {type(exc).__name__}: {exc}")

    if cleanup:
        try:
            client.delete_bank(bank_id=BANK)
            print(f"\nCleaned up test bank '{BANK}'.")
        except Exception as exc:  # noqa: BLE001
            print(f"\n(cleanup failed: {exc})")

    if not memories:
        fail("Hindsight accepted the data but recall returned nothing. Check the Hindsight server LLM settings/logs.")
    print(f"\nPASS: Hindsight returned {len(memories)} remembered fact(s). Memory is working.")


if __name__ == "__main__":
    try:
        main()
    finally:
        hs.close_client()
