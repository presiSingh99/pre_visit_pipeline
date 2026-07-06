"""Sprint 1 demo UI — a thin client for the extraction service.

This page does exactly one thing: send a transcript to the existing
FastAPI `POST /extract-intake` endpoint and render the validated JSON
response. It contains NO extraction, validation, or clinical logic —
all of that stays in the backend. This is a developer/stakeholder demo,
not the doctor dashboard (that's Sprint 6).

Run:
    uvicorn app.main:app --reload          # terminal 1 (backend)
    streamlit run demo/streamlit_demo.py   # terminal 2 (this demo)
"""

import json
import os
from pathlib import Path

import httpx
import streamlit as st

API_URL = os.getenv("INTAKE_API_URL", "http://127.0.0.1:8000")
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_transcripts" / "sore_throat.txt"

st.set_page_config(page_title="Intake Extraction Demo — Sprint 1", layout="wide")
st.title("Pre-Visit Intake — Extraction Demo (Sprint 1)")
st.caption(
    "Sends a raw patient–AI transcript to the FastAPI backend and shows the "
    "validated intermediate clinical JSON. Extraction only — no diagnosis, "
    "no prescribing, no medical advice. Demo UI, not the clinician dashboard."
)

left, right = st.columns(2)

with left:
    st.subheader("Transcript")
    default_text = ""
    if st.button("Load sample transcript"):
        default_text = SAMPLE_PATH.read_text() if SAMPLE_PATH.exists() else ""
        st.session_state["transcript"] = default_text
    transcript = st.text_area(
        "Patient–AI conversation",
        key="transcript",
        height=380,
        placeholder="Paste an intake conversation transcript here…",
    )
    extract_clicked = st.button("Extract", type="primary", disabled=not transcript.strip())

with right:
    st.subheader("Validated extraction")
    if extract_clicked:
        try:
            with st.spinner("Calling /extract-intake…"):
                response = httpx.post(
                    f"{API_URL}/extract-intake",
                    json={"transcript": transcript},
                    timeout=90,
                )
        except httpx.HTTPError as exc:
            st.error(
                f"Could not reach the backend at {API_URL}: {exc}. "
                "Is FastAPI running? Start it with: uvicorn app.main:app --reload"
            )
        else:
            if response.status_code == 200:
                body = response.json()
                extraction = body["extraction"]
                if extraction.get("red_flags_detected"):
                    st.error(
                        "Red flags reported by patient: "
                        + ", ".join(extraction.get("red_flag_symptoms", []))
                        + " — requires clinician review."
                    )
                st.json(body)
                st.download_button(
                    "Download JSON",
                    data=json.dumps(body, indent=2),
                    file_name="intake_extraction.json",
                    mime="application/json",
                )
            else:
                st.error(f"Backend returned {response.status_code}")
                st.json(response.json())
    else:
        st.info("Enter a transcript and click **Extract**.")
