from urllib.parse import urlencode
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
INNERTUBE_SEARCH_URL = "https://www.youtube.com/youtubei/v1/search"

SCOPES = "https://www.googleapis.com/auth/youtube"


def get_authorize_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "response_type": "code",
        "redirect_uri": settings.google_redirect_uri,
        "scope": SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.google_redirect_uri,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def search_video(access_token: str, query: str) -> str | None:
    """Search YouTube for a video matching the query. Returns video ID or None.

    Uses YouTube's innertube API to avoid consuming Data API quota
    (the official search endpoint costs 100 units per call).
    """
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.00.00",
                "hl": "en",
                "gl": "US",
            }
        },
        "query": query,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            INNERTUBE_SEARCH_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            params={"prettyPrint": "false"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.warning("Innertube search returned %s for query: %s", resp.status_code, query)
            return None

    try:
        data = resp.json()
        sections = (
            data["contents"]["twoColumnSearchResultsRenderer"]
            ["primaryContents"]["sectionListRenderer"]["contents"]
        )
        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                vr = item.get("videoRenderer")
                if vr:
                    return vr["videoId"]
    except (KeyError, IndexError):
        logger.warning("Could not parse innertube results for: %s", query)

    return None


async def create_playlist(
    access_token: str, title: str, description: str = ""
) -> str:
    """Create a new YouTube playlist. Returns the playlist ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{YOUTUBE_API_BASE}/playlists",
            params={"part": "snippet,status"},
            json={
                "snippet": {
                    "title": title,
                    "description": description,
                },
                "status": {"privacyStatus": "private"},
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def find_playlist_by_title(access_token: str, title: str) -> str | None:
    """Search the user's own playlists for one matching *title*. Returns playlist ID or None.

    Uses playlists.list (1 quota unit per page).
    """
    url: str | None = f"{YOUTUBE_API_BASE}/playlists"
    params: dict = {"part": "snippet", "mine": "true", "maxResults": "50"}
    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (401, 403):
                return None
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                if item["snippet"]["title"] == title:
                    return item["id"]
            next_token = data.get("nextPageToken")
            if next_token:
                params["pageToken"] = next_token
            else:
                url = None
    return None


async def get_playlist_video_ids(access_token: str, playlist_id: str) -> set[str]:
    """Return all video IDs already in a YouTube playlist.

    Uses playlistItems.list (1 quota unit per page).
    """
    video_ids: set[str] = set()
    url: str | None = f"{YOUTUBE_API_BASE}/playlistItems"
    params: dict = {
        "part": "contentDetails",
        "playlistId": playlist_id,
        "maxResults": "50",
    }
    async with httpx.AsyncClient() as client:
        while url:
            resp = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (401, 403):
                break
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    video_ids.add(vid)
            next_token = data.get("nextPageToken")
            if next_token:
                params["pageToken"] = next_token
            else:
                url = None
    return video_ids


async def add_video_to_playlist(
    access_token: str, playlist_id: str, video_id: str
) -> None:
    """Add a video to a YouTube playlist."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{YOUTUBE_API_BASE}/playlistItems",
            params={"part": "snippet"},
            json={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
