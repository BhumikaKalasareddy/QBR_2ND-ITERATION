from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(title="QBR Telemetry Service")
app.include_router(api_router, prefix="/api/v1")