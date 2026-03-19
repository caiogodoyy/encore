import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Encore!",
  description:
    "Transforme suas playlists de estúdio do Spotify em experiências ao vivo no YouTube.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
