from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict

class EventDateTime(BaseModel):
    dateTime: Optional[str] = None # ISO 8601 string
    date: Optional[str] = None
    timeZone: Optional[str] = "UTC"

class Attendee(BaseModel):
    email: EmailStr
    status: Optional[str] = "pending" # 'pending', 'accepted', 'declined'

class UnifiedEvent(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    start: EventDateTime
    end: EventDateTime
    source: Optional[str] = "unified" # 'google', 'microsoft', or 'unified'
    original_ids: Optional[Dict[str, str]] = Field(default_factory=dict) # e.g., {"google": "id1", "microsoft": "id2"}
    attendees: Optional[List[Attendee]] = Field(default_factory=list)

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_datetime: str  # e.g., "2026-08-10T10:00:00"
    end_datetime: str    # e.g., "2026-08-10T11:00:00"
    timezone: str = "Asia/Kolkata"
    provider: str = "google" # Tells the backend which calendar to push to
    attendees: Optional[List[str]] = Field(default_factory=list)