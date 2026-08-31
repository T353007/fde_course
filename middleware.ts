import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { TRACK_COOKIE } from "@/lib/track";

export function middleware(request: NextRequest) {
  const track = request.nextUrl.searchParams.get("track");
  if (track !== "full" && track !== "condensed") {
    return NextResponse.next();
  }

  const url = request.nextUrl.clone();
  url.searchParams.delete("track");
  const response = NextResponse.redirect(url);
  response.cookies.set(TRACK_COOKIE, track, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
  return response;
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico).*)"],
};
