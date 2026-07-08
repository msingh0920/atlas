// Basic-auth gate for the whole site. Free-tier Netlify edge function.
// The credential is verified against a SHA-256 hash (htpasswd-style), so no
// plaintext password exists anywhere server-side. To rotate: hash the new
// "Basic " + base64("user:password") header value and replace EXPECTED_HASH.
const EXPECTED_HASH = "e8a58d4ff15432965d1b5e1803db50a1a2fad3bd03d3e63bbf87ae6e3f29bc57";

async function sha256hex(s: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(d)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export default async (request: Request, context: { next: () => Promise<Response> }) => {
  const auth = request.headers.get("authorization") ?? "";
  if (auth && (await sha256hex(auth)) === EXPECTED_HASH) {
    return context.next();
  }
  return new Response("Atlas — authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Atlas"', "Cache-Control": "no-store" },
  });
};

export const config = { path: "/*" };
