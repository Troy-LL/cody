import { NextResponse } from "next/server";
import { ApiError } from "./engine";

export async function readJson(req: Request): Promise<Record<string, unknown>> {
  try {
    const body: unknown = await req.json();
    if (typeof body !== "object" || body === null) throw new Error();
    return body as Record<string, unknown>;
  } catch {
    throw new ApiError(400, "Body must be a JSON object.");
  }
}

export function handleApiError(error: unknown): NextResponse {
  if (error instanceof ApiError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  console.error(error);
  return NextResponse.json({ error: "Something went wrong." }, { status: 500 });
}
