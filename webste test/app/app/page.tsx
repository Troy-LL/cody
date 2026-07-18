"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveIdentity } from "@/lib/client";
import { EmojiPicker, PARTY_EMOJIS } from "@/components/EmojiPicker";

type Panel = "host" | "join";

export default function LandingPage() {
  const router = useRouter();
  const [panel, setPanel] = useState<Panel>("host");
  const [name, setName] = useState("");
  const [emoji, setEmoji] = useState(PARTY_EMOJIS[0]!);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const room =
        panel === "host" ? await api.createRoom(name, emoji) : await api.joinRoom(code, name, emoji);
      saveIdentity(room.code, { playerId: room.you, name });
      router.push(`/room/${room.code}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setBusy(false);
    }
  };

  return (
    <main className="shell">
      <h1 className="title-xl pop">
        <span className="hi-coral">Confetti</span> <span className="hi-aqua">Club</span>
      </h1>
      <p className="subtitle pop pop-1">
        One screen each, one room code, three ridiculous games. Gather your people.
      </p>

      <div className="center-actions pop pop-2">
        <button
          type="button"
          data-testid="tab-host"
          className={panel === "host" ? "btn" : "btn btn-ghost"}
          onClick={() => setPanel("host")}
        >
          Host a party
        </button>
        <button
          type="button"
          data-testid="tab-join"
          className={panel === "join" ? "btn btn-aqua" : "btn btn-ghost"}
          onClick={() => setPanel("join")}
        >
          Join with code
        </button>
      </div>

      <form
        className="card pop pop-3"
        style={{ marginTop: 22 }}
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        {panel === "join" && (
          <div className="field">
            <label className="label" htmlFor="code">
              Room code
            </label>
            <input
              id="code"
              data-testid="join-code"
              className="input input-code"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase().slice(0, 4))}
              placeholder="ABCD"
              autoComplete="off"
              maxLength={4}
            />
          </div>
        )}

        <div className="field">
          <label className="label" htmlFor="name">
            Your name
          </label>
          <input
            id="name"
            data-testid="player-name"
            className="input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Sam"
            autoComplete="off"
            maxLength={20}
          />
        </div>

        <div className="field">
          <span className="label">Your emoji</span>
          <EmojiPicker idPrefix="landing" value={emoji} onChange={setEmoji} />
        </div>

        <div className="center-actions" style={{ marginTop: 10 }}>
          <button
            type="submit"
            data-testid="submit-enter"
            className={panel === "host" ? "btn" : "btn btn-aqua"}
            disabled={busy || name.trim().length === 0 || (panel === "join" && code.length !== 4)}
          >
            {panel === "host" ? "Open the room" : "Jump in"}
          </button>
        </div>

        {error && (
          <p className="error-note" data-testid="landing-error">
            {error}
          </p>
        )}
      </form>
    </main>
  );
}
