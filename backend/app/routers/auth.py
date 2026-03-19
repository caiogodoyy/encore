import secrets

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import RedirectResponse

from app.config import settings
from app.services import spotify, youtube
from app.services.session import create_session, get_session, update_session

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Spotify ──────────────────────────────────────────────────────────────────


@router.get("/spotify/login")
async def spotify_login(session_id: str | None = Cookie(None)):
    if not session_id:
        session_id = await create_session()

    state = f"{session_id}:{secrets.token_urlsafe(16)}"
    await update_session(session_id, {"spotify_oauth_state": state})

    redirect = RedirectResponse(url=spotify.get_authorize_url(state))
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return redirect


@router.get("/spotify/callback")
async def spotify_callback(code: str, state: str):
    session_id = state.split(":")[0]
    session = await get_session(session_id)

    if session is None or session.get("spotify_oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_data = await spotify.exchange_code(code)

    await update_session(
        session_id,
        {
            "spotify_access_token": token_data["access_token"],
            "spotify_refresh_token": token_data.get("refresh_token", ""),
            "spotify_connected": True,
        },
    )

    redirect = RedirectResponse(url=f"{settings.frontend_url}?spotify=connected")
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return redirect


# ── YouTube / Google ─────────────────────────────────────────────────────────


@router.get("/youtube/login")
async def youtube_login(session_id: str | None = Cookie(None)):
    if not session_id:
        session_id = await create_session()

    state = f"{session_id}:{secrets.token_urlsafe(16)}"
    await update_session(session_id, {"youtube_oauth_state": state})

    redirect = RedirectResponse(url=youtube.get_authorize_url(state))
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return redirect


@router.get("/youtube/callback")
async def youtube_callback(code: str, state: str):
    session_id = state.split(":")[0]
    session = await get_session(session_id)

    if session is None or session.get("youtube_oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_data = await youtube.exchange_code(code)

    await update_session(
        session_id,
        {
            "youtube_access_token": token_data["access_token"],
            "youtube_refresh_token": token_data.get("refresh_token", ""),
            "youtube_connected": True,
        },
    )

    redirect = RedirectResponse(url=f"{settings.frontend_url}?youtube=connected")
    redirect.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return redirect


# ── Status ───────────────────────────────────────────────────────────────────


@router.get("/status")
async def auth_status(session_id: str | None = Cookie(None)):
    if not session_id:
        return {"spotify": False, "youtube": False}

    session = await get_session(session_id)
    if session is None:
        return {"spotify": False, "youtube": False}

    return {
        "spotify": session.get("spotify_connected", False),
        "youtube": session.get("youtube_connected", False),
    }
