# In-memory token storage (For demonstration. Use a real database like PostgreSQL in production!)
# Maps a user ID (e.g., "test_user") to their tokens.
user_tokens = {
    "test_user": {
        "google": {"access_token": None, "refresh_token": None},
        "microsoft": {"access_token": None, "refresh_token": None}
    }
}