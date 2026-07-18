import type { Room, RoomCode } from "./types";

// Unambiguous alphabet: no I/O/0/1 lookalikes.
const CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ";
const ROOM_TTL_MS = 24 * 60 * 60 * 1000;

// Hang the store off globalThis so Next dev-mode module reloads
// don't silently give route handlers a fresh empty Map.
declare global {
  var __confettiRooms: Map<RoomCode, Room> | undefined;
}

const rooms: Map<RoomCode, Room> = (globalThis.__confettiRooms ??= new Map());

function randomCode(): RoomCode {
  let code = "";
  for (let i = 0; i < 4; i++) {
    code += CODE_ALPHABET[Math.floor(Math.random() * CODE_ALPHABET.length)];
  }
  return code as RoomCode;
}

export function normalizeCode(raw: string): RoomCode {
  return raw.trim().toUpperCase() as RoomCode;
}

export function insertRoom(build: (code: RoomCode) => Room): Room {
  const now = Date.now();
  for (const [code, room] of rooms) {
    if (now - room.createdAt > ROOM_TTL_MS) rooms.delete(code);
  }
  let code = randomCode();
  while (rooms.has(code)) code = randomCode();
  const room = build(code);
  rooms.set(code, room);
  return room;
}

export function getRoom(code: RoomCode): Room | undefined {
  return rooms.get(code);
}

export function mutateRoom(room: Room, mutate: (room: Room) => void): Room {
  mutate(room);
  room.version += 1;
  return room;
}
