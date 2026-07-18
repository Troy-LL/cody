import { NextResponse } from "next/server";
import { joinRoom, parseEmoji, parseName, toClientRoom } from "@/lib/engine";
import { handleApiError, readJson } from "@/lib/http";

interface Params {
  params: Promise<{ code: string }>;
}

export async function POST(req: Request, { params }: Params): Promise<NextResponse> {
  try {
    const { code } = await params;
    const body = await readJson(req);
    const name = parseName(body.name);
    const emoji = parseEmoji(body.emoji);
    const { room, playerId } = joinRoom(code, name, emoji);
    return NextResponse.json({ room: toClientRoom(room, playerId) }, { status: 200 });
  } catch (error) {
    return handleApiError(error);
  }
}
