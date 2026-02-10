from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import db


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
    return {"status": "ok", "message": "IPO Reminder Backend is running"}


@app.get("/ipos/upcoming")
def get_upcoming_ipos() -> List[Dict[str, str]]:
    return SAMPLE_IPOS


if __name__ == "__main__":
    # Initialize database
    db.init_db()
    
    # Run development server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
