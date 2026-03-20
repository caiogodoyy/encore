from fastapi import APIRouter, BackgroundTasks, Cookie, HTTPException

from app.services import spotify as spotify_service
from app.services.session import get_session, update_session
from app.services.sync import sync_playlist, _refresh_spotify_token

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/playlists")
async def list_playlists(session_id: str | None = Cookie(None)):
    """Return the user's Spotify playlists."""
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")

    session = await get_session(session_id)
    if session is None or not session.get("spotify_access_token"):
        raise HTTPException(status_code=401, detail="Spotify not connected")

    token = await _refresh_spotify_token(session_id, session)
    playlists = await spotify_service.get_user_playlists(token)
    return {"playlists": playlists}


@router.post("/start")
async def start_sync(
    playlist_id: str,
    background_tasks: BackgroundTasks,
    session_id: str | None = Cookie(None),
):
    """Start syncing a Spotify playlist to YouTube in the background."""
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")

    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    if not session.get("spotify_access_token"):
        raise HTTPException(status_code=400, detail="Spotify not connected")
    if not session.get("youtube_access_token"):
        raise HTTPException(status_code=400, detail="YouTube not connected")

    background_tasks.add_task(sync_playlist, session_id, playlist_id)

    return {"status": "started", "playlist_id": playlist_id}


@router.get("/status")
async def sync_status(session_id: str | None = Cookie(None)):
    """Return the current sync progress."""
    if not session_id:
        raise HTTPException(status_code=401, detail="No session")

    session = await get_session(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid session")

    return {
        "status": session.get("sync_status"),
        "progress": session.get("sync_progress", 0),
        "total": session.get("sync_total", 0),
        "added": session.get("sync_added", 0),
        "skipped": session.get("sync_skipped", 0),
        "error": session.get("sync_error"),
        "youtube_playlist_id": session.get("sync_youtube_playlist_id"),
    }
