"use client";

import { Check } from "lucide-react";

interface ConnectButtonProps {
  platform: "spotify" | "youtube";
  connected: boolean;
}

const config = {
  spotify: {
    label: "Spotify",
    color: "bg-[#1db954] hover:bg-[#1ed760]",
    connectedColor: "bg-[#1db954]/20 border-[#1db954]/40",
    loginUrl: "/api/auth/spotify/login",
    icon: (
      <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
      </svg>
    ),
  },
  youtube: {
    label: "YouTube",
    color: "bg-[#ff0000] hover:bg-[#ff2020]",
    connectedColor: "bg-[#ff0000]/20 border-[#ff0000]/40",
    loginUrl: "/api/auth/youtube/login",
    icon: (
      <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
  },
};

export default function ConnectButton({
  platform,
  connected,
}: ConnectButtonProps) {
  const c = config[platform];

  if (connected) {
    return (
      <div
        className={`flex items-center gap-3 px-6 py-3 rounded-xl border ${c.connectedColor} text-white/90 transition-all`}
      >
        {c.icon}
        <span className="font-medium">{c.label}</span>
        <Check className="w-5 h-5 text-green-400 ml-auto" />
      </div>
    );
  }

  return (
    <a
      href={c.loginUrl}
      className={`flex items-center gap-3 px-6 py-3 rounded-xl ${c.color} text-white font-medium transition-all shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]`}
    >
      {c.icon}
      <span>Conectar {c.label}</span>
    </a>
  );
}
