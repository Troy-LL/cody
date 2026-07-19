"use client";

import type { ClientRoom, ClientTriviaView, RoomAction } from "@/lib/types";
import { PlayerChips, ScoreRows } from "./bits";
import { Podium } from "./Podium";

export function Trivia({
  room,
  view,
  isHost,
  act,
}: {
  room: ClientRoom;
  view: ClientTriviaView;
  isHost: boolean;
  act: (action: RoomAction) => void;
}) {
  if (view.kind === "final") {
    return (
      <Podium
        players={room.players}
        title="Trivia Blitz — final scores"
        isHost={isHost}
        onBackToLobby={() => act({ type: "backToLobby" })}
      />
    );
  }

  const header = (
    <div className="meta-row">
      <span>⚡ Trivia Blitz</span>
      <span data-testid="trivia-progress">
        Question {view.index + 1} / {view.total}
      </span>
    </div>
  );

  if (view.kind === "question") {
    const yourChoice = view.yourChoice;
    return (
      <section className="card pop" data-testid="trivia-question-screen">
        {header}
        <h2 className="question-title" data-testid="trivia-question">
          {view.prompt}
        </h2>
        <div className="answers">
          {view.choices.map((choice, i) => (
            <button
              key={choice}
              type="button"
              data-testid={`answer-${i}`}
              className={`answer-btn${yourChoice === i ? " picked" : ""}`}
              disabled={yourChoice !== null}
              onClick={() => act({ type: "trivia/answer", choice: i })}
            >
              {choice}
            </button>
          ))}
        </div>
        <p className="waiting-note">
          {yourChoice === null ? "Lock in fast for a speed bonus." : "Answer locked. Waiting for the others…"}
        </p>
        <div style={{ marginTop: 14 }}>
          <PlayerChips players={room.players} doneIds={view.answeredIds} />
        </div>
        {isHost && (
          <div className="center-actions">
            <button
              type="button"
              data-testid="advance"
              className="btn btn-ghost"
              onClick={() => act({ type: "trivia/advance" })}
            >
              Reveal now
            </button>
          </div>
        )}
      </section>
    );
  }

  return (
    <section className="card pop" data-testid="trivia-reveal-screen">
      {header}
      <h2 className="question-title">{view.prompt}</h2>
      <div className="answers">
        {view.choices.map((choice, i) => {
          const count = view.counts[i] ?? 0;
          return (
            <button
              key={choice}
              type="button"
              className={`answer-btn${i === view.correct ? " correct" : ""}`}
              disabled
              data-testid={i === view.correct ? "correct-answer" : undefined}
            >
              {choice}
              {count > 0 ? ` · ${count} ${count === 1 ? "vote" : "votes"}` : ""}
              {i === view.correct ? " ✓" : ""}
            </button>
          );
        })}
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
            onClick={() => act({ type: "trivia/advance" })}
          >
            {view.index + 1 < view.total ? "Next question" : "Final scores"}
          </button>
        </div>
      ) : (
        <p className="waiting-note">Waiting for the host…</p>
      )}
    </section>
  );
}
