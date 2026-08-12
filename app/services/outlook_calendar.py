import httpx
from typing import List

async def fetch_events(access_token: str, time_min: str, time_max: str) -> List[dict]:
    url = f"https://graph.microsoft.com/v1.0/me/calendarview"
    params = {
        "startDateTime": time_min,
        "endDateTime": time_max,
        "$select": "id,subject,bodyPreview,start,end"
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.timezone="UTC"'  # Forces Outlook to return explicit UTC (Z) times
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        
    if response.status_code != 200:
        print(f"Microsoft API Error: {response.text}")
        return []
         
    data = response.json()
    events = []
    for item in data.get("value", []):
        start = item.get("start", {})
        end = item.get("end", {})
        
        # Ensure the Z suffix is present so JavaScript parses it accurately as UTC
        start_dt = start.get("dateTime")
        end_dt = end.get("dateTime")
        if start_dt and not start_dt.endswith("Z") and "+" not in start_dt:
            start_dt += "Z"
        if end_dt and not end_dt.endswith("Z") and "+" not in end_dt:
            end_dt += "Z"

        events.append({
            "id": item.get("id"),
            "title": item.get("subject", "No Title"),
            "description": item.get("bodyPreview", ""),
            "start": {"dateTime": start_dt, "timeZone": "UTC"},
            "end": {"dateTime": end_dt, "timeZone": "UTC"},
            "source": "microsoft"
        })
    return events

async def create_event(access_token: str, event_data: dict) -> str:
    url = "https://graph.microsoft.com/v1.0/me/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=event_data)
        if res.status_code == 201:
            return res.json().get("id")
        else:
            print(f"Failed to create Microsoft event: {res.text}")
            return None

async def update_event(access_token: str, event_id: str, event_data: dict):
    url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        await client.patch(url, headers=headers, json=event_data)

async def delete_event(access_token: str, event_id: str):
    url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        await client.delete(url, headers=headers)