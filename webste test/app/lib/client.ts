import type { ClientRoom, RoomAction } from "./types";

export interface Identity {
  playerId: string;
  name: string;
}

const identityKey = (code: string) => `confetti:${code.toUpperCase()}`;

export function loadIdentity(code: string): Identity | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(identityKey(code));
  if (!raw) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed === "object" &&
      parsed !== null &&
      typeof (parsed as Identity).playerId === "string" &&
      typeof (parsed as Identity).name === "string"
    ) {
      return parsed as Identity;
    }
  } catch {
    // fall through to null
  }
  return null;
}

export function saveIdentity(code: string, identity: Identity): void {
  sessionStorage.setItem(identityKey(code), JSON.stringify(identity));
}

async function request(path: string, init?: RequestInit): Promise<ClientRoom> {
  const res = await fetch(path, init);
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) {
    const message =
      typeof body === "object" && body !== null && typeof (body as { error?: unknown }).error === "string"
        ? (body as { error: string }).error
        : `Request failed (${res.status}).`;
    throw new Error(message);
  }
  return (body as { room: ClientRoom }).room;
}

const post = (path: string, payload: unknown): Promise<ClientRoom> =>
  request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const api = {
  createRoom: (name: string, emoji: string) => post("/api/rooms", { name, emoji }),
  joinRoom: (code: string, name: string, emoji: string) =>
    post(`/api/rooms/${encodeURIComponent(code)}/join`, { name, emoji }),
  getRoom: (code: string, playerId: string) =>
    request(`/api/rooms/${encodeURIComponent(code)}?player=${encodeURIComponent(playerId)}`),
  act: (code: string, playerId: string, action: RoomAction) =>
    post(`/api/rooms/${encodeURIComponent(code)}/action`, { playerId, action }),
};
