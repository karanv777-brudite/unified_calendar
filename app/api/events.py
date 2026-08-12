from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from datetime import datetime, timedelta
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.event import UnifiedEvent, EventDateTime
from app.database import get_db
from app.repositories.token_repository import TokenRepository
from app.services import google_calendar, outlook_calendar

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=List[UnifiedEvent])
async def get_unified_events(
    days: int = 7, 
    user_id: str = "test_user", 
    db: AsyncSession = Depends(get_db)
):
    """Fetches events from all connected provider accounts and returns a unified list using PostgreSQL tokens."""
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'
    
    # Fetch tokens securely from PostgreSQL database
    tokens = await TokenRepository.get_tokens_by_user(db, user_id)
    unified_events = []
    
    for acc in tokens:
        access_token = acc.access_token
        if not access_token:
            continue
            
        account_key = acc.account_key
        
        if acc.provider == "google":
            g_events = await google_calendar.fetch_events(access_token, time_min, time_max)
            for ge in g_events:
                unified_events.append(UnifiedEvent(
                    id=f"{account_key}_{ge['id']}", 
                    title=ge['title'], 
                    description=ge.get("description"),
                    start=EventDateTime(**ge["start"]), 
                    end=EventDateTime(**ge["end"]),
                    source="google", 
                    original_ids={"google": ge["id"], "account": account_key}
                ))
                
        elif acc.provider == "microsoft":
             m_events = await outlook_calendar.fetch_events(access_token, time_min, time_max)
             for me in m_events:
                 unified_events.append(UnifiedEvent(
                    id=f"{account_key}_{me['id']}",
                    title=me['title'],
                    description=me.get("description"),
                    start=EventDateTime(**me["start"]), 
                    end=EventDateTime(**me["end"]),
                    source="microsoft", 
                    original_ids={"microsoft": me["id"], "account": account_key}
                 ))
               
    return unified_events

@router.post("", response_model=UnifiedEvent)
async def create_event(
    event: UnifiedEvent, 
    target_account: List[str] = Query(["all"]), 
    user_id: str = "test_user",
    db: AsyncSession = Depends(get_db)
):
    """Creates a new event and syncs it to the specified accounts or all connected accounts using DB tokens."""
    tokens = await TokenRepository.get_tokens_by_user(db, user_id)
    created_ids = {}
    
    for acc in tokens:
        access_token = acc.access_token
        if not access_token:
            continue
            
        account_key = acc.account_key
        
        # Since target_account is now a List[str], check if "all" is selected or this specific account key is in the list
        is_targeted = "all" in target_account or account_key in target_account
        if not is_targeted:
            continue
            
        if acc.provider == "google":
            payload = {
                "summary": event.title, 
                "description": event.description, 
                "start": event.start.model_dump(exclude_none=True), 
                "end": event.end.model_dump(exclude_none=True)
            }
            g_id = await google_calendar.create_event(access_token, payload)
            if g_id: 
                created_ids["google"] = g_id
                created_ids["account"] = account_key

        elif acc.provider == "microsoft":
            start_data = event.start.model_dump(exclude_none=True)
            end_data = event.end.model_dump(exclude_none=True)
            
            is_all_day = "date" in start_data
            
            if is_all_day:
                start_dt = f"{start_data['date']}T00:00:00"
                end_dt = f"{end_data.get('date', start_data['date'])}T00:00:00"
                ms_start = {"dateTime": start_dt, "timeZone": "UTC"}
                ms_end = {"dateTime": end_dt, "timeZone": "UTC"}
            else:
                ms_start = {
                    "dateTime": start_data.get("dateTime"),
                    "timeZone": start_data.get("timeZone", "UTC")
                }
                ms_end = {
                    "dateTime": end_data.get("dateTime"),
                    "timeZone": end_data.get("timeZone", "UTC")
                }

            payload = {
                "subject": event.title, 
                "body": {"contentType": "HTML", "content": event.description or ""}, 
                "start": ms_start, 
                "end": ms_end,
                "isAllDay": is_all_day
            }
            m_id = await outlook_calendar.create_event(access_token, payload)
            if m_id: 
                created_ids["microsoft"] = m_id
                created_ids["account"] = account_key

    if not created_ids:
        raise HTTPException(status_code=400, detail="Failed to create event. Check if the target accounts are linked and authenticated.")

    event.original_ids = created_ids
    event.source = "unified"
    event.id = f"unified_{datetime.utcnow().timestamp()}" 
    return event

