import { IMPOSTER_ENTRIES, sample, TRIVIA_QUESTIONS, WYR_PROMPTS } from "./content";
import { getRoom, insertRoom, mutateRoom, normalizeCode } from "./store";
import type {
  ClientPlayer,
  ClientRoom,
  ClientView,
  GameId,
  ImposterRole,
  Player,
  PlayerId,
  Room,
  RoomAction,
  RoomCode,
  TriviaState,
  WyrState,
  ImposterState,
} from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

const MAX_PLAYERS = 8;
const TRIVIA_ROUNDS = 5;
const WYR_ROUNDS = 4;
const MIN_PLAYERS: Record<GameId, number> = { trivia: 2, wyr: 2, imposter: 3 };

function newPlayerId(): PlayerId {
  return crypto.randomUUID() as PlayerId;
}

function makePlayer(name: string, emoji: string): Player {
  return { id: newPlayerId(), name, emoji, score: 0, joinedAt: Date.now() };
}

export function createRoom(name: string, emoji: string): { room: Room; playerId: PlayerId } {
  const host = makePlayer(name, emoji);
  const room = insertRoom((code) => ({
    code,
    hostId: host.id,
    createdAt: Date.now(),
    version: 1,
    players: [host],
    state: { game: "lobby" },
  }));
  return { room, playerId: host.id };
}

export function joinRoom(rawCode: string, name: string, emoji: string): { room: Room; playerId: PlayerId } {
  const room = requireRoom(rawCode);
  if (room.state.game !== "lobby") throw new ApiError(409, "Game already in progress. Wait for the lobby.");
  if (room.players.length >= MAX_PLAYERS) throw new ApiError(409, "Room is full.");
  if (room.players.some((p) => p.name.toLowerCase() === name.toLowerCase())) {
    throw new ApiError(409, "That name is taken in this room.");
  }
  const player = makePlayer(name, emoji);
  mutateRoom(room, (r) => r.players.push(player));
  return { room, playerId: player.id };
}

export function requireRoom(rawCode: string): Room {
  const room = getRoom(normalizeCode(rawCode));
  if (!room) throw new ApiError(404, "Room not found. Check the code.");
  return room;
}

function requirePlayer(room: Room, playerId: PlayerId): Player {
  const player = room.players.find((p) => p.id === playerId);
  if (!player) throw new ApiError(403, "You are not in this room.");
  return player;
}

function requireHost(room: Room, playerId: PlayerId): void {
  if (room.hostId !== playerId) throw new ApiError(403, "Only the host can do that.");
}

function zeroGains(room: Room): Record<PlayerId, number> {
  const gained: Record<PlayerId, number> = {};
  for (const p of room.players) gained[p.id] = 0;
  return gained;
}

// ---- Game starters ----

function startTrivia(): TriviaState {
  return {
    game: "trivia",
    questions: sample(TRIVIA_QUESTIONS, TRIVIA_ROUNDS),
    phase: { kind: "question", index: 0, askedAt: Date.now(), answers: {} },
  };
}

function startWyr(): WyrState {
  return {
    game: "wyr",
    prompts: sample(WYR_PROMPTS, WYR_ROUNDS),
    phase: { kind: "vote", index: 0, votes: {} },
  };
}

function startImposter(room: Room): ImposterState {
  const entry = sample(IMPOSTER_ENTRIES, 1)[0]!;
  const imposter = sample(room.players, 1)[0]!;
  return {
    game: "imposter",
    category: entry.category,
    word: entry.word,
    imposter: imposter.id,
    phase: { kind: "discuss", startedAt: Date.now() },
  };
}

// ---- Phase transitions ----

function revealTrivia(room: Room, state: TriviaState): void {
  if (state.phase.kind !== "question") return;
  const { index, askedAt, answers } = state.phase;
  const question = state.questions[index]!;
  const gained = zeroGains(room);
  for (const p of room.players) {
    const answer = answers[p.id];
    if (answer && answer.choice === question.answer) {
      const seconds = Math.max(0, (answer.at - askedAt) / 1000);
      const bonus = Math.max(0, Math.round(50 - seconds * 10));
      const points = 100 + bonus;
      gained[p.id] = points;
      p.score += points;
    }
  }
  state.phase = { kind: "reveal", index, answers, gained };
}

