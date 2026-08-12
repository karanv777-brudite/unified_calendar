from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx
from app.core.config import settings
from app.core.db import user_tokens

router = APIRouter(prefix="/auth", tags=["Authentication"])
FRONTEND_URL = "http://localhost:5173"

@router.get("/google/login")
async def google_login():
    """Redirects the user to Google's OAuth 2.0 consent screen[cite: 2]."""
    # Added userinfo.email scope so we can fetch the account email dynamically
    scope = "https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/userinfo.email"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return RedirectResponse(auth_url)

@router.get("/google/callback")
async def google_callback(code: str, request: Request):
    """Handles the callback from Google, fetches user identity, and stores account-specific tokens[cite: 2]."""
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        token_data = response.json()
        
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data["error"])
            
        access_token = token_data.get("access_token")
        
        # Fetch the user's email address to uniquely segment multiple Google accounts
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo = userinfo_response.json()
        email = userinfo.get("email", f"google_{code[:6]}")

    user_id = "test_user" 
    if user_id not in user_tokens:
        user_tokens[user_id] = {}
        
    account_key = f"google_{email}"
    existing_token = user_tokens[user_id].get(account_key, {})
    refresh_token = token_data.get("refresh_token") or existing_token.get("refresh_token")

    user_tokens[user_id][account_key] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": email
    }
        
    print ({"message": f"Google authentication successful for {email}"})
    return RedirectResponse(url=FRONTEND_URL, status_code=303)

@router.get("/microsoft/login")
async def microsoft_login():
    """Redirects the user to Microsoft's OAuth 2.0 consent screen[cite: 2]."""
    # Added User.Read scope to fetch the account profile/email dynamically
    scope = "Calendars.ReadWrite offline_access User.Read"
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={settings.MICROSOFT_CLIENT_ID}&"
        f"redirect_uri={settings.MICROSOFT_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scope}"
    )
    return RedirectResponse(auth_url)

@router.get("/microsoft/callback")
async def microsoft_callback(code: str, request: Request):
    """Handles the callback from Microsoft, fetches user identity, and stores account-specific tokens[cite: 2]."""
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "scope": "Calendars.ReadWrite User.Read",
        "code": code,
        "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        token_data = response.json()

        if "error" in token_data:
            raise HTTPException(status_code=400, detail=token_data.get("error_description", "Unknown error"))

        access_token = token_data.get("access_token")

        # Fetch user email from Microsoft Graph to uniquely segment multiple accounts
        userinfo_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        userinfo = userinfo_response.json()
        email = userinfo.get("mail") or userinfo.get("userPrincipalName", f"microsoft_{code[:6]}")

    user_id = "test_user"
    if user_id not in user_tokens:
        user_tokens[user_id] = {}
        
    account_key = f"microsoft_{email}"
    existing_token = user_tokens[user_id].get(account_key, {})
    refresh_token = token_data.get("refresh_token") or existing_token.get("refresh_token")

    user_tokens[user_id][account_key] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": email
    }
        
    print ({"message": f"Microsoft authentication successful for {email}"})
    return RedirectResponse(url=FRONTEND_URL, status_code=303)

@router.get("/accounts")
async def get_connected_accounts(user_id: str = "test_user"):
    """Returns the precise link status of Google and Microsoft providers."""
    tokens = user_tokens.get(user_id, {})
    
    google_accounts = []
    microsoft_accounts = []
    
    for key, data in tokens.items():
        if data.get("access_token"):
            if key.startswith("google"):
                google_accounts.append({"key": key, "email": data.get("email", "Connected Google Account"), "linked": True})
            elif key.startswith("microsoft"):
                microsoft_accounts.append({"key": key, "email": data.get("email", "Connected Microsoft Account"), "linked": True})
                
    # If no accounts are found, return default unlinked states so the UI always shows options
    response_data = []
    
    if google_accounts:
        response_data.extend(google_accounts)
    else:
        response_data.append({"key": "google_placeholder", "provider": "Google", "email": "No account linked", "linked": False})
        
    if microsoft_accounts:
        response_data.extend(microsoft_accounts)
    else:
        response_data.append({"key": "microsoft_placeholder", "provider": "Microsoft", "email": "No account linked", "linked": False})
        
    # Format provider names cleanly
    for item in response_data:
        if "provider" not in item:
            item["provider"] = "Google" if item["key"].startswith("google") else "Microsoft"

    return response_data