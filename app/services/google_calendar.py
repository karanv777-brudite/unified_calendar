import httpx
from typing import List, Optional

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
        
        if "date" in start:
            start_val = {"date": start.get("date")}
            end_date = end.get("date") or start.get("date")
            end_val = {"date": end_date}
        else:
            start_val = {
                "dateTime": start.get("dateTime"), 
                "timeZone": start.get("timeZone", "UTC")
            }
            end_val = {
                "dateTime": end.get("dateTime"), 
                "timeZone": end.get("timeZone", "UTC")
            }
        
        # Map Google attendees to unified format
        raw_attendees = item.get("attendees", [])
        attendees_list = []
        for att in raw_attendees:
            g_status = att.get("responseStatus", "needsAction")
            status = "accepted" if g_status == "accepted" else ("declined" if g_status == "declined" else "pending")
            attendees_list.append({
                "email": att.get("email"),
                "status": status
            })

        events.append({
            "id": item.get("id"),
            "title": item.get("summary", "No Title"),
            "description": item.get("description", ""),
            "start": start_val,
            "end": end_val,
            "source": "google",
            "attendees": attendees_list
        })
    return events

async def create_event(access_token: str, event_data: dict, attendees: Optional[List[str]] = None) -> str:
    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    if attendees:
        event_data["attendees"] = [{"email": email} for email in attendees]

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=event_data)
        if res.status_code == 200:
            return res.json().get("id")
        else:
            print(f"Failed to create Google event: {res.text}")
            return None

async def update_event(access_token: str, event_id: str, event_data: dict, attendees: Optional[List[str]] = None):
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    if attendees:
        event_data["attendees"] = [{"email": email} for email in attendees]

    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        await client.put(url, headers=headers, json=event_data)

async def delete_event(access_token: str, event_id: str):
    url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        await client.delete(url, headers=headers)