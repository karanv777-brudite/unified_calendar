import httpx
from typing import List, Optional

async def fetch_events(access_token: str, time_min: str, time_max: str) -> List[dict]:
    url = f"https://graph.microsoft.com/v1.0/me/calendarview"
    params = {
        "startDateTime": time_min,
        "endDateTime": time_max,
        "$select": "id,subject,bodyPreview,start,end,isAllDay,attendees"
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

        raw_attendees = item.get("attendees", [])
        attendees_list = []
        for att in raw_attendees:
            email = att.get("emailAddress", {}).get("address")
            status_obj = att.get("status", {})
            ms_response = status_obj.get("response", "none")
            status = "accepted" if ms_response == "accepted" else ("declined" if ms_response == "declined" else "pending")
            if email:
                attendees_list.append({
                    "email": email,
                    "status": status
                })

        events.append({
            "id": item.get("id"),
            "title": item.get("subject", "No Title"),
            "description": item.get("bodyPreview", ""),
            "start": start_obj,
            "end": end_obj,
            "source": "microsoft",
            "attendees": attendees_list
        })
    return events

async def create_event(access_token: str, event_data: dict, attendees: Optional[List[str]] = None) -> str:
    url = "https://graph.microsoft.com/v1.0/me/events"
    if attendees:
        valid_attendees = [email.strip() for email in attendees if email and "@" in email]
        if valid_attendees:
            event_data["attendees"] = [
                {
                    "emailAddress": {"address": email, "name": email.split("@")[0]},
                    "type": "required"
                }
                for email in valid_attendees
            ]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=event_data)
        if res.status_code in [200, 201]:
            return res.json().get("id")
        else:
            print(f"Failed to create Microsoft event: {res.status_code} - {res.text}")
            return None

async def update_event(access_token: str, event_id: str, event_data: dict, attendees: Optional[List[str]] = None):
    url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
    if attendees is not None:
        valid_attendees = [email.strip() for email in attendees if email and "@" in email]
        event_data["attendees"] = [
            {
                "emailAddress": {"address": email, "name": email.split("@")[0]},
                "type": "required"
            }
            for email in valid_attendees
        ]

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        res = await client.patch(url, headers=headers, json=event_data)
        if res.status_code not in [200, 204]:
            print(f"Failed to update Microsoft event: {res.status_code} - {res.text}")

async def delete_event(access_token: str, event_id: str):
    url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Prefer": 'outlook.timezone="UTC"'
    }
    async with httpx.AsyncClient() as client:
        await client.delete(url, headers=headers)