import uvicorn
import asyncio
from fastapi import FastAPI
from app.api.v1.api import router as api_router
from app.infra.database.database import Database
from app.infra.database.models import Conversions, Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text

Database()
app = FastAPI()
app.include_router(api_router, prefix="/api/v1")
