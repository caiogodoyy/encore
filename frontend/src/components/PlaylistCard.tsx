"use client";

import { Music } from "lucide-react";

interface Playlist {
  id: string;
  name: string;
  description: string;
  track_count: number;
  image: string | null;
}

interface PlaylistCardProps {
  playlist: Playlist;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

export default function PlaylistCard({
  playlist,
  onSelect,
  disabled,
}: PlaylistCardProps) {
  return (
    <button
      onClick={() => onSelect(playlist.id)}
      disabled={disabled}
      className="flex items-center gap-4 p-4 rounded-xl bg-[var(--card)] border border-[var(--border)] hover:border-[var(--accent)]/50 hover:bg-[var(--card)]/80 transition-all text-left w-full disabled:opacity-50 disabled:cursor-not-allowed group"
    >
      {playlist.image ? (
        <img
          src={playlist.image}
          alt={playlist.name}
          className="w-14 h-14 rounded-lg object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-14 h-14 rounded-lg bg-[var(--border)] flex items-center justify-center flex-shrink-0">
          <Music className="w-6 h-6 text-[var(--muted)]" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="font-medium truncate group-hover:text-[var(--accent)] transition-colors">
          {playlist.name}
        </p>
        <p className="text-sm text-[var(--muted)] truncate">
          {playlist.track_count} música{playlist.track_count !== 1 ? "s" : ""}
        </p>
      </div>
    </button>
  );
}
