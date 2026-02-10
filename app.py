from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from pydantic import BaseModel
import db

app = FastAPI(title="IPO Reminder Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request validation
class IPOEntry(BaseModel):
    company: str
    startDate: str
    endDate: str

class IPOBulkUpdate(BaseModel):
    ipos: List[IPOEntry]
    source: str = "scraper"


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    db.init_db()
    print("✅ Database initialized and ready")


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "IPO Reminder Backend is running",
        "version": "1.0.0"
    }


@app.get("/ipos/upcoming")
def get_upcoming_ipos() -> List[Dict[str, str]]:
    """
    Get upcoming IPO listings
    
    Returns:
        List of IPO objects with company, startDate, and endDate fields
    """
    try:
        ipos = db.get_upcoming_ipos()
        return ipos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/ipos/update")
def update_ipos(data: IPOBulkUpdate):
    """
    Bulk update IPO entries (used by GitHub Actions scraper)
    
    Args:
        data: IPOBulkUpdate object containing list of IPOs and source
    
    Returns:
        Status message with count of updated records
    """
    try:
        # Clear existing IPOs
        db.clear_all_ipos()
        
        # Convert Pydantic models to dicts
        ipos_data = [ipo.dict() for ipo in data.ipos]
        
        # Save new IPOs
        count = db.save_ipos(ipos_data)
        
        print(f"✅ Updated database with {count} IPO records from {data.source}")
        
        return {
            "status": "success",
            "message": f"Updated {count} IPO records",
            "count": count,
            "source": data.source
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.get("/ipos/stats")
def get_stats():
    """Get database statistics"""
    try:
        count = db.get_ipo_count()
        return {
            "total_ipos": count,
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Run the server using import string for reload support
    uvicorn.run(
        "app:app",  # Import string format: "module:app_instance"
        host="0.0.0.0",
        port=8000,
        reload=True
    )