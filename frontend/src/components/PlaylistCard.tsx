"use client";

import { Music, ArrowRight } from "lucide-react";

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
      className="group relative flex items-center gap-4 p-3 pr-4 rounded-2xl bg-[var(--card)] border border-[var(--border)] hover:border-[var(--accent)]/40 hover:bg-[var(--card-hover)] transition-all duration-200 text-left w-full cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:border-[var(--border)]"
    >
      {/* Thumbnail */}
      {playlist.image ? (
        <img
          src={playlist.image}
          alt={playlist.name}
          className="w-14 h-14 rounded-xl object-cover flex-shrink-0 shadow-lg"
        />
      ) : (
        <div className="w-14 h-14 rounded-xl bg-[var(--border)] flex items-center justify-center flex-shrink-0">
          <Music className="w-6 h-6 text-[var(--muted)]" />
        </div>
      )}

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="font-semibold text-[15px] truncate group-hover:text-[var(--accent)] transition-colors duration-200">
          {playlist.name}
        </p>
        <p className="text-[13px] text-[var(--muted)] truncate mt-0.5">
          {playlist.track_count} música{playlist.track_count !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Arrow */}
      <ArrowRight className="w-4 h-4 text-[var(--muted)] opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all duration-200 flex-shrink-0" />
    </button>
  );
}
