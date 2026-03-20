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
    <div className="w-full max-w-md mx-auto p-6 rounded-2xl glass animate-fade-in-up">
      {/* Status header */}
      <div className="flex items-center gap-3 mb-5">
        {isRunning && (
          <div className="w-9 h-9 rounded-full bg-[var(--accent)]/10 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-[var(--accent)] animate-spin" />
          </div>
        )}
        {isCompleted && (
          <div className="w-9 h-9 rounded-full bg-green-500/10 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
          </div>
        )}
        {isError && (
          <div className="w-9 h-9 rounded-full bg-red-500/10 flex items-center justify-center">
            <XCircle className="w-5 h-5 text-red-400" />
          </div>
        )}
        <div>
          <span className="font-semibold text-[15px]">{statusLabels[status] || status}</span>
          {isRunning && total > 0 && (
            <p className="text-[13px] text-[var(--muted)] mt-0.5">
              {progress}/{total} faixas
            </p>
          )}
        </div>
        {total > 0 && (
          <span className="ml-auto text-sm font-mono font-semibold text-[var(--accent)]">
            {percentage}%
          </span>
        )}
      </div>

      {/* Progress bar */}
      {total > 0 && (
        <div className="w-full h-1.5 rounded-full bg-[var(--border)] overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${
              isError ? "bg-red-500" : "bg-[var(--accent)]"
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}

      {/* Completed state */}
      {isCompleted && (
        <div className="mt-5 pt-4 border-t border-[var(--border)] space-y-3">
          <div className="flex gap-4 text-[13px]">
            <span className="text-green-400">
              ✓ {added} adicionada{added !== 1 ? "s" : ""}
            </span>
            {skipped > 0 && (
              <span className="text-[var(--muted)]">
                · {skipped} não encontrada{skipped !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          {youtubePlaylistId && (
            <a
              href={`https://www.youtube.com/playlist?list=${youtubePlaylistId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#ff0000] text-white text-sm font-medium hover:bg-[#ff2020] transition-all duration-200 shadow-[0_4px_16px_rgba(255,0,0,0.25)] hover:shadow-[0_4px_24px_rgba(255,0,0,0.4)] hover:scale-[1.02] active:scale-[0.98]"
            >
              Abrir no YouTube
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      )}

      {/* Error state */}
      {isError && error && (
        <p className="mt-4 text-[13px] text-red-400/90 leading-relaxed">{error}</p>
      )}
    </div>
  );
}
