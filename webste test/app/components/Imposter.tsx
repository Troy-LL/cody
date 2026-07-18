"use client";

import { useState } from "react";
import type { ClientImposterView, ClientRoom, RoomAction } from "@/lib/types";
import { PlayerChips, ScoreRows } from "./bits";
import { Podium } from "./Podium";

function RoleCard({ view }: { view: Extract<ClientImposterView, { kind: "discuss" | "vote" }> }) {
  const [peeking, setPeeking] = useState(false);
  const isImposter = view.you.role === "imposter";
  return (
    <button
      type="button"
      data-testid="role-card"
      className={`role-card${isImposter ? " imposter-card" : ""}`}
      onClick={() => setPeeking((p) => !p)}
    >
      {peeking ? (
        view.you.role === "crew" ? (
          <>
            <span className="label">The secret word is</span>
            <div className="secret-word" data-testid="secret-word">
              {view.you.word}
            </div>
            <p className="waiting-note">Category: {view.you.category}. Tap to hide.</p>
          </>
        ) : (
          <>
            <span className="label">Shhh…</span>
            <div className="secret-word" style={{ color: "var(--coral)" }} data-testid="imposter-badge">
              You are the imposter
            </div>
            <p className="waiting-note">
              You only know the category: {view.you.category}. Blend in. Tap to hide.
            </p>
          </>
        )
      ) : (
        <>
          <span className="label">Your secret role</span>
          <div className="secret-word" style={{ color: "var(--text)" }}>
            Tap to peek 👀
          </div>
          <p className="waiting-note">Make sure nobody is looking over your shoulder.</p>
        </>
      )}
    </button>
  );
}

export function Imposter({
  room,
  view,
  isHost,
  act,
}: {
  room: ClientRoom;
  view: ClientImposterView;
  isHost: boolean;
  act: (action: RoomAction) => void;
}) {
  if (view.kind === "final") {
    return (
      <Podium
        players={room.players}
        title="Imposter Word — final scores"
        isHost={isHost}
        onBackToLobby={() => act({ type: "backToLobby" })}
      />
    );
  }

  const header = (
    <div className="meta-row">
      <span>🕵️ Imposter Word</span>
      <span>{view.kind === "discuss" ? "Discussion" : view.kind === "vote" ? "Voting" : "The reveal"}</span>
    </div>
  );

  if (view.kind === "discuss") {
    return (
      <section className="card pop" data-testid="imposter-discuss-screen">
        {header}
        <h2 className="question-title">Category: {view.you.category}</h2>
        <RoleCard view={view} />
        <p className="waiting-note">
          Out loud, take turns describing the secret word without saying it. The imposter fakes it.
          When you&apos;re suspicious, the host calls the vote.
        </p>
        {isHost ? (
          <div className="center-actions">
            <button
              type="button"
              data-testid="start-vote"
              className="btn"
              onClick={() => act({ type: "imposter/startVote" })}
            >
              Call the vote
            </button>
          </div>
        ) : (
          <p className="waiting-note">The host calls the vote when the room is ready.</p>
        )}
      </section>
    );
  }

  if (view.kind === "vote") {
    const yourVote = view.yourVote;
    return (
      <section className="card pop" data-testid="imposter-vote-screen">
        {header}
        <h2 className="question-title">Who is the imposter?</h2>
        <RoleCard view={view} />
        <div className="vote-grid" style={{ marginTop: 16 }}>
          {room.players
            .filter((p) => p.id !== room.you)
            .map((p) => (
              <button
                key={p.id}
                type="button"
                data-testid={`vote-player-${p.name}`}
                className={`vote-btn${yourVote === p.id ? " picked" : ""}`}
                disabled={yourVote !== null}
                onClick={() => act({ type: "imposter/vote", suspect: p.id })}
              >
                {p.emoji} {p.name}
              </button>
            ))}
        </div>
        <p className="waiting-note">
          {yourVote === null ? "Point your finger. Choose wisely." : "Vote cast. Waiting for the others…"}
        </p>
        <div style={{ marginTop: 14 }}>
          <PlayerChips players={room.players} doneIds={view.votedIds} />
        </div>
      </section>
    );
  }

  const imposterPlayer = room.players.find((p) => p.id === view.imposter);
  return (
    <section className="card pop" data-testid="imposter-reveal-screen">
      {header}
      <h2 className="question-title" data-testid="imposter-outcome">
        {view.caught ? "Caught!" : "The imposter escaped!"}
      </h2>
      <div className="role-card imposter-card" style={{ cursor: "default" }}>
        <span className="label">The imposter was</span>
        <div className="secret-word" style={{ color: "var(--coral)" }}>
          {imposterPlayer ? `${imposterPlayer.emoji} ${imposterPlayer.name}` : "???"}
        </div>
        <p className="waiting-note">
          The word was “{view.word}” ({view.category}).{" "}
          {view.caught ? "Correct accusers score 100." : "A clean escape scores the imposter 250."}
        </p>
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
            onClick={() => act({ type: "imposter/advance" })}
          >
            Final scores
          </button>
        </div>
      ) : (
        <p className="waiting-note">Waiting for the host…</p>
      )}
    </section>
  );
}
