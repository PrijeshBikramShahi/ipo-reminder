from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict

app = FastAPI(title="IPO Reminder Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_IPOS = [
    {
        "company": "ABC Ltd.",
        "startDate": "2026-02-15",
        "endDate": "2026-02-19"
    },
    {
        "company": "XYZ Corporation",
        "startDate": "2026-02-20",
        "endDate": "2026-02-24"
    },
    {
        "company": "KTM Motors",
        "startDate": "2026-03-01",
        "endDate": "2026-03-05"
    }
]


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "IPO Reminder Backend is running"}


@app.get("/ipos/upcoming")
def get_upcoming_ipos() -> List[Dict[str, str]]:
    """
    Get upcoming IPO listings
    """
    return SAMPLE_IPOS
