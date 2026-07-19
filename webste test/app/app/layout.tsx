import type { Metadata, Viewport } from "next";
import "@fontsource/lilita-one/400.css";
import "@fontsource/outfit/400.css";
import "@fontsource/outfit/600.css";
import "@fontsource/outfit/700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Confetti Club — party games with friends",
  description: "Host a room, share a 4-letter code, and play trivia, would-you-rather, and imposter word with friends.",
};

export const viewport: Viewport = {
  themeColor: "#0b0e1d",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="stage">
          <div className="orb orb-coral" />
          <div className="orb orb-aqua" />
          <div className="orb orb-sun" />
          {children}
        </div>
      </body>
    </html>
  );
}
