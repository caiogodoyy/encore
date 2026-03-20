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

  const step = !spotifyConnected || !youtubeConnected ? 1 : syncing || syncState.status ? 3 : 2;

  return (
    <main className="min-h-screen bg-gradient-radial">
      <div className="flex flex-col items-center px-4 py-20 max-w-lg mx-auto">
        {/* Hero */}
        <div className="text-center mb-16 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent)]/10 border border-[var(--accent)]/20 text-[var(--accent)] text-xs font-medium mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
            Spotify → YouTube
          </div>
          <h1 className="text-6xl font-extrabold tracking-tight mb-4">
            Encore<span className="text-[var(--accent)]">!</span>
          </h1>
          <p className="text-[var(--muted)] text-base max-w-sm mx-auto leading-relaxed">
            Migre suas playlists do Spotify para o YouTube em poucos cliques.
          </p>
        </div>

        {/* Step 1: Connect */}
        <section className="w-full mb-10 animate-fade-in-up" style={{ animationDelay: "0.1s" }}>
          <div className="flex items-center gap-3 mb-4">
            <span className={`step-badge ${step > 1 ? "done" : "active"}`}>
              {step > 1 ? "✓" : "1"}
            </span>
            <h2 className="text-sm font-semibold text-white/80">
              Conectar plataformas
            </h2>
          </div>
          <div className="ml-[40px] space-y-2.5">
            <ConnectButton platform="spotify" connected={spotifyConnected} />
            <ConnectButton platform="youtube" connected={youtubeConnected} />
          </div>
        </section>

        {/* Step 2: Playlists */}
        {bothConnected && (
          <section className="w-full mb-10 animate-fade-in-up">
            <div className="flex items-center gap-3 mb-4">
              <span className={`step-badge ${step > 2 ? "done" : step === 2 ? "active" : ""}`}>
                {step > 2 ? "✓" : "2"}
              </span>
              <h2 className="text-sm font-semibold text-white/80">
                Escolher playlist
              </h2>
              {playlists.length > 0 && (
                <span className="ml-auto text-xs text-[var(--muted)] font-medium">
                  {playlists.length} playlist{playlists.length !== 1 ? "s" : ""}
                </span>
              )}
            </div>
            <div className="ml-[40px]">
              {playlists.length === 0 ? (
                <p className="text-sm text-[var(--muted)] py-8 text-center">
                  Nenhuma playlist encontrada.
                </p>
              ) : (
                <div className="grid gap-1.5 max-h-[420px] overflow-y-auto pr-1 stagger">
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
            </div>
          </section>
        )}

        {/* Step 3: Sync */}
        {syncState.status && (
          <section className="w-full animate-fade-in-up">
            <div className="flex items-center gap-3 mb-4">
              <span className={`step-badge ${syncState.status === "completed" ? "done" : "active"}`}>
                {syncState.status === "completed" ? "✓" : "3"}
              </span>
              <h2 className="text-sm font-semibold text-white/80">
                Sincronização
              </h2>
            </div>
            <div className="ml-[40px]">
              <SyncProgress
                status={syncState.status}
                progress={syncState.progress}
                total={syncState.total}
                added={syncState.added}
                skipped={syncState.skipped}
                error={syncState.error}
                youtubePlaylistId={syncState.youtube_playlist_id}
              />
            </div>
          </section>
        )}

        {/* Footer */}
        <footer className="mt-24 pb-8 text-center">
          <p className="text-xs text-[var(--muted)]/60">
            Encore! — Feito com ♫
          </p>
        </footer>
      </div>
    </main>
  );
}
