import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs # for async function in fastapi
from sqlalchemy.orm import declarative_base
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL # fetches db url from config instead of searching for it

engine = create_async_engine(DATABASE_URL, echo=False) #because we are using async function, create_engine would cause conflict
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base(cls=AsyncAttrs) # base class for ORM, to use tables as Classes

# FastAPI dependency to yield async database sessions per request
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session