from app.services import google_calendar, outlook_calendar

class CalendarServiceDispatcher:
    """
    Open-Closed Principle: New providers can be added to this registry 
    without modifying the core event route logic.
    """
    
    _fetch_handlers = {
        "google": google_calendar.fetch_events,
        "microsoft": outlook_calendar.fetch_events,
    }

    @classmethod
    async def fetch_events_for_account(cls, provider: str, access_token: str, days: int):
        handler = cls._fetch_handlers.get(provider.lower())
        if not handler:
            raise ValueError(f"Unsupported calendar provider: {provider}")
        
        # Dispatch to the specific provider's implementation
        return await handler(access_token, days)