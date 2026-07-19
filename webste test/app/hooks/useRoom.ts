"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/client";
import type { ClientRoom, RoomAction } from "@/lib/types";

const POLL_MS = 1000;

export interface RoomHook {
  room: ClientRoom | null;
  error: string | null;
  fatal: boolean;
  act: (action: RoomAction) => Promise<void>;
}

export function useRoom(code: string, playerId: string | null): RoomHook {
  const [room, setRoom] = useState<ClientRoom | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fatal, setFatal] = useState(false);
  const versionRef = useRef(0);

  const accept = useCallback((next: ClientRoom) => {
    if (next.version >= versionRef.current) {
      versionRef.current = next.version;
      setRoom(next);
    }
  }, []);

  useEffect(() => {
    if (!playerId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const tick = async () => {
      try {
        const next = await api.getRoom(code, playerId);
        if (!cancelled) {
          accept(next);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          const message = e instanceof Error ? e.message : "Connection lost.";
          setError(message);
          if (message.includes("not found") || message.includes("not in this room")) setFatal(true);
        }
      }
      if (!cancelled) timer = setTimeout(tick, POLL_MS);
    };

    void tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [code, playerId, accept]);

  const act = useCallback(
    async (action: RoomAction) => {
      if (!playerId) return;
      try {
        accept(await api.act(code, playerId, action));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Action failed.");
      }
    },
    [code, playerId, accept],
  );

  return { room, error, fatal, act };
}
