from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, events
import app.models
from app.database import engine, Base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create database tables asynchronously on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown actions (if any) can go here


app = FastAPI(
    title="Unified Calendar API", 
    description="Syncs events across Google and Outlook calendars.",
    lifespan=lifespan
)

# This allows your future frontend (e.g., localhost:3000) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Unified Calendar API"}