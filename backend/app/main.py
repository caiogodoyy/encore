from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, sync

app = FastAPI(
    title="Encore!",
    description="Sync Spotify playlists to YouTube",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sync.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