function revealWyr(room: Room, state: WyrState): void {
  if (state.phase.kind !== "vote") return;
  const { index, votes } = state.phase;
  const sides = Object.values(votes);
  const countA = sides.filter((s) => s === "a").length;
  const countB = sides.filter((s) => s === "b").length;
  const winning: ("a" | "b")[] = countA === countB ? ["a", "b"] : countA > countB ? ["a"] : ["b"];
  const gained = zeroGains(room);
  for (const p of room.players) {
    const vote = votes[p.id];
    if (vote && winning.includes(vote)) {
      gained[p.id] = 25;
      p.score += 25;
    }
  }
  state.phase = { kind: "reveal", index, votes, gained };
}

function revealImposter(room: Room, state: ImposterState): void {
  if (state.phase.kind !== "vote") return;
  const votes = state.phase.votes;
  const tally = new Map<PlayerId, number>();
  for (const suspect of Object.values(votes)) {
    tally.set(suspect, (tally.get(suspect) ?? 0) + 1);
  }
  let accused: PlayerId | null = null;
  let best = 0;
  let tied = false;
  for (const [suspect, count] of tally) {
    if (count > best) {
      best = count;
      accused = suspect;
      tied = false;
    } else if (count === best) {
      tied = true;
    }
  }
  if (tied) accused = null;
  const caught = accused === state.imposter;
  const gained = zeroGains(room);
  if (caught) {
    for (const p of room.players) {
      if (votes[p.id] === state.imposter && p.id !== state.imposter) {
        gained[p.id] = 100;
        p.score += 100;
      }
    }
  } else {
    const imposter = room.players.find((p) => p.id === state.imposter);
    if (imposter) {
      gained[imposter.id] = 250;
      imposter.score += 250;
    }
  }
  state.phase = { kind: "reveal", votes, accused, caught, gained };
}

// ---- The reducer ----

