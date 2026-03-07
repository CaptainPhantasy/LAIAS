import { NextRequest, NextResponse } from "next/server";
import { stackServerApp } from "@/stack/server";

export async function middleware(request: NextRequest) {
  const user = await stackServerApp.getUser();

  if (!user) {
    return NextResponse.redirect(new URL("/handler/sign-in", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Protect all app routes EXCEPT:
  // - /handler/* (Stack Auth sign-in/sign-up/callback pages)
  // - /api/* (backend API routes — authenticated separately)
  // - /_next/* (Next.js internals)
  // - /favicon.ico, static assets
  matcher: [
    "/((?!handler|api|_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
