const API_BASE = "";

export async function getAuthStatus(): Promise<{
  spotify: boolean;
  youtube: boolean;
}> {
  const res = await fetch(`${API_BASE}/api/auth/status`, { credentials: "include" });
  if (!res.ok) return { spotify: false, youtube: false };
  return res.json();
}

export async function getPlaylists(): Promise<
  {
    id: string;
    name: string;
    description: string;
    track_count: number;
    image: string | null;
  }[]
> {
  const res = await fetch(`${API_BASE}/api/sync/playlists`, {
    credentials: "include",
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.playlists;
}

export async function startSync(playlistId: string) {
  const res = await fetch(`${API_BASE}/api/sync/start?playlist_id=${encodeURIComponent(playlistId)}`, {
    method: "POST",
    credentials: "include",
  });
  return res.json();
}

export async function getSyncStatus(): Promise<{
  status: string | null;
  progress: number;
  total: number;
  added: number;
  skipped: number;
  error: string | null;
  youtube_playlist_id: string | null;
}> {
  const res = await fetch(`${API_BASE}/api/sync/status`, {
    credentials: "include",
  });
  return res.json();
}
