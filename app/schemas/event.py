from pydantic import BaseModel
from typing import Optional

class EventDateTime(BaseModel):
    dateTime: Optional[str] = None # ISO 8601 string
    date: Optional[str] = None
    timeZone: Optional[str] = "UTC"

class UnifiedEvent(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    start: EventDateTime
    end: EventDateTime
    source: Optional[str] = "unified" # 'google', 'microsoft', or 'unified'
    original_ids: Optional[dict] = {} # e.g., {"google": "id1", "microsoft": "id2"}

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_datetime: str  # e.g., "2026-08-10T10:00:00"
    end_datetime: str    # e.g., "2026-08-10T11:00:00"
    timezone: str = "Asia/Kolkata"
    provider: str = "google" # Tells the backend which calendar to push to