import { NextResponse } from "next/server";
import { applyAction, parseAction, parsePlayerId, toClientRoom } from "@/lib/engine";
import { handleApiError, readJson } from "@/lib/http";

interface Params {
  params: Promise<{ code: string }>;
}

export async function POST(req: Request, { params }: Params): Promise<NextResponse> {
  try {
    const { code } = await params;
    const body = await readJson(req);
    const playerId = parsePlayerId(body.playerId);
    const action = parseAction(body.action);
    const room = applyAction(code, playerId, action);
    return NextResponse.json({ room: toClientRoom(room, playerId) });
  } catch (error) {
    return handleApiError(error);
  }
}