export function applyAction(rawCode: string, playerId: PlayerId, action: RoomAction): Room {
  const room = requireRoom(rawCode);
  requirePlayer(room, playerId);

  return mutateRoom(room, (r) => {
    switch (action.type) {
      case "startGame": {
        requireHost(r, playerId);
        if (r.state.game !== "lobby") throw new ApiError(409, "A game is already running.");
        if (r.players.length < MIN_PLAYERS[action.game]) {
          throw new ApiError(409, `Need at least ${MIN_PLAYERS[action.game]} players for that game.`);
        }
        r.state =
          action.game === "trivia" ? startTrivia() : action.game === "wyr" ? startWyr() : startImposter(r);
        return;
      }

      case "trivia/answer": {
        if (r.state.game !== "trivia" || r.state.phase.kind !== "question") {
          throw new ApiError(409, "Not accepting answers right now.");
        }
        const question = r.state.questions[r.state.phase.index]!;
        if (!Number.isInteger(action.choice) || action.choice < 0 || action.choice >= question.choices.length) {
          throw new ApiError(400, "Invalid choice.");
        }
        if (r.state.phase.answers[playerId]) throw new ApiError(409, "Already answered.");
        r.state.phase.answers[playerId] = { choice: action.choice, at: Date.now() };
        if (Object.keys(r.state.phase.answers).length >= r.players.length) {
          revealTrivia(r, r.state);
        }
        return;
      }

      case "trivia/advance": {
        requireHost(r, playerId);
        if (r.state.game !== "trivia") throw new ApiError(409, "Trivia is not running.");
        const state = r.state;
        if (state.phase.kind === "question") {
          revealTrivia(r, state);
        } else if (state.phase.kind === "reveal") {
          const next = state.phase.index + 1;
          state.phase =
            next < state.questions.length
              ? { kind: "question", index: next, askedAt: Date.now(), answers: {} }
              : { kind: "final" };
        }
        return;
      }

      case "wyr/vote": {
        if (r.state.game !== "wyr" || r.state.phase.kind !== "vote") {
          throw new ApiError(409, "Not accepting votes right now.");
        }
        if (r.state.phase.votes[playerId]) throw new ApiError(409, "Already voted.");
        r.state.phase.votes[playerId] = action.side;
        if (Object.keys(r.state.phase.votes).length >= r.players.length) {
          revealWyr(r, r.state);
        }
        return;
      }

      case "wyr/advance": {
        requireHost(r, playerId);
        if (r.state.game !== "wyr") throw new ApiError(409, "Would You Rather is not running.");
        const state = r.state;
        if (state.phase.kind === "vote") {
          revealWyr(r, state);
        } else if (state.phase.kind === "reveal") {
          const next = state.phase.index + 1;
          state.phase =
            next < state.prompts.length ? { kind: "vote", index: next, votes: {} } : { kind: "final" };
        }
        return;
      }

      case "imposter/startVote": {
        requireHost(r, playerId);
        if (r.state.game !== "imposter" || r.state.phase.kind !== "discuss") {
          throw new ApiError(409, "Not in the discussion phase.");
        }
        r.state.phase = { kind: "vote", votes: {} };
        return;
      }

      case "imposter/vote": {
        if (r.state.game !== "imposter" || r.state.phase.kind !== "vote") {
          throw new ApiError(409, "Not accepting votes right now.");
        }
        if (action.suspect === playerId) throw new ApiError(400, "You cannot vote for yourself.");
        requirePlayer(r, action.suspect);
        if (r.state.phase.votes[playerId]) throw new ApiError(409, "Already voted.");
        r.state.phase.votes[playerId] = action.suspect;
        if (Object.keys(r.state.phase.votes).length >= r.players.length) {
          revealImposter(r, r.state);
        }
        return;
      }

      case "imposter/advance": {
        requireHost(r, playerId);
        if (r.state.game !== "imposter") throw new ApiError(409, "Imposter is not running.");
        if (r.state.phase.kind === "reveal") r.state.phase = { kind: "final" };
        return;
      }

      case "backToLobby": {
        requireHost(r, playerId);
        r.state = { game: "lobby" };
        return;
      }

      default: {
        const exhausted: never = action;
        throw new ApiError(400, `Unknown action ${JSON.stringify(exhausted)}.`);
      }
    }
  });
}

// ---- Per-player redacted view ----

function imposterRole(state: ImposterState, playerId: PlayerId): ImposterRole {
  return state.imposter === playerId
    ? { role: "imposter", category: state.category }
    : { role: "crew", category: state.category, word: state.word };
}

function buildView(room: Room, playerId: PlayerId): ClientView {
  const state = room.state;
  switch (state.game) {
    case "lobby":
      return { game: "lobby" };

    case "trivia": {
      const total = state.questions.length;
      switch (state.phase.kind) {
        case "question": {
          const q = state.questions[state.phase.index]!;
          return {
            game: "trivia",
            kind: "question",
            index: state.phase.index,
            total,
            prompt: q.prompt,
            choices: q.choices,
            answeredIds: Object.keys(state.phase.answers) as PlayerId[],
            yourChoice: state.phase.answers[playerId]?.choice ?? null,
          };
        }
        case "reveal": {
          const q = state.questions[state.phase.index]!;
          const counts: [number, number, number, number] = [0, 0, 0, 0];
          for (const a of Object.values(state.phase.answers)) {
            if (a.choice >= 0 && a.choice < 4) counts[a.choice as 0 | 1 | 2 | 3] += 1;
          }
          return {
            game: "trivia",
            kind: "reveal",
            index: state.phase.index,
            total,
            prompt: q.prompt,
            choices: q.choices,
            correct: q.answer,
            counts,
            gained: state.phase.gained,
          };
        }
        case "final":
          return { game: "trivia", kind: "final" };
      }
      break;
    }

    case "wyr": {
      const total = state.prompts.length;
      switch (state.phase.kind) {
        case "vote":
          return {
            game: "wyr",
            kind: "vote",
            index: state.phase.index,
            total,
            prompt: state.prompts[state.phase.index]!,
            votedIds: Object.keys(state.phase.votes) as PlayerId[],
            yourVote: state.phase.votes[playerId] ?? null,
          };
        case "reveal": {
          const sides = Object.values(state.phase.votes);
          return {
            game: "wyr",
            kind: "reveal",
            index: state.phase.index,
            total,
            prompt: state.prompts[state.phase.index]!,
            countA: sides.filter((s) => s === "a").length,
            countB: sides.filter((s) => s === "b").length,
            gained: state.phase.gained,
          };
        }
        case "final":
          return { game: "wyr", kind: "final" };
      }
      break;
    }

    case "imposter": {
      switch (state.phase.kind) {
        case "discuss":
          return {
            game: "imposter",
            kind: "discuss",
            you: imposterRole(state, playerId),
            startedAt: state.phase.startedAt,
          };
        case "vote":
          return {
            game: "imposter",
            kind: "vote",
            you: imposterRole(state, playerId),
            votedIds: Object.keys(state.phase.votes) as PlayerId[],
            yourVote: state.phase.votes[playerId] ?? null,
          };
        case "reveal":
          return {
            game: "imposter",
            kind: "reveal",
            imposter: state.imposter,
            accused: state.phase.accused,
            caught: state.phase.caught,
            word: state.word,
            category: state.category,
            votes: state.phase.votes,
            gained: state.phase.gained,
          };
        case "final":
          return { game: "imposter", kind: "final" };
      }
    }
  }
}

