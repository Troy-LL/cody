import { NextResponse } from "next/server";
import { createRoom, parseEmoji, parseName, toClientRoom } from "@/lib/engine";
import { handleApiError, readJson } from "@/lib/http";

export async function POST(req: Request): Promise<NextResponse> {
  try {
    const body = await readJson(req);
    const name = parseName(body.name);
    const emoji = parseEmoji(body.emoji);
    const { room, playerId } = createRoom(name, emoji);
    return NextResponse.json({ room: toClientRoom(room, playerId) }, { status: 201 });
  } catch (error) {
    return handleApiError(error);
  }
}
