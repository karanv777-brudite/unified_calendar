import httpx
from typing import List

async def fetch_events(access_token: str, time_min: str, time_max: str) -> List[dict]:
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        
    if response.status_code != 200:
        print(f"Google API Error: {response.text}")
        return [] 
        
    data = response.json()
    events = []
    for item in data.get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})
        
        # Safely parse dates (Google returns 'date' for all-day, 'dateTime' for timed)
        start_dt = start.get("dateTime")
        if not start_dt:
            start_dt = f"{start.get('date')}T00:00:00Z"
            
        end_dt = end.get("dateTime")
        if not end_dt:
            end_dt = f"{end.get('date')}T23:59:59Z"
        
        events.append({
            "id": item.get("id"),
            "title": item.get("summary", "No Title"),
            "description": item.get("description", ""),
            "start": {"dateTime": start_dt, "timeZone": start.get("timeZone", "UTC")},
            "end": {"dateTime": end_dt, "timeZone": end.get("timeZone", "UTC")},
            "source": "google"
        })
    return events

async def create_event(access_token: str, event_data: dict) -> str:
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=event_data)
        if res.status_code == 200:
            return res.json().get("id")
        else:
            print(f"Failed to create Google event: {res.text}")
            return None

async def update_event(access_token: str, event_id: str, event_data: dict):
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        await client.put(url, headers=headers, json=event_data)

async def delete_event(access_token: str, event_id: str):
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(url, headers=headers)