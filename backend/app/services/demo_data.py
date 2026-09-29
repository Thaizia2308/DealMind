"""The judge-demo script. Single source of truth for the UI, API and docs."""

DEMO = {
    "name": "Rahul",
    "company": "ABC Corp",
    "industry": "SaaS",
    "steps": [
        {"kind": "call", "content": "Rahul is interested in the Enterprise Plan."},
        {"kind": "call", "content": "Rahul thinks pricing is high."},
        {"kind": "meeting", "content": "Security is very important to Rahul."},
        {"kind": "email", "content": "Rahul asked about SOC 2 compliance."},
        {"kind": "call", "content": "Rahul wants a 30-day evaluation."},
    ],
    "question": "Prepare me for Rahul's meeting.",
}
