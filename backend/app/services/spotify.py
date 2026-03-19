from urllib.parse import urlencode
import asyncio
import json
import logging
import re

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_EMBED_URL = "https://open.spotify.com/embed/playlist"

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


async def _fetch_embed_tracks(playlist_id: str) -> list[dict]:
    """Scrape track data from the Spotify embed page.

    The embed page includes a __NEXT_DATA__ JSON blob with track titles
    and artists, bypassing the Web API Basic Quota Mode restriction.
    Returns up to 100 tracks per page (Spotify embed limit).
    """
    url = f"{SPOTIFY_EMBED_URL}/{playlist_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning("Embed page returned %s for playlist %s", resp.status_code, playlist_id)
            return []

    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        resp.text,
    )
    if not match:
        logger.warning("No __NEXT_DATA__ found in embed page for %s", playlist_id)
        return []

    try:
        next_data = json.loads(match.group(1))
        entity = next_data["props"]["pageProps"]["state"]["data"]["entity"]
        track_list = entity.get("trackList", [])
    except (KeyError, json.JSONDecodeError) as e:
        logger.warning("Failed to parse embed data for %s: %s", playlist_id, e)
        return []

    tracks: list[dict] = []
    for t in track_list:
        title = t.get("title", "")
        artist = t.get("subtitle", "")
        if title:
            tracks.append({
                "name": title,
                "artists": artist,
                "album": "",
                "query": f"{title} {artist}",
            })
    return tracks


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
                tracks_info = item.get("tracks") or {}
                playlists.append(
                    {
                        "id": item["id"],
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "track_count": tracks_info.get("total") or 0,
                        "image": (
                            item["images"][0]["url"] if item.get("images") else None
                        ),
                    }
                )
            url = data.get("next")

    # If track counts are 0 (Basic Quota Mode), get counts from embed page
    if playlists and all(p["track_count"] == 0 for p in playlists):
        async def _get_count(p: dict) -> None:
            try:
                embed_tracks = await _fetch_embed_tracks(p["id"])
                p["track_count"] = len(embed_tracks)
            except Exception:
                pass

        await asyncio.gather(*[_get_count(p) for p in playlists])

    return playlists


async def get_playlist_tracks(access_token: str, playlist_id: str) -> list[dict]:
    """Fetch tracks from a playlist. Tries the Web API first, falls back
    to scraping the Spotify embed page (bypasses Basic Quota Mode)."""
    tracks: list[dict] = []

    async with httpx.AsyncClient() as client:
        # Attempt 1: dedicated tracks endpoint
        url: str | None = f"{SPOTIFY_API_BASE}/playlists/{playlist_id}/tracks?limit=100"
        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (401, 403):
                logger.warning("Tracks endpoint returned %s, trying embed fallback", resp.status_code)
                break
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                track = item.get("track")
                if track is None:
                    continue
                artists = ", ".join(a["name"] for a in track.get("artists", []))
                tracks.append(
                    {
                        "name": track["name"],
                        "artists": artists,
                        "album": track.get("album", {}).get("name", ""),
                        "query": f"{track['name']} {artists}",
                    }
                )
            url = data.get("next")
            if tracks:
                return tracks

    # Attempt 2: embed page scraping (bypasses Basic Quota Mode)
    logger.info("Falling back to embed page for playlist %s", playlist_id)
    tracks = await _fetch_embed_tracks(playlist_id)
    if tracks:
        return tracks

    logger.error(
        "Could not fetch tracks for playlist %s from any source",
        playlist_id,
    )
    return tracks
