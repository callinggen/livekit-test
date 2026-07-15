from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.campaigns import router as campaign_router
from app.api.calls import router as call_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="Calling Platform API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(call_router, prefix="/api", tags=["Calls"])
app.include_router(campaign_router, prefix="/api", tags=["Campaigns"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Backend is working",
    }