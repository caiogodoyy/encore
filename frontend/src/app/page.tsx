"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ConnectButton from "@/components/ConnectButton";
import PlaylistCard from "@/components/PlaylistCard";
import SyncProgress from "@/components/SyncProgress";
import { getAuthStatus, getPlaylists, getSyncStatus, startSync } from "@/lib/api";

interface Playlist {
  id: string;
  name: string;
  description: string;
  track_count: number;
  image: string | null;
}

interface SyncState {
  status: string | null;
  progress: number;
  total: number;
  added: number;
  skipped: number;
  error: string | null;
  youtube_playlist_id: string | null;
}

export default function Home() {
  const [spotifyConnected, setSpotifyConnected] = useState(false);
  const [youtubeConnected, setYoutubeConnected] = useState(false);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>({
    status: null,
    progress: 0,
    total: 0,
    added: 0,
    skipped: 0,
    error: null,
    youtube_playlist_id: null,
  });

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Check auth status on mount
  useEffect(() => {
    getAuthStatus().then(({ spotify, youtube }) => {
      setSpotifyConnected(spotify);
      setYoutubeConnected(youtube);
    });
  }, []);

  // Load playlists when Spotify is connected
  useEffect(() => {
    if (spotifyConnected) {
      getPlaylists().then(setPlaylists);
    }
  }, [spotifyConnected]);

  // Poll sync status while syncing
  useEffect(() => {
    if (!syncing) return;

    pollRef.current = setInterval(async () => {
      const s = await getSyncStatus();
      setSyncState(s);
      if (s.status === "completed" || s.status === "error") {
        setSyncing(false);
      }
    }, 1500);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [syncing]);

  const handleSync = useCallback(
    async (playlistId: string) => {
      if (syncing) return;
      setSyncing(true);
      setSyncState({
        status: "reading_playlist",
        progress: 0,
        total: 0,
        added: 0,
        skipped: 0,
        error: null,
        youtube_playlist_id: null,
      });
      await startSync(playlistId);
    },
    [syncing],
  );

  const bothConnected = spotifyConnected && youtubeConnected;

  return (
    <main className="flex flex-col items-center px-4 py-16 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold tracking-tight mb-3">
          Encore<span className="text-[var(--accent)]">!</span>
        </h1>
        <p className="text-[var(--muted)] text-lg max-w-md">
          Transforme suas playlists de estúdio do Spotify em experiências ao
          vivo no YouTube.
        </p>
      </div>

      {/* Connect */}
      <section className="w-full max-w-sm space-y-3 mb-12">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-[var(--muted)] mb-4">
          1 · Conectar plataformas
        </h2>
        <ConnectButton platform="spotify" connected={spotifyConnected} />
        <ConnectButton platform="youtube" connected={youtubeConnected} />
      </section>

      {/* Playlists */}
      {bothConnected && (
        <section className="w-full mb-12">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[var(--muted)] mb-4">
            2 · Escolher playlist
          </h2>

          {playlists.length === 0 ? (
            <p className="text-center text-[var(--muted)]">
              Nenhuma playlist encontrada.
            </p>
          ) : (
            <div className="grid gap-2">
              {playlists.map((pl) => (
                <PlaylistCard
                  key={pl.id}
                  playlist={pl}
                  onSelect={handleSync}
                  disabled={syncing}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Sync Progress */}
      {syncState.status && (
        <section className="w-full">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-[var(--muted)] mb-4">
            3 · Sincronização
          </h2>
          <SyncProgress
            status={syncState.status}
            progress={syncState.progress}
            total={syncState.total}
            added={syncState.added}
            skipped={syncState.skipped}
            error={syncState.error}
            youtubePlaylistId={syncState.youtube_playlist_id}
          />
        </section>
      )}

      {/* Footer */}
      <footer className="mt-20 text-center text-xs text-[var(--muted)]">
        Encore! — Feito com ♫
      </footer>
    </main>
  );
}
