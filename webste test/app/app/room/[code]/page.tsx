"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { api, loadIdentity, saveIdentity } from "@/lib/client";
import { useRoom } from "@/hooks/useRoom";
import { EmojiPicker, PARTY_EMOJIS } from "@/components/EmojiPicker";
import { Lobby } from "@/components/Lobby";
import { Trivia } from "@/components/Trivia";
import { Wyr } from "@/components/Wyr";
import { Imposter } from "@/components/Imposter";

function JoinInPlace({ code, onJoined }: { code: string; onJoined: (playerId: string) => void }) {
  const [name, setName] = useState("");
  const [emoji, setEmoji] = useState(PARTY_EMOJIS[1]!);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const room = await api.joinRoom(code, name, emoji);
      saveIdentity(room.code, { playerId: room.you, name });
      onJoined(room.you);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not join.");
      setBusy(false);
    }
  };

  return (
    <form
      className="card pop"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <h2 style={{ fontSize: 26, marginBottom: 14 }}>Join room {code}</h2>
      <div className="field">
        <label className="label" htmlFor="join-name">
          Your name
        </label>
        <input
          id="join-name"
          data-testid="player-name"
          className="input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={20}
          autoComplete="off"
        />
      </div>
      <div className="field">
        <span className="label">Your emoji</span>
        <EmojiPicker idPrefix="room" value={emoji} onChange={setEmoji} />
      </div>
      <div className="center-actions" style={{ marginTop: 8 }}>
        <button
          type="submit"
          data-testid="submit-enter"
          className="btn btn-aqua"
          disabled={busy || name.trim().length === 0}
        >
          Jump in
        </button>
      </div>
      {error && (
        <p className="error-note" data-testid="join-error">
          {error}
        </p>
      )}
    </form>
  );
}

export default function RoomPage() {
  const params = useParams<{ code: string }>();
  const router = useRouter();
  const code = (params.code ?? "").toUpperCase();
  const [playerId, setPlayerId] = useState<string | null>(null);
  const [checkedStorage, setCheckedStorage] = useState(false);

  useEffect(() => {
    setPlayerId(loadIdentity(code)?.playerId ?? null);
    setCheckedStorage(true);
  }, [code]);

  const { room, error, fatal, act } = useRoom(code, playerId);

  useEffect(() => {
    if (fatal) router.push("/");
  }, [fatal, router]);

  return (
    <main className="shell">
      <div className="meta-row" style={{ marginBottom: 20 }}>
        <Link href="/" className="brand">
          Confetti<span className="dot"> Club</span>
        </Link>
        <span data-testid="room-code-header">Room {code}</span>
      </div>

      {!checkedStorage ? null : !playerId ? (
        <JoinInPlace code={code} onJoined={setPlayerId} />
      ) : !room ? (
        <p className="waiting-note" data-testid="loading">
          Setting the table…
        </p>
      ) : (
        <>
          {room.view.game === "lobby" && (
            <Lobby room={room} isHost={room.hostId === room.you} onStart={(game) => void act({ type: "startGame", game })} />
          )}
          {room.view.game === "trivia" && (
            <Trivia room={room} view={room.view} isHost={room.hostId === room.you} act={(a) => void act(a)} />
          )}
          {room.view.game === "wyr" && (
            <Wyr room={room} view={room.view} isHost={room.hostId === room.you} act={(a) => void act(a)} />
          )}
          {room.view.game === "imposter" && (
            <Imposter room={room} view={room.view} isHost={room.hostId === room.you} act={(a) => void act(a)} />
          )}
          {error && (
            <p className="error-note" data-testid="room-error">
              {error}
            </p>
          )}
        </>
      )}
    </main>
  );
}
