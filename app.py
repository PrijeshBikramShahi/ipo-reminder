from fastapi import FastAPI

app = FastAPI(title="IPO Reminder Backend")

@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "IPO Reminder Backend is running"}
