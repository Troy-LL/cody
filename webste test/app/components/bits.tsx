"use client";

import type { ClientPlayer, PlayerId } from "@/lib/types";

export function PlayerChips({
  players,
  doneIds,
  showScores,
}: {
  players: ClientPlayer[];
  doneIds?: PlayerId[];
  showScores?: boolean;
}) {
  return (
    <div className="player-grid">
      {players.map((p) => (
        <span
          key={p.id}
          data-testid={`player-chip-${p.name}`}
          className={`player-chip${doneIds?.includes(p.id) ? " done" : ""}`}
        >
          <span className="chip-emoji">{p.emoji}</span>
          <span>{p.name}</span>
          {p.isHost && <span className="chip-host">★ host</span>}
          {showScores && <span className="chip-score">{p.score}</span>}
          {doneIds?.includes(p.id) && <span aria-label="ready">✓</span>}
        </span>
      ))}
    </div>
  );
}

export function ScoreRows({
  players,
  gained,
}: {
  players: ClientPlayer[];
  gained?: Record<PlayerId, number>;
}) {
  const sorted = [...players].sort((a, b) => b.score - a.score);
  return (
    <div className="score-rows">
      {sorted.map((p) => (
        <div key={p.id} className="score-row" data-testid={`score-row-${p.name}`}>
          <span className="chip-emoji">{p.emoji}</span>
          <span className="row-name">{p.name}</span>
          {gained && (gained[p.id] ?? 0) > 0 && <span className="row-delta">+{gained[p.id]}</span>}
          <span className="row-points">{p.score}</span>
        </div>
      ))}
    </div>
  );
}
