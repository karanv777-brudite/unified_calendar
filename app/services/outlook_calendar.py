import httpx
from typing import List

import httpx
from typing import List

async def fetch_events(access_token: str, time_min: str, time_max: str) -> List[dict]:
    url = f"https://graph.microsoft.com/v1.0/me/calendarview"
    params = {
        "startDateTime": time_min,
        "endDateTime": time_max,
        "$select": "id,subject,bodyPreview,start,end,isAllDay"  # 👈 Added isAllDay here
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.timezone="UTC"' 
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
        is_all_day = item.get("isAllDay", False)
        
        if is_all_day:
            # Extract just the YYYY-MM-DD date to prevent local timezone shifts (e.g., 5:30 AM bug)
            start_date = start.get("dateTime", "").split("T")[0]
            end_date = end.get("dateTime", "").split("T")[0]
            
            start_obj = {"date": start_date}
            end_obj = {"date": end_date}
        else:
            start_dt = start.get("dateTime")
            end_dt = end.get("dateTime")
            if start_dt and not start_dt.endswith("Z") and "+" not in start_dt:
                start_dt += "Z"
            if end_dt and not end_dt.endswith("Z") and "+" not in end_dt:
                end_dt += "Z"
                
            start_obj = {"dateTime": start_dt, "timeZone": "UTC"}
            end_obj = {"dateTime": end_dt, "timeZone": "UTC"}

        events.append({
            "id": item.get("id"),
            "title": item.get("subject", "No Title"),
            "description": item.get("bodyPreview", ""),
            "start": start_obj,
            "end": end_obj,
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