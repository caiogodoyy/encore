import asyncio
import logging

import httpx

from app.services import spotify, youtube
from app.services.session import get_session, update_session

logger = logging.getLogger(__name__)


async def _refresh_spotify_token(session_id: str, session: dict) -> str:
    """Refresh the Spotify token if expired and return a valid one."""
    token = session.get("spotify_access_token", "")
    refresh = session.get("spotify_refresh_token", "")
    if not refresh:
        return token

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code in (401, 403):
        new_data = await spotify.refresh_access_token(refresh)
        token = new_data["access_token"]
        await update_session(
            session_id,
            {
                "spotify_access_token": token,
                "spotify_refresh_token": new_data.get("refresh_token", refresh),
            },
        )
    return token


async def _refresh_youtube_token(session_id: str, session: dict) -> str:
    """Refresh the YouTube token if expired and return a valid one."""
    token = session.get("youtube_access_token", "")
    refresh = session.get("youtube_refresh_token", "")
    if not refresh:
        return token

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true",
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code == 401:
        new_data = await youtube.refresh_access_token(refresh)
        token = new_data["access_token"]
        await update_session(
            session_id,
            {
                "youtube_access_token": token,
                "youtube_refresh_token": new_data.get("refresh_token", refresh),
            },
        )
    return token


async def sync_playlist(session_id: str, playlist_id: str) -> None:
    """Background task: reads a Spotify playlist and recreates it on YouTube."""
    session = await get_session(session_id)
    if session is None:
        logger.error("Session %s not found", session_id)
        return

    spotify_token = await _refresh_spotify_token(session_id, session)
    youtube_token = await _refresh_youtube_token(session_id, session)

    if not spotify_token or not youtube_token:
        await update_session(
            session_id, {"sync_status": "error", "sync_error": "Missing tokens"}
        )
        return

    try:
        await update_session(
            session_id,
            {"sync_status": "reading_playlist", "sync_progress": 0, "sync_error": ""},
        )

        # 1. Read tracks from Spotify
        tracks = await spotify.get_playlist_tracks(spotify_token, playlist_id)
        if not tracks:
            await update_session(
                session_id,
                {
                    "sync_status": "error",
                    "sync_error": "Não foi possível ler as faixas da playlist.",
                },
            )
            return

        # Get playlist name for the YouTube playlist title
        playlists = await spotify.get_user_playlists(spotify_token)
        playlist_name = playlist_id
        for p in playlists:
            if p["id"] == playlist_id:
                playlist_name = p["name"]
                break

        await update_session(
            session_id,
            {
                "sync_status": "creating_playlist",
                "sync_total": len(tracks),
                "sync_progress": 0,
            },
        )

        # 2. Create a new YouTube playlist
        try:
            yt_playlist_id = await youtube.create_playlist(
                youtube_token,
                title=f"{playlist_name} (via Encore!)",
                description=f"Synced from Spotify playlist: {playlist_name}",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                await update_session(
                    session_id,
                    {
                        "sync_status": "error",
                        "sync_error": (
                            "Quota do YouTube atingida. "
                            "Tente novamente amanhã."
                        ),
                    },
                )
                return
            raise

        # 3. Search & add each track
        await update_session(session_id, {"sync_status": "adding_tracks"})

        added = 0
        skipped = 0
        for i, track in enumerate(tracks):
            video_id = await youtube.search_video(youtube_token, track["query"])
            if video_id:
                try:
                    await youtube.add_video_to_playlist(
                        youtube_token, yt_playlist_id, video_id
                    )
                    added += 1
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (401, 403):
                        # Try refreshing the YouTube token once
                        try:
                            session = await get_session(session_id)
                            youtube_token = await _refresh_youtube_token(session_id, session)
                            await youtube.add_video_to_playlist(
                                youtube_token, yt_playlist_id, video_id
                            )
                            added += 1
                        except httpx.HTTPStatusError as e2:
                            if e2.response.status_code == 403:
                                logger.warning(
                                    "YouTube quota likely exceeded at track %d/%d",
                                    i + 1,
                                    len(tracks),
                                )
                                await update_session(
                                    session_id,
                                    {
                                        "sync_status": "completed",
                                        "sync_youtube_playlist_id": yt_playlist_id,
                                        "sync_added": added,
                                        "sync_skipped": len(tracks) - i,
                                        "sync_progress": len(tracks),
                                        "sync_error": (
                                            f"Quota do YouTube atingida após {added} faixas. "
                                            "Tente novamente amanhã para continuar."
                                        ),
                                    },
                                )
                                return
                            raise
                    else:
                        skipped += 1
                        logger.warning(
                            "Failed to add track %s: %s", track["query"], e
                        )
            else:
                skipped += 1
                logger.warning("No YouTube result for: %s", track["query"])

            await update_session(
                session_id,
                {
                    "sync_progress": i + 1,
                    "sync_added": added,
                    "sync_skipped": skipped,
                },
            )

            # Small delay to respect API rate limits
            await asyncio.sleep(0.3)

        await update_session(
            session_id,
            {
                "sync_status": "completed",
                "sync_youtube_playlist_id": yt_playlist_id,
                "sync_added": added,
                "sync_skipped": skipped,
            },
        )

    except Exception as e:
        logger.exception("Sync failed for session %s", session_id)
        await update_session(
            session_id,
            {"sync_status": "error", "sync_error": str(e)},
        )
