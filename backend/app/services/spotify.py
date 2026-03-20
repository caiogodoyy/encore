from urllib.parse import urlencode
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SCOPES = "playlist-read-private playlist-read-collaborative"


def get_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
        )
        resp.raise_for_status()
        return resp.json()


async def get_user_playlists(access_token: str) -> list[dict]:
    playlists: list[dict] = []
    url = f"{SPOTIFY_API_BASE}/me/playlists?limit=50"

    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                if item is None:
                    continue
                items_info = item.get("items") or {}
                playlists.append(
                    {
                        "id": item["id"],
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "track_count": items_info.get("total") or 0,
                        "image": (
                            item["images"][0]["url"] if item.get("images") else None
                        ),
                    }
                )
            url = data.get("next")

    return playlists


async def get_playlist_tracks(access_token: str, playlist_id: str) -> list[dict]:
    """Fetch all tracks from a playlist using the /items endpoint."""
    tracks: list[dict] = []
    url: str | None = (
        f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/items?limit=100"
    )
    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (401, 403):
                logger.warning(
                    "Items endpoint returned %s for playlist %s",
                    resp.status_code,
                    playlist_id,
                )
                return []
            resp.raise_for_status()
            data = resp.json()
            for entry in data.get("items", []):
                track = entry.get("item")
                if track is None:
                    continue
                artists = ", ".join(
                    a["name"] for a in track.get("artists", [])
                )
                tracks.append(
                    {
                        "name": track["name"],
                        "artists": artists,
                        "album": track.get("album", {}).get("name", ""),
                        "query": f"{track['name']} {artists}",
                    }
                )
            url = data.get("next")

    if not tracks:
        logger.error("Could not fetch tracks for playlist %s", playlist_id)
    return tracks
