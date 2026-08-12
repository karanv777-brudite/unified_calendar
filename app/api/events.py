from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import json

from app.schemas.event import UnifiedEvent, EventDateTime
from app.core.db import user_tokens
from app.services import google_calendar, outlook_calendar

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=List[UnifiedEvent])
async def get_unified_events(days: int = 7, user_id: str = "test_user"):
    """Fetches events from all connected provider accounts and returns a unified list."""
    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + timedelta(days=days)).isoformat() + 'Z'
    
    tokens = user_tokens.get(user_id, {})
    unified_events = []
    
    # tokens can now store accounts like: 
    # {"google_personal": {"access_token": "..."}, "google_work": {"access_token": "..."}}
    for account_key, token_data in tokens.items():
        access_token = token_data.get("access_token")
        if not access_token:
            continue
            
        if account_key.startswith("google"):
            g_events = await google_calendar.fetch_events(access_token, time_min, time_max)
            for ge in g_events:
                unified_events.append(UnifiedEvent(
                    id=f"{account_key}_{ge['id']}", # Prefix ID to avoid collisions
                    title=ge['title'], # Optional: tag title with account name
                    description=ge["description"],
                    start=EventDateTime(**ge["start"]), 
                    end=EventDateTime(**ge["end"]),
                    source="google", 
                    original_ids={"google": ge["id"], "account": account_key}
                ))
                
        elif account_key.startswith("microsoft"):
             m_events = await outlook_calendar.fetch_events(access_token, time_min, time_max)
             for me in m_events:
                 unified_events.append(UnifiedEvent(
                    id=f"{account_key}_{me['id']}",
                    title=me['title'],
                    description=me["description"],
                    start=EventDateTime(**me["start"]), 
                    end=EventDateTime(**me["end"]),
                    source="microsoft", 
                    original_ids={"microsoft": me["id"], "account": account_key}
                 ))
             
    return unified_events

@router.post("", response_model=UnifiedEvent)
async def create_event(event: UnifiedEvent, target_account: str = "all", user_id: str = "test_user"):
    """Creates a new event and syncs it to the specified account or all connected accounts."""
    tokens = user_tokens.get(user_id, {})
    created_ids = {}
    
    for account_key, token_data in tokens.items():
        access_token = token_data.get("access_token")
        if not access_token:
            continue
            
        # If a specific account is chosen, skip all other accounts
        if target_account != "all" and account_key != target_account:
            continue
            
        if account_key.startswith("google"):
            payload = {"summary": event.title, "description": event.description, "start": event.start.model_dump(), "end": event.end.model_dump()}
            g_id = await google_calendar.create_event(access_token, payload)
            if g_id: 
                created_ids["google"] = g_id
                created_ids["account"] = account_key

        elif account_key.startswith("microsoft"):
            payload = {"subject": event.title, "body": {"contentType": "HTML", "content": event.description}, "start": event.start.model_dump(), "end": event.end.model_dump()}
            m_id = await outlook_calendar.create_event(access_token, payload)
            if m_id: 
                created_ids["microsoft"] = m_id
                created_ids["account"] = account_key

    if not created_ids:
        raise HTTPException(status_code=400, detail="Failed to create event. Check if the target account is linked and authenticated.")

    event.original_ids = created_ids
    event.source = "unified"
    event.id = f"unified_{datetime.utcnow().timestamp()}" 
    return event

@router.put("/{unified_id}", response_model=UnifiedEvent)
async def update_event(unified_id: str, event_update: UnifiedEvent, user_id: str = "test_user"):
    if not event_update.original_ids:
        raise HTTPException(status_option=400, detail="original_ids mapping required for update.")
        
    tokens = user_tokens.get(user_id, {})
    target_account = event_update.original_ids.get("account")
    
    # If a specific account was saved with the event, update only that account
    if target_account and target_account in tokens:
        access_token = tokens[target_account].get("access_token")
        if target_account.startswith("google"):
             payload = {"summary": event_update.title, "description": event_update.description, "start": event_update.start.model_dump(), "end": event_update.end.model_dump()}
             await google_calendar.update_event(access_token, event_update.original_ids["google"], payload)
        elif target_account.startswith("microsoft"):
             payload = {"subject": event_update.title, "body": {"contentType": "HTML", "content": event_update.description}, "start": event_update.start.model_dump(), "end": event_update.end.model_dump()}
             await outlook_calendar.update_event(access_token, event_update.original_ids["microsoft"], payload)
    else:
        # Fallback loop if account key isn't explicitly tied
        for account_key, token_data in tokens.items():
            access_token = token_data.get("access_token")
            if not access_token: continue
            if "google" in event_update.original_ids and account_key.startswith("google"):
                 payload = {"summary": event_update.title, "description": event_update.description, "start": event_update.start.model_dump(), "end": event_update.end.model_dump()}
                 await google_calendar.update_event(access_token, event_update.original_ids["google"], payload)

    return event_update

@router.delete("/{unified_id}")
async def delete_event(unified_id: str, original_ids: str, user_id: str = "test_user"):
    """Deletes an event from the specific provider account using parsed original_ids."""
    try:
        ids_mapping = json.loads(original_ids)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid original_ids format.")
        
    tokens = user_tokens.get(user_id, {})
    target_account = ids_mapping.get("account")
    
    # Target the exact account the event belonged to
    if target_account and target_account in tokens:
        access_token = tokens[target_account].get("access_token")
        if target_account.startswith("google") and "google" in ids_mapping:
            await google_calendar.delete_event(access_token, ids_mapping["google"])
        elif target_account.startswith("microsoft") and "microsoft" in ids_mapping:
            await outlook_calendar.delete_event(access_token, ids_mapping["microsoft"])
    else:
        # Fallback loop
        for account_key, token_data in tokens.items():
            access_token = token_data.get("access_token")
            if not access_token: continue
            if "google" in ids_mapping and account_key.startswith("google"):
                await google_calendar.delete_event(access_token, ids_mapping["google"])
            elif "microsoft" in ids_mapping and account_key.startswith("microsoft"):
                await outlook_calendar.delete_event(access_token, ids_mapping["microsoft"])

    return {"message": "Event deleted successfully"}