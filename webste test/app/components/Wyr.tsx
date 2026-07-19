"use client";

import type { ClientRoom, ClientWyrView, RoomAction } from "@/lib/types";
import { PlayerChips, ScoreRows } from "./bits";
import { Podium } from "./Podium";

export function Wyr({
  room,
  view,
  isHost,
  act,
}: {
  room: ClientRoom;
  view: ClientWyrView;
  isHost: boolean;
  act: (action: RoomAction) => void;
}) {
  if (view.kind === "final") {
    return (
      <Podium
        players={room.players}
        title="Would You Rather — final scores"
        isHost={isHost}
        onBackToLobby={() => act({ type: "backToLobby" })}
      />
    );
  }

  const header = (
    <div className="meta-row">
      <span>🤔 Would You Rather</span>
      <span data-testid="wyr-progress">
        Round {view.index + 1} / {view.total}
      </span>
    </div>
  );

  if (view.kind === "vote") {
    return (
      <section className="card pop" data-testid="wyr-vote-screen">
        {header}
        <h2 className="question-title">Would you rather…</h2>
        <div className="wyr-cards">
          <button
            type="button"
            data-testid="vote-a"
            className={`wyr-card${view.yourVote === "a" ? " picked" : ""}`}
            disabled={view.yourVote !== null}
            onClick={() => act({ type: "wyr/vote", side: "a" })}
          >
            {view.prompt.a}
          </button>
          <button
            type="button"
            data-testid="vote-b"
            className={`wyr-card${view.yourVote === "b" ? " picked" : ""}`}
            disabled={view.yourVote !== null}
            onClick={() => act({ type: "wyr/vote", side: "b" })}
          >
            {view.prompt.b}
          </button>
        </div>
        <p className="waiting-note">
          {view.yourVote === null ? "Majority side scores." : "Vote in. Waiting for the others…"}
        </p>
        <div style={{ marginTop: 14 }}>
          <PlayerChips players={room.players} doneIds={view.votedIds} />
        </div>
        {isHost && (
          <div className="center-actions">
            <button
              type="button"
              data-testid="advance"
              className="btn btn-ghost"
              onClick={() => act({ type: "wyr/advance" })}
            >
              Reveal now
            </button>
          </div>
        )}
      </section>
    );
  }

  const total = view.countA + view.countB;
  const pctA = total === 0 ? 50 : Math.round((view.countA / total) * 100);
  const pctB = 100 - pctA;

  return (
    <section className="card pop" data-testid="wyr-reveal-screen">
      {header}
      <h2 className="question-title">The room says…</h2>
      <div className="split-bar" data-testid="wyr-split">
        <div className="split-a" style={{ flexGrow: Math.max(view.countA, 0.001) }}>
          {pctA}%
        </div>
        <div className="split-b" style={{ flexGrow: Math.max(view.countB, 0.001) }}>
          {pctB}%
        </div>
      </div>
      <div className="wyr-cards" style={{ marginTop: 12 }}>
        <div className="wyr-card" style={{ cursor: "default" }}>
          {view.prompt.a} · {view.countA} {view.countA === 1 ? "vote" : "votes"}
        </div>
        <div className="wyr-card" style={{ cursor: "default" }}>
          {view.prompt.b} · {view.countB} {view.countB === 1 ? "vote" : "votes"}
        </div>
      </div>
      <div style={{ marginTop: 18 }}>
        <span className="label">Scores</span>
        <ScoreRows players={room.players} gained={view.gained} />
      </div>
      {isHost ? (
        <div className="center-actions">
          <button
            type="button"
            data-testid="advance"
            className="btn"
            onClick={() => act({ type: "wyr/advance" })}
          >
            {view.index + 1 < view.total ? "Next round" : "Final scores"}
          </button>
        </div>
      ) : (
        <p className="waiting-note">Waiting for the host…</p>
      )}
    </section>
  );
}