export function toClientRoom(room: Room, playerId: PlayerId): ClientRoom {
  requirePlayer(room, playerId);
  const players: ClientPlayer[] = room.players.map((p) => ({
    id: p.id,
    name: p.name,
    emoji: p.emoji,
    score: p.score,
    isHost: p.id === room.hostId,
  }));
  return {
    code: room.code,
    you: playerId,
    hostId: room.hostId,
    version: room.version,
    players,
    view: buildView(room, playerId),
  };
}

// ---- Boundary parsing (untyped JSON in, typed action out) ----

export function parseName(value: unknown): string {
  if (typeof value !== "string") throw new ApiError(400, "Name is required.");
  const name = value.trim();
  if (name.length < 1 || name.length > 20) throw new ApiError(400, "Name must be 1-20 characters.");
  return name;
}

export function parseEmoji(value: unknown): string {
  if (typeof value !== "string" || value.length === 0 || value.length > 8) {
    throw new ApiError(400, "Pick an emoji.");
  }
  return value;
}

export function parsePlayerId(value: unknown): PlayerId {
  if (typeof value !== "string" || value.length === 0) throw new ApiError(400, "Missing playerId.");
  return value as PlayerId;
}

export function parseCode(value: unknown): string {
  if (typeof value !== "string" || value.trim().length !== 4) {
    throw new ApiError(400, "Room code must be 4 letters.");
  }
  return value;
}

export function parseAction(value: unknown): RoomAction {
  if (typeof value !== "object" || value === null || typeof (value as { type?: unknown }).type !== "string") {
    throw new ApiError(400, "Invalid action.");
  }
  const raw = value as Record<string, unknown>;
  switch (raw.type) {
    case "startGame":
      if (raw.game === "trivia" || raw.game === "wyr" || raw.game === "imposter") {
        return { type: "startGame", game: raw.game };
      }
      throw new ApiError(400, "Unknown game.");
    case "trivia/answer":
      if (typeof raw.choice === "number") return { type: "trivia/answer", choice: raw.choice };
      throw new ApiError(400, "Missing choice.");
    case "trivia/advance":
      return { type: "trivia/advance" };
    case "wyr/vote":
      if (raw.side === "a" || raw.side === "b") return { type: "wyr/vote", side: raw.side };
      throw new ApiError(400, "Vote must be side a or b.");
    case "wyr/advance":
      return { type: "wyr/advance" };
    case "imposter/startVote":
      return { type: "imposter/startVote" };
    case "imposter/vote":
      return { type: "imposter/vote", suspect: parsePlayerId(raw.suspect) };
    case "imposter/advance":
      return { type: "imposter/advance" };
    case "backToLobby":
      return { type: "backToLobby" };
    default:
      throw new ApiError(400, `Unknown action type "${String(raw.type)}".`);
  }
}
