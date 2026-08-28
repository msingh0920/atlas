# Practice Integration Hub — Osmind × mdhub × Headway

Standalone project (unrelated to the Atlas dashboard in this repo): connect a psychiatry practice's
three platforms — **Osmind** (EHR), **mdhub** (AI assistant), **Headway** (insurance billing) — with
APIs and webhooks.

**Start here → [`RESEARCH.md`](./RESEARCH.md)** — deep research (2026-08-28) into what each platform
actually exposes, with sources for every claim, plus the recommended architecture.

## One-paragraph summary

Only **mdhub** has a real API (quietly published at [docs.mdhub.ai](https://docs.mdhub.ai): key-gated
REST v1 + partially-deployed FHIR R4 with documented-but-not-yet-live `Subscription` webhooks; keys
via support@mdhub.ai). **Osmind** and **Headway** publish no public API or webhooks; their usable
surfaces are Google Calendar sync (both strip PHI from events), private iCal feeds, CSV/exports, and
emails. Osmind grants partner API access behind a BD door (Keragon integrates with it). Headway has
no partner program at all and its ToS bars portal automation. The recommended build is a small
HIPAA-covered serverless hub (AWS + Google Workspace, both under BAA) that converts calendar and
email changes into webhooks, talks to mdhub's API directly, and runs a nightly three-way
reconciliation ledger (sessions ↔ notes ↔ billing). Zapier/Make are disqualified (no BAA).

## Planned components (not yet built)

- `hub/` — webhook receivers (Google Calendar push, Gmail push, mdhub), queue workers, recon jobs
- `infra/` — IaC for the BAA-covered AWS stack

## Status

- [x] Deep research + architecture (see RESEARCH.md)
- [ ] API access requested from mdhub (support@mdhub.ai) and Osmind (CSM/ISV program)
- [ ] Account-level verification steps (RESEARCH.md §6)
- [ ] BAAs: Google Workspace, AWS
- [ ] Build flow #1: reconciliation ledger
