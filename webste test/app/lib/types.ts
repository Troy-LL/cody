export type RoomCode = string & { readonly __brand: "RoomCode" };
export type PlayerId = string & { readonly __brand: "PlayerId" };

export interface Player {
  id: PlayerId;
  name: string;
  emoji: string;
  score: number;
  joinedAt: number;
}

export type GameId = "trivia" | "wyr" | "imposter";

export interface TriviaQuestion {
  prompt: string;
  choices: [string, string, string, string];
  answer: 0 | 1 | 2 | 3;
}

export interface TriviaAnswer {
  choice: number;
  at: number;
}

export type TriviaPhase =
  | { kind: "question"; index: number; askedAt: number; answers: Record<PlayerId, TriviaAnswer> }
  | { kind: "reveal"; index: number; answers: Record<PlayerId, TriviaAnswer>; gained: Record<PlayerId, number> }
  | { kind: "final" };

export interface TriviaState {
  game: "trivia";
  questions: TriviaQuestion[];
  phase: TriviaPhase;
}

export interface WyrPrompt {
  a: string;
  b: string;
}

export type WyrSide = "a" | "b";

export type WyrPhase =
  | { kind: "vote"; index: number; votes: Record<PlayerId, WyrSide> }
  | { kind: "reveal"; index: number; votes: Record<PlayerId, WyrSide>; gained: Record<PlayerId, number> }
  | { kind: "final" };

export interface WyrState {
  game: "wyr";
  prompts: WyrPrompt[];
  phase: WyrPhase;
}

export type ImposterPhase =
  | { kind: "discuss"; startedAt: number }
  | { kind: "vote"; votes: Record<PlayerId, PlayerId> }
  | {
      kind: "reveal";
      votes: Record<PlayerId, PlayerId>;
      accused: PlayerId | null;
      caught: boolean;
      gained: Record<PlayerId, number>;
    }
  | { kind: "final" };

export interface ImposterState {
  game: "imposter";
  category: string;
  word: string;
  imposter: PlayerId;
  phase: ImposterPhase;
}

export type GameState = { game: "lobby" } | TriviaState | WyrState | ImposterState;

export interface Room {
  code: RoomCode;
  hostId: PlayerId;
  createdAt: number;
  version: number;
  players: Player[];
  state: GameState;
}

// ---- Client-facing views (redacted per player at the API boundary) ----

export interface ClientPlayer {
  id: PlayerId;
  name: string;
  emoji: string;
  score: number;
  isHost: boolean;
}

export type ClientTriviaView =
  | {
      game: "trivia";
      kind: "question";
      index: number;
      total: number;
      prompt: string;
      choices: [string, string, string, string];
      answeredIds: PlayerId[];
      yourChoice: number | null;
    }
  | {
      game: "trivia";
      kind: "reveal";
      index: number;
      total: number;
      prompt: string;
      choices: [string, string, string, string];
      correct: number;
      counts: [number, number, number, number];
      gained: Record<PlayerId, number>;
    }
  | { game: "trivia"; kind: "final" };

export type ClientWyrView =
  | {
      game: "wyr";
      kind: "vote";
      index: number;
      total: number;
      prompt: WyrPrompt;
      votedIds: PlayerId[];
      yourVote: WyrSide | null;
    }
  | {
      game: "wyr";
      kind: "reveal";
      index: number;
      total: number;
      prompt: WyrPrompt;
      countA: number;
      countB: number;
      gained: Record<PlayerId, number>;
    }
  | { game: "wyr"; kind: "final" };

export type ImposterRole =
  | { role: "crew"; category: string; word: string }
  | { role: "imposter"; category: string };

export type ClientImposterView =
  | { game: "imposter"; kind: "discuss"; you: ImposterRole; startedAt: number }
  | { game: "imposter"; kind: "vote"; you: ImposterRole; votedIds: PlayerId[]; yourVote: PlayerId | null }
  | {
      game: "imposter";
      kind: "reveal";
      imposter: PlayerId;
      accused: PlayerId | null;
      caught: boolean;
      word: string;
      category: string;
      votes: Record<PlayerId, PlayerId>;
      gained: Record<PlayerId, number>;
    }
  | { game: "imposter"; kind: "final" };

export type ClientView = { game: "lobby" } | ClientTriviaView | ClientWyrView | ClientImposterView;

export interface ClientRoom {
  code: RoomCode;
  you: PlayerId;
  hostId: PlayerId;
  version: number;
  players: ClientPlayer[];
  view: ClientView;
}

// ---- Actions (parsed at the API boundary, applied by the reducer) ----

export type RoomAction =
  | { type: "startGame"; game: GameId }
  | { type: "trivia/answer"; choice: number }
  | { type: "trivia/advance" }
  | { type: "wyr/vote"; side: WyrSide }
  | { type: "wyr/advance" }
  | { type: "imposter/startVote" }
  | { type: "imposter/vote"; suspect: PlayerId }
  | { type: "imposter/advance" }
  | { type: "backToLobby" };
