"use client";

import type { ClientRoom, GameId } from "@/lib/types";
import { PlayerChips } from "./bits";

const GAMES: { id: GameId; emoji: string; name: string; blurb: string; min: number }[] = [
  { id: "trivia", emoji: "⚡", name: "Trivia Blitz", blurb: "Five quickfire questions. Speed pays.", min: 2 },
  { id: "wyr", emoji: "🤔", name: "Would You Rather", blurb: "Pick a side, see the split.", min: 2 },
  { id: "imposter", emoji: "🕵️", name: "Imposter Word", blurb: "One of you doesn't know the word.", min: 3 },
];

export function Lobby({
  room,
  isHost,
  onStart,
}: {
  room: ClientRoom;
  isHost: boolean;
  onStart: (game: GameId) => void;
}) {
  return (
    <section className="pop">
      <div className="card" style={{ textAlign: "center" }}>
        <span className="label">Share this code</span>
        <div className="code-badge" data-testid="room-code">
          {room.code}
        </div>
        <p className="waiting-note">
          Friends join at this site with the code. {room.players.length}{" "}
          {room.players.length === 1 ? "player" : "players"} in the room.
        </p>
      </div>

      <div className="card pop pop-1" style={{ marginTop: 16 }}>
        <span className="label">Who&apos;s here</span>
        <PlayerChips players={room.players} showScores />
      </div>

      <div className="card pop pop-2" style={{ marginTop: 16 }}>
        <span className="label">{isHost ? "Pick a game" : "Games"}</span>
        <div className="game-pick">
          {GAMES.map((game) => {
            const enough = room.players.length >= game.min;
            return (
              <button
                key={game.id}
                type="button"
                data-testid={`start-${game.id}`}
                className="game-tile"
                disabled={!isHost || !enough}
                title={enough ? undefined : `Needs ${game.min}+ players`}
                onClick={() => onStart(game.id)}
              >
                <span className="tile-emoji">{game.emoji}</span>
                <h3>{game.name}</h3>
                <p>{game.blurb}</p>
                {!enough && <p>Needs {game.min}+ players</p>}
              </button>
            );
          })}
        </div>
        {!isHost && <p className="waiting-note">The host picks what you play next.</p>}
      </div>
    </section>
  );
}
