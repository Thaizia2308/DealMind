# DealMind judge demo (2-4 minutes)

Before you start: backend and frontend running, sidebar shows green **"Hindsight connected"**. (Optional dry run: `python scripts\test_memory.py`.)

## Script

1. **Open http://localhost:5173.** Say: *"DealMind is a sales assistant with long-term memory, powered by Hindsight."*
2. Click **Start judge demo (Rahul)**. This creates Rahul / ABC Corp / SaaS with **no interactions yet**. Point at the bank id under his name: *"He has his own Hindsight memory bank."*
3. **BEFORE MEMORY.** On the **Meeting prep** tab click **Show without memory**. An amber card appears: *"Generic template - no memory used"*. Say: *"This is what an assistant with no memory gives you: a generic checklist."*
4. **Build memory.** In the yellow-blue "Judge demo" box click **Add next interaction** five times (each shows **Stored in Hindsight**):
   1. Rahul is interested in the Enterprise Plan.
   2. Rahul thinks pricing is high.
   3. Security is very important to Rahul.
   4. Rahul asked about SOC 2 compliance.
   5. Rahul wants a 30-day evaluation.
5. **AFTER MEMORY.** Click **Prepare me for Rahul's meeting**. Wait for the spinner (Hindsight is recalling and reasoning; 10-30 s). A blue **"Built from Hindsight memory"** card appears next to the generic one. Expected: the briefing mentions the Enterprise Plan interest, the pricing objection, security/SOC 2, and the 30-day evaluation.
6. Open **"Memories Hindsight recalled"** under the answer: *"These are the facts Hindsight retrieved."*
7. Optional (30 s): **Ask about customer** -> "What is Rahul most worried about?"; **Follow-up** -> **Write follow-up** to show a draft that references SOC 2 and the evaluation.

## What to point out: before vs after
| | BEFORE memory | AFTER memory |
|---|---|---|
| Badge | Generic template - no memory used | Built from Hindsight memory |
| Content | Standard checklist, could be about anyone | Rahul's interest, objection, priority, request |
| Source | Fixed text in DealMind | Hindsight `recall` + `reflect` |

## If something goes wrong on stage
- **Amber "Not stored in Hindsight"** on an interaction: click **Retry**; read the message next to it.
- **Answer is very short or misses a point:** wait a few seconds and click prepare again (Hindsight processing can lag if `HINDSIGHT_RETAIN_ASYNC=true`; keep it `false` for demos).
- **Reset for another run:** click **Delete customer** (also removes the Hindsight bank), then **Start judge demo** again.
