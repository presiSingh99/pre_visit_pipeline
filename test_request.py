"""Manual end-to-end test against a running server (requires real API key).

Usage:
    uvicorn app.main:app --reload   # terminal 1
    python test_request.py          # terminal 2
"""

import json
from pathlib import Path

import httpx

transcript = Path("data/sample_transcripts/sore_throat.txt").read_text()

response = httpx.post(
    "http://127.0.0.1:8000/extract-intake",
    json={"transcript": transcript},
    timeout=90,
)
print("Status:", response.status_code)
print(json.dumps(response.json(), indent=2))
