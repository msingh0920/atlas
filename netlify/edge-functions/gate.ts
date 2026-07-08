// Basic-auth gate for the whole site. Free-tier Netlify edge function.
// Set the GATE_PASSWORD env var on the site; until it is set, the gate
// FAILS CLOSED (everything 401s) so an unconfigured deploy never exposes data.
export default async (request: Request, context: { next: () => Promise<Response> }) => {
  const password = Netlify.env.get("GATE_PASSWORD");
  const auth = request.headers.get("authorization") ?? "";
  if (password && auth === "Basic " + btoa(`manav:${password}`)) {
    return context.next();
  }
  return new Response("Atlas — authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Atlas"', "Cache-Control": "no-store" },
  });
};

export const config = { path: "/*" };