@router.put("/{unified_id}", response_model=UnifiedEvent)
async def update_event(
    unified_id: str, 
    event_update: UnifiedEvent, 
    user_id: str = "test_user",
    db: AsyncSession = Depends(get_db)
):
    if not event_update.original_ids:
        raise HTTPException(status_code=400, detail="original_ids mapping required for update.")
        
    tokens = await TokenRepository.get_tokens_by_user(db, user_id)
    token_map = {t.account_key: t for t in tokens}
    target_account = event_update.original_ids.get("account")
    
    if target_account and target_account in token_map:
        acc = token_map[target_account]
        access_token = acc.access_token
        if acc.provider == "google":
             payload = {
                 "summary": event_update.title, 
                 "description": event_update.description, 
                 "start": event_update.start.model_dump(exclude_none=True), 
                 "end": event_update.end.model_dump(exclude_none=True)
             }
             await google_calendar.update_event(access_token, event_update.original_ids["google"], payload)
        elif acc.provider == "microsoft":
             start_data = event_update.start.model_dump(exclude_none=True)
             end_data = event_update.end.model_dump(exclude_none=True)
             is_all_day = "date" in start_data
             
             if is_all_day:
                 ms_start = {"dateTime": f"{start_data['date']}T00:00:00", "timeZone": "UTC"}
                 ms_end = {"dateTime": f"{end_data.get('date', start_data['date'])}T00:00:00", "timeZone": "UTC"}
             else:
                 ms_start = {"dateTime": start_data.get("dateTime"), "timeZone": start_data.get("timeZone", "UTC")}
                 ms_end = {"dateTime": end_data.get("dateTime"), "timeZone": end_data.get("timeZone", "UTC")}

             payload = {
                 "subject": event_update.title, 
                 "body": {"contentType": "HTML", "content": event_update.description or ""}, 
                 "start": ms_start, 
                 "end": ms_end,
                 "isAllDay": is_all_day
             }
             await outlook_calendar.update_event(access_token, event_update.original_ids["microsoft"], payload)
    else:
        for acc in tokens:
            access_token = acc.access_token
            if not access_token: continue
            if "google" in event_update.original_ids and acc.provider == "google":
                 payload = {
                     "summary": event_update.title, 
                     "description": event_update.description, 
                     "start": event_update.start.model_dump(exclude_none=True), 
                     "end": event_update.end.model_dump(exclude_none=True)
                 }
                 await google_calendar.update_event(access_token, event_update.original_ids["google"], payload)

    return event_update

@router.delete("/{unified_id}")
async def delete_event(
    unified_id: str, 
    original_ids: str, 
    user_id: str = "test_user",
    db: AsyncSession = Depends(get_db)
):
    """Deletes an event from the specific provider account using parsed original_ids."""
    try:
        ids_mapping = json.loads(original_ids)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid original_ids format.")
        
    tokens = await TokenRepository.get_tokens_by_user(db, user_id)
    token_map = {t.account_key: t for t in tokens}
    target_account = ids_mapping.get("account")
    
    if target_account and target_account in token_map:
        acc = token_map[target_account]
        access_token = acc.access_token
        if acc.provider == "google" and "google" in ids_mapping:
            await google_calendar.delete_event(access_token, ids_mapping["google"])
        elif acc.provider == "microsoft" and "microsoft" in ids_mapping:
            await outlook_calendar.delete_event(access_token, ids_mapping["microsoft"])
    else:
        for acc in tokens:
            access_token = acc.access_token
            if not access_token: continue
            if "google" in ids_mapping and acc.provider == "google":
                await google_calendar.delete_event(access_token, ids_mapping["google"])
            if "microsoft" in ids_mapping and acc.provider == "microsoft":
                await outlook_calendar.delete_event(access_token, ids_mapping["microsoft"])

    return {"message": "Event deleted successfully"}