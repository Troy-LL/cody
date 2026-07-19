import { NextResponse } from "next/server";
import { parsePlayerId, requireRoom, toClientRoom } from "@/lib/engine";
import { handleApiError } from "@/lib/http";

interface Params {
  params: Promise<{ code: string }>;
}

export async function GET(req: Request, { params }: Params): Promise<NextResponse> {
  try {
    const { code } = await params;
    const playerId = parsePlayerId(new URL(req.url).searchParams.get("player"));
    const room = requireRoom(code);
    return NextResponse.json({ room: toClientRoom(room, playerId) });
  } catch (error) {
    return handleApiError(error);
  }
}
