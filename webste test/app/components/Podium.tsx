"use client";

import type { ClientPlayer } from "@/lib/types";
import { ScoreRows } from "./bits";

export function Podium({
  players,
  title,
  isHost,
  onBackToLobby,
}: {
  players: ClientPlayer[];
  title: string;
  isHost: boolean;
  onBackToLobby: () => void;
}) {
  const sorted = [...players].sort((a, b) => b.score - a.score);
  const [first, second, third] = sorted;
  const slots = [
    second ? { player: second, cls: "podium-2", place: "2" } : null,
    first ? { player: first, cls: "podium-1", place: "1" } : null,
    third ? { player: third, cls: "podium-3", place: "3" } : null,
  ].filter((s) => s !== null);

  return (
    <section className="card pop" data-testid="podium">
      <h2 style={{ textAlign: "center", fontSize: 30 }}>{title}</h2>
      <div className="podium">
        {slots.map((slot, i) => (
          <div key={slot.player.id} className={`podium-slot ${slot.cls} pop pop-${i + 1}`}>
            <span className="podium-emoji">{slot.player.emoji}</span>
            <span className="podium-name">{slot.player.name}</span>
            <div className="podium-block">{slot.place}</div>
          </div>
        ))}
      </div>
      <ScoreRows players={players} />
      {isHost ? (
        <div className="center-actions">
          <button type="button" data-testid="back-to-lobby" className="btn" onClick={onBackToLobby}>
            Back to lobby
          </button>
        </div>
      ) : (
        <p className="waiting-note">Waiting for the host to head back to the lobby…</p>
      )}
    </section>
  );
}
