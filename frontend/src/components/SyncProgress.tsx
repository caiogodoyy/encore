"use client";

import { Loader2, CheckCircle2, XCircle, ExternalLink } from "lucide-react";

interface SyncProgressProps {
  status: string | null;
  progress: number;
  total: number;
  added: number;
  skipped: number;
  error: string | null;
  youtubePlaylistId: string | null;
}

export default function SyncProgress({
  status,
  progress,
  total,
  added,
  skipped,
  error,
  youtubePlaylistId,
}: SyncProgressProps) {
  if (!status) return null;

  const percentage = total > 0 ? Math.round((progress / total) * 100) : 0;
  const isRunning = ["reading_playlist", "creating_playlist", "adding_tracks"].includes(status);
  const isCompleted = status === "completed";
  const isError = status === "error";

  const statusLabels: Record<string, string> = {
    reading_playlist: "Lendo playlist do Spotify…",
    creating_playlist: "Criando playlist no YouTube…",
    adding_tracks: "Adicionando faixas…",
    completed: "Sincronização concluída!",
    error: "Erro na sincronização",
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 rounded-2xl bg-[var(--card)] border border-[var(--border)]">
      <div className="flex items-center gap-3 mb-4">
        {isRunning && <Loader2 className="w-5 h-5 text-[var(--accent)] animate-spin" />}
        {isCompleted && <CheckCircle2 className="w-5 h-5 text-green-400" />}
        {isError && <XCircle className="w-5 h-5 text-red-400" />}
        <span className="font-medium">{statusLabels[status] || status}</span>
      </div>

      {total > 0 && (
        <>
          <div className="w-full h-2 rounded-full bg-[var(--border)] mb-2 overflow-hidden">
            <div
              className="h-full rounded-full bg-[var(--accent)] transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-[var(--muted)]">
            <span>
              {progress}/{total} faixas
            </span>
            <span>{percentage}%</span>
          </div>
        </>
      )}

      {isCompleted && (
        <div className="mt-4 space-y-2">
          <p className="text-sm text-[var(--muted)]">
            {added} adicionada{added !== 1 ? "s" : ""} · {skipped} não encontrada
            {skipped !== 1 ? "s" : ""}
          </p>
          {youtubePlaylistId && (
            <a
              href={`https://www.youtube.com/playlist?list=${youtubePlaylistId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#ff0000] text-white text-sm font-medium hover:bg-[#ff2020] transition-colors"
            >
              Abrir no YouTube
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      )}

      {isError && error && (
        <p className="mt-3 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
}
