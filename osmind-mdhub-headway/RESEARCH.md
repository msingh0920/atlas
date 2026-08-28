# Osmind + mdhub + Headway — API & Webhook Research

> Deep research into the integration surfaces of the three platforms used by the practice:
> **Osmind** (psychiatry EHR, osmind.org), **mdhub** (AI assistant for behavioral health, mdhub.ai),
> and **Headway** (insurance credentialing/billing network, headway.co).
> Research date: 2026-08-28. Every claim carries its source. This project is independent of the
> Atlas dashboard code in this repository.

---

## TL;DR

| Platform | Public API | Webhooks | Automation connectors | Realistic integration surface |
|---|---|---|---|---|
| **Osmind** | ❌ None public. Partner-gated API exists (evidenced by Keragon) | ❌ None | Keragon only (healthcare iPaaS) | Google/Outlook 2-way calendar sync, 1-way iCal feed, CSV dashboard exports, ticket-based bulk export, ISV partner program |
| **mdhub** | ✅ Yes — real, live, documented at docs.mdhub.ai (unannounced) | 🟡 Documented (FHIR `Subscription` rest-hooks) but not publicly deployed yet | None | v1 REST API (API key via support@mdhub.ai), FHIR R4 (partially live), Zoom app, Google Calendar sync |
| **Headway** | ❌ None public | ❌ None | None | Google Calendar 2-way sync, private iCal export URL, mandatory booking/cancellation notification emails, provider portal |

**The architecture that follows from this:** a small HIPAA-covered hub (custom serverless or self-hosted n8n)
that treats **Google Workspace (BAA signed) as the event bus** — Calendar sync + parsed notification
emails give you "webhooks" for Osmind and Headway, and mdhub's real API/FHIR surface gives you a
programmatic leg. Zapier and Make are disqualified for anything touching PHI (no BAA).

---

## 1. Osmind (osmind.org)

Interventional-psychiatry EHR: charting, e-prescribing (DrFirst), claims (Claim.MD), measurement-based
care, patient app. Sales-led SaaS — Osmind One is $249/mo per clinician ([pricing](https://www.osmind.org/pricing)).

### 1.1 No public developer surface

- The [API Evangelist profile](https://github.com/api-evangelist/osmind) (the repo you linked) is a
  **stub** (`x-tier: stub`, `apis: []`, pricing/onboarding "unknown") and states in its
  [apis.yml](https://raw.githubusercontent.com/api-evangelist/osmind/main/apis.yml):
  *"Osmind publishes no public developer API, developer portal, API reference, SDKs, or webhook
  surface on its public site."* (profile dated 2026-07; also at [apis.io/providers/osmind](https://apis.io/providers/osmind/))
- Verified by probing: `docs.osmind.org`, `api.osmind.org`, `developers.osmind.org`, `help.osmind.org`
  do not resolve. The two real support sites are end-user help centers, not developer docs:
  [support.osmind.org](https://support.osmind.org/en/) (Intercom) and
  [support.care.osmind.org](https://support.care.osmind.org/) (Pylon).
- An **internal REST API exists** — `https://prod-app-api.osmind.org`, found in the patient app's JS
  bundle, authenticated with AWS Cognito (Amplify). All unauthenticated probes return 403. It is not
  documented or offered to third parties.
- **No webhooks**: no events, no signing scheme, no setup UI anywhere in docs, changelogs, or the app
  bundle. Hard "does not exist," not "couldn't find."
- **Not ONC (g)(10) certified**: Osmind does not appear in the CHPL (g)(10) directory of 293 certified
  products ([Flexpa CHPL directory](https://www.flexpa.com/docs/network/chpl)), so no legally-mandated
  FHIR patient-access API exists. Third-party review sites saying "ONC certified" likely refer to
  certified partner modules (DrFirst).

### 1.2 A partner API exists behind closed doors

- **[Keragon](https://www.keragon.com/integrations/osmind)** (healthcare iPaaS) sells an Osmind
  integration: *"create automations using any action and trigger available through Osmind's API… If
  you can't find the action or trigger you are looking for, get in touch and we can easily add it."*
  This is the strongest public evidence that Osmind grants API access to partners.
- Osmind runs native, bespoke integrations (Zoom telehealth, DrFirst e-prescribing, Claim.MD claims,
  labs) through an **ISV partner program** — business-development conversation, not self-serve
  ([Zoom integration coverage](https://www.healthcareitnews.com/news/osmind-ehr-integrates-zoom-psychiatry-telehealth)).
- [Morf Health](https://www.morf.health/integrations/osmind) lists Osmind as "Request Integration"
  (not built). **Zapier/Make/n8n: no Osmind app exists** (zapier.com/apps/osmind → 404; no Make module;
  no n8n node).

### 1.3 Usable integration seams (no API needed)

- **Calendar sync** ([support article](https://support.care.osmind.org/articles/7140177460-sync-osmind-with-google-calendar-outlook-calendar-and-ical)):
  - Google Calendar & Outlook: **two-way sync via OAuth**.
  - Apple/iCal: **one-way (Osmind → subscriber) iCal subscription URL** — the closest thing to a
    machine-readable feed out of Osmind.
  - Sync latency up to ~30 min; *"Osmind should always be treated as the source of truth for scheduling."*
  - **PHI is stripped**: synced events show only *"Osmind Appointment"*
    ([Osmind blog](https://www.osmind.org/blog/ehr-scheduling-simplified-google-calendar-sync)) — so
    the calendar carries timing signals, not patient identity. Patient matching must happen elsewhere.
- **CSV exports** from [Visualize dashboards](https://support.care.osmind.org/articles/7240288110-using-dashboards-in-visualize-by-osmind)
  (Appointments, Payments; Visualize+ builder in development).
- **Bulk data export** via support ticket: ZIP of per-patient PDFs; no CSV/HL7/CCDA offered; messaging
  history excluded ([export article](https://support.care.osmind.org/articles/5377504051-exporting-your-data-from-osmind)).
- **Billing side door — Claim.MD**: Osmind claims flow through Claim.MD, and
  [Claim.MD offers a REST API + SFTP batch](https://www.claim.md/services-software-vendors) for
  real-time transactions. If the practice has (or can get) its own Claim.MD account credentials,
  claim/ERA data may be reachable programmatically. (To verify with Osmind/Claim.MD.)

---

## 2. mdhub (mdhub.ai)

YC S24, "AI-native operating system for behavioral health": AI scribe, intake/phone agent ("Sarah"),
questionnaires, and now its own EHR. Signs a BAA with every partner; SOC 2 Type II
([security](https://www.mdhub.ai/security), [enterprise FAQ](https://www.mdhub.ai/for/enterprises)).

### 2.1 There IS a real API — quietly published

**[docs.mdhub.ai](https://docs.mdhub.ai)** — "mdhub API Documentation," a Scalar-rendered OpenAPI 3.1
spec ([openapi.yaml](https://docs.mdhub.ai/openapi.yaml), `version 1.0.23`, last-modified 2026-08-26 —
two days before this research). It is **not linked from mdhub.ai and not indexed by search engines**
(soft launch). Status page: [mdhub.statuspage.io](https://mdhub.statuspage.io/).

Two API families:

**mdhub API v1** — `https://api.mdhub.ai/v1`, auth via `x-api-key` header. Rate limits: *"100 requests
per minute per API key, 1000 requests per hour."* Endpoints (verified live against the gateway):

| Endpoint | Purpose | Live? |
|---|---|---|
| `POST /v1/patients`, `PUT /v1/patients/{patientId}` | Create/update patients | ✅ (route exists; 401/405 without key) |
| `POST /v1/sessions/getTranscript` | Retrieve session transcript by sessionId | ✅ |
| `POST /v1/questionnaires/submit` | Submit custom questionnaire | ✅ |
| `POST /v1/questionnaires/submit-mdhub` | Submit standardized PHQ-9 / GAD-7 / MADRS raw scores | ✅ |
| `GET /v1/calls/all` | AI phone-agent call records (Session schema incl. `audioUrl`) | ✅ |
| `POST /v1/oauth2/token` | OAuth token endpoint (SMART Backend Services) | ✅ |

**FHIR R4 API** — `https://api.mdhub.ai/v1/fhir/R4`, OAuth 2.0 client-credentials with SMART v2 system
scopes (`system/Patient.read`, `system/Appointment.write`, …). 24 resources documented, including
Patient, Coverage/CoverageEligibility (BH-specific benefits, TMS/IOP auth), Schedule/Slot/Appointment,
Encounter, Observation (MBC scores), Questionnaire/QuestionnaireResponse, **DocumentReference**
(*"Session notes and transcripts"*), ServiceRequest, and **Subscription**.

> ⚠️ **Deployment lags the docs**: only `Patient` and the OAuth token endpoint answer today; the other
> 23 FHIR resources — including `Subscription` (webhooks) and `DocumentReference` (notes) — return the
> gateway's 404. Either not yet shipped or enabled per-tenant. Ask mdhub.

### 2.2 Webhooks

Documented as **FHIR `Subscription` rest-hooks** ([guides](https://docs.mdhub.ai/guides.html)):
*"Register a `Subscription` with a `rest-hook` channel and mdhub will POST notifications to your
endpoint when resources matching your `criteria` change"* (e.g. `Appointment?status=booked`; custom
`Authorization` header supported). **Not publicly routable yet** (see above). No other event mechanism
exists.

### 2.3 Access & integrations

- **Getting keys: email support@mdhub.ai** — stated three times in the docs ("You will receive an API
  key for the v1 API and OAuth 2.0 client credentials for the FHIR API"). No self-serve portal.
  Enterprise FAQ: *"mdhub has an open API for integrations and data access… We will scope specific
  integrations with you rather than overpromise."* ([enterprises](https://www.mdhub.ai/for/enterprises))
- **EHR integrations**: only **athenahealth** is productized (Marketplace partner,
  [announcement 2026-08-20](https://www.mdhub.ai/blog-posts/mdhub-partners-with-athenahealth-to-bring-ai-admissions-automation-to-mental-health-clinics)).
  The old per-EHR landing pages (`/ehr/advancedmd`, `/ehr/osmind`, ~28 probed) now 404 — mdhub pivoted
  to selling its own EHR. **`mdhub.ai/ehr/osmind` → 404; no Osmind integration exists publicly.**
  Also: [Zoom Marketplace app](https://www.mdhub.ai/blog-posts/mdhub-is-now-on-zoom), Google Calendar
  sync ([privacy policy](https://www.mdhub.ai/privacy-policy)), in-product fax.
- **No Zapier/Make/n8n connector** (Zapier catalog search: 0 results).
- No public mdhub↔Headway relationship; Headway builds its own AI notes feature.
- Engineering evidence: mdhub hires a
  [Forward Deployed Engineer](https://www.ycombinator.com/companies/mdhub/jobs/pZxi9cF-forward-deployed-engineer)
  to *"build and maintain integrations between mdhub's platform and customer systems — EHRs, billing
  clearinghouses, scheduling APIs."* Bespoke integrations are their model. (Their security page also
  contains a stray link to Medplum's security docs — hinting the FHIR stack may be Medplum-based.)

---

## 3. Headway (headway.co)

Insurance credentialing/billing/scheduling network for therapists & psychiatrists (NYC; legal entity
"Headway Colorado Behavioral Health Services, Inc.", corporate email domain findheadway.com).
$2.3B valuation (Series D, Jul 2024). Not to be confused with headwayapp.co (changelog SaaS — the
"Headway API" you find on apitracker.io is *that* company) or makeheadway.com (book app).

### 3.1 No public or partner API, no webhooks

- `developers.headway.co` and `docs.headway.co`: **no DNS records**. `api.headway.co` is a **live but
  fully closed** internal FastAPI backend behind Cloudflare — every probed path (incl. `/docs`,
  `/openapi.json`) returns `{"detail":"Not Found"}`; interactive docs disabled.
- [API Evangelist's Headway profile](https://github.com/api-evangelist/headway-co) (`apis: []`):
  *"Headway does not publish a public developer API, OpenAPI specification, SDK, or partner
  integration program — its platform is offered exclusively as a managed SaaS to providers, group
  practices, and health plans."* ([apis.io/providers/headway](https://apis.io/providers/headway/))
- **Webhooks: none.** Headway's own help-center search API returns `count: 0` for "webhook" (and for
  "API" and "Zapier"). [status.headway.co](https://status.headway.co) monitors exactly one component
  ("headway.co") — no API component.
- **No EHR partner program** ("Headway Connect" / "Headway for EHRs" don't exist). Headway's strategy
  is the opposite — it ships its **own free insurance-native EHR** with AI-assisted notes ("Scribe")
  and embedded telehealth
  ([PRNewswire, Sept 2025](https://www.prnewswire.com/news-releases/headway-expands-its-insurance-native-ehr-with-ai-assisted-notes-and-enhanced-features-302550728.html)
  — a release with *"no mentions of APIs, integrations with other EHR systems, interoperability
  standards, or data import/export"*). Independent scribe trackers:
  *"No tracked scribe publishes a native Headway integration today — copy-paste workflow is the
  default"* ([comparetherapyscribe.com](https://comparetherapyscribe.com/ehr/headway)).
- The one EHR-facing motion: a
  [May 2025 primary-care referral program](https://www.prnewswire.com/news-releases/headway-launches-nationwide-solution-to-bridge-the-primary-care-mental-health-divide-through-insurance-302453801.html)
  (*"Through their existing EHR system, physicians can refer patients to Headway in less than two
  minutes"*) — mechanism, vendors, and access process undisclosed. Payer "integrations" are commercial
  network arrangements, not developer APIs.
- **Zapier / Make / n8n: nothing.** Zapier's live catalog returns 0 results for headway.co;
  `zapier.com/apps/headway` → 404.

### 3.2 Sanctioned surfaces of the provider portal ("Sigmund")

The provider portal is named **Sigmund**
([intro article](https://help.headway.co/hc/en-us/articles/7663746214420-Introduction-to-Sigmund)).
(The help center HTML is Cloudflare-gated, but its Zendesk JSON API is open — quotes below pulled from
`help.headway.co/api/v2/help_center/...`.)

- **Google Calendar two-way OAuth sync**: Settings → Calendar → "Connect Google Calendar", with
  "Import into Headway" and "Export to Google" toggles. *"Headway will automatically remove
  availability that conflicts with your external events so you won't be double-booked."*
  ([Importing external calendars](https://help.headway.co/hc/en-us/articles/4409497691540-Importing-external-calendars-into-Sigmund),
  [Managing your calendar](https://help.headway.co/hc/en-us/articles/4411124539540-Managing-your-calendar))
  Supported import sources: Google, Outlook, SimplePractice **via Google** only.
- **ICS feed out**: Settings → Calendar → "Export Sigmund Calendar" → copy private URL.
  **Client names are stripped**: *"Client details will not be shown in your external calendar. You'll
  be able to view the event type and timing… you'll have to view the event in Sigmund to see full
  details."* The **telehealth link does flow through** to the external calendar.
  ([Exporting your Headway calendar](https://help.headway.co/hc/en-us/articles/4409491542292-Exporting-your-Headway-calendar),
  [Telehealth](https://help.headway.co/hc/en-us/articles/4421041745684-Telehealth-teletherapy-virtual-sessions))
  Treat the URL as a credential. If Google subscribes to an ICS URL it refreshes only every 12–24h —
  poll the feed directly from the hub (5–15 min) or prefer the native Google sync.
- **Emails**: client-facing messages are well documented (welcome, intake reminders, session
  reminders with price, *"invoices after each session"* —
  [client intake & experience](https://help.headway.co/hc/en-us/articles/4403895592724-Headway-s-client-intake-and-experience)).
  **Provider-side** booking/cancellation notification emails are *not* publicly documented — verify
  with a real provider account and capture samples before betting on the email-parsing leg.
- **CSV / reports**: documented only for **group practices** (admin "practice-level payments report",
  one row per transaction —
  [Group practice payments](https://help.headway.co/hc/en-us/articles/39971268274580-Group-practice-payments)).
  Solo providers get the Payments tab UI; no solo CSV documented.
- Embedded vendors: Stripe (payments), Plaid (bank), DrFirst (eRx), Google (calendar OAuth), Zendesk.
  Security contact: security@findheadway.com. SOC 2 Type II + HIPAA asserted in prose
  ([compliance page](https://headway.co/resources/behavioral-health-compliance)); no public trust
  center.

### 3.3 Don't scrape the portal

A DIY client for `api.headway.co` means defeating Cloudflare bot management + session auth, violating
ToS that prohibit any *"automated system, including spiders, robots… scrapers"* and *"unauthorized
script[s]"* ([terms](https://headway.co/legal/terms)), voiding session-confirmation protections, and
handling PHI with no BAA. Headway also began **biometric identity verification** for providers and
patients in May 2026
([BHB coverage](https://bhbusiness.com/2026/05/28/headway-requires-biomarker-verification-for-patients-providers/)).
No public reverse-engineering projects exist (GitHub search: 1 unrelated hit). Beware
`headwayproviderportal.net/.com` — third-party lookalike SEO sites, not Headway.

---

## 4. Automation platforms & HIPAA reality

| Vendor | BAA? | Notes | Source |
|---|---|---|---|
| **Zapier** | ❌ Never | *"No, Zapier isn't HIPAA compliant… you can't use it to automate anything involving PHI. That includes not signing a BAA."* (Zapier's own blog) | [zapier.com/blog/is-zapier-hipaa-compliant](https://zapier.com/blog/is-zapier-hipaa-compliant/) |
| **Make.com** | ❌ No, any tier | Community reports Make refused to sign a BAA | [community thread](https://community.make.com/t/will-make-com-sign-a-baa-for-hippa/27130), [analysis](https://www.accountablehq.com/post/is-make-com-hipaa-compliant-what-healthcare-teams-need-to-know) |
| **n8n Cloud** | ❌ No (official, 2026-01) | *"Currently, n8n does not offer a BAA"* — but **self-hosted n8n in your own BAA-covered cloud is the accepted pattern** (BAA is with AWS/GCP, not n8n) | [n8n community (staff answer)](https://community.n8n.io/t/baa-agreement-for-n8n-cloud/219805), [Accountable guide](https://www.accountablehq.com/post/is-n8n-hipaa-compliant-baa-self-hosting-best-practices) |
| **Keragon** | ✅ All paid plans | Healthcare iPaaS; BAA self-serve at checkout; **has an Osmind connector listing**; no Headway/mdhub connectors | [BAA article](https://help.keragon.com/hc/en-us/articles/32165862678802-Signing-a-Business-Associate-Agreement-BAA-With-Keragon), [Osmind listing](https://www.keragon.com/integrations/osmind) |
| **Google Workspace** | ✅ Self-serve (Admin console) | HIPAA "Included Functionality" explicitly names **Gmail and Google Calendar** — legal to use as PHI transport. Free/personal Gmail is NOT eligible | [HIPAA functionality list](https://workspace.google.com/terms/2015/1/hipaa_functionality/), [admin guide](https://knowledge.workspace.google.com/admin/compliance/hipaa-compliance-with-google-workspace-and-cloud-identity) |
| **AWS** | ✅ Free, self-serve (Artifact) | Lambda, API Gateway, SQS, SES, EventBridge, DynamoDB all HIPAA-eligible | [aws.amazon.com/compliance/hipaa-compliance](https://aws.amazon.com/compliance/hipaa-compliance/), [eligible services](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/) |
| **Google Cloud** | ✅ Self-serve (console) | BAA covers Cloud Run, Cloud Functions, 150+ products | [cloud.google.com/security/compliance/hipaa](https://cloud.google.com/security/compliance/hipaa) |
| **Render** | ✅ Scale/Enterprise plans | HIPAA-enabled workspaces, +20% usage fee | [render.com/docs/hipaa-compliance](https://render.com/docs/hipaa-compliance) |
| **Aptible** | ✅ Production plan ($499/mo) | Overkill at this scale | [aptible.com/pricing](https://www.aptible.com/pricing) |

Also ruled out: commercial email parsers (Mailparser, Parseur — no BAA today); enterprise health iPaaS
(Redox, Health Gorilla, 1upHealth, Metriport — none list Osmind/Headway).

**Community knowledge check**: essentially zero public playbooks exist for connecting these specific
tools (nothing on Reddit/indexed forums for "Osmind + Headway", "Osmind + Zapier", "mdhub + Osmind").
The closest lore: third-party guides on bridging Headway's calendar
([Calensync](https://calensync.live/blog/synchronize-your-headway-calendar-with-google),
[ClinikEHR](https://clinikehr.com/blog/how-to-sync-headway-calendar-with-central-calendar-2027) —
*"This sync is one-way (read-only)… Treat your Headway calendar link like a password"*).

---

## 5. Recommended architecture

### 5.1 What "connect all three" actually means here

Only mdhub exposes a real API today. Osmind and Headway are closed products whose machine-readable
surfaces are calendar feeds (both PHI-stripped), CSV/exports, and emails. So the integration is a
**hub-and-spoke design where the hub manufactures its own webhooks** from those surfaces:

```
             Headway (Sigmund)                      Osmind EHR
      native Google sync / private ICS        native 2-way Google sync
        (client names stripped)              (events say "Osmind Appointment")
                   │                                    │
                   ▼                                    ▼
     ┌─────────────────────────────────────────────────────────────┐
     │        Google Workspace tenant  (BAA accepted)              │
     │   • "bus" calendars (Headway cal, Osmind cal)               │
     │   • dedicated mailbox for Headway notification emails       │
     └───────────────┬─────────────────────────┬───────────────────┘
        Calendar API events.watch         Gmail API users.watch
        (push → HTTPS webhook)            (Pub/Sub push → webhook)
                   │                           │
                   ▼                           ▼
     ┌─────────────────────────────────────────────────────────────┐
     │   Integration hub  (BAA-covered cloud: AWS/GCP)             │
     │   API GW → Lambda receivers → SQS (+DLQ) → workers          │
     │   DynamoDB: roster/matching table, idempotency, audit log   │
     │   EventBridge: watch renewals, ICS poller, nightly recon    │
     └───────┬─────────────────────────────────────┬───────────────┘
             │  x-api-key / OAuth2 (SMART)         │  (future, if granted)
             ▼                                     ▼
        mdhub API v1 + FHIR R4                Osmind partner API
        patients, questionnaires,             (exists behind ISV/BD door —
        transcripts, notes*, Subscription*    Keragon proves it)
                                              + Claim.MD REST API for claims
        (* documented, pending deployment)
```

### 5.2 Ranked options

1. **Custom serverless hub (recommended — this is the "do APIs and webhooks for him" build).**
   One AWS account with the free self-serve BAA (AWS Artifact); API Gateway + Lambda + SQS + DynamoDB
   + EventBridge are all HIPAA-eligible. Google Workspace tenant with BAA accepted (Admin console →
   Legal & compliance). Google Calendar `events.watch` push channels (must be renewed — no
   auto-renewal) and Gmail `users.watch` (renew ≤7 days) turn calendar/email changes into real
   webhooks hitting the hub.
2. **Keragon (managed healthcare iPaaS)** — BAA on all paid plans, has an Osmind connector, no-code.
   Lowest effort; verify in a demo what its Osmind triggers/actions actually are and pricing. mdhub
   and Headway legs still ride HTTP/Gmail/Calendar connectors inside Keragon.
3. **Self-hosted n8n inside the BAA'd account** — middle ground: webhook/Gmail/Calendar/HTTP nodes
   and retries without writing a service. n8n itself signs no BAA, so cloud-host it yourself.

Zapier and Make are **out** for anything touching PHI (no BAA at any tier).

### 5.3 Concrete flows to build (in order of value)

1. **Session ledger + nightly reconciliation (the killer feature).** Ingest Headway sessions
   (calendar/ICS) + Osmind appointments (calendar) + mdhub notes/transcripts (API). Nightly job
   diffs the three and emails/texts a digest: *sessions with no signed note; Headway sessions never
   confirmed (unbilled = lost revenue); Osmind appointments with no Headway session; tomorrow's
   schedule with telehealth links.* Works entirely on surfaces available **today**, no vendor
   permission needed.
2. **Booking propagation.** New Headway event on the bus calendar → hub checks for a time-matching
   Osmind appointment → if missing, creates a task/alert (or writes to Osmind once partner API
   access exists). Both feeds are PHI-stripped, so matching is by time-slot + provider + a roster
   table the hub keeps (patient identity enriched from mdhub's Patient API where possible).
3. **Notes pipeline.** mdhub session finalized → pull transcript/note via API (DocumentReference
   once FHIR fully deploys; transcripts endpoint today) → deliver to the clinician for paste-in to
   Osmind with deep links (fully automatic write-back only when Osmind grants API access) → mark the
   ledger.
4. **Measurement-based care loop.** Push PHQ-9/GAD-7/MADRS scores into mdhub via
   `POST /v1/questionnaires/submit-mdhub`; mirror scores into the ledger for outcomes tracking
   across systems.
5. **Claims visibility (stretch).** If the practice can get credentials for its Claim.MD account
   (Osmind's clearinghouse), poll Claim.MD's REST API for claim/ERA status and join it to the ledger.

### 5.4 Hub non-negotiables

- BAAs signed **before** PHI flows: Google Workspace, AWS/GCP, mdhub (offered to every partner),
  Keragon if used. Personal Gmail is not BAA-eligible — use Workspace.
- Idempotency keys `(source, event_id, updated_at)`; SQS DLQ + alarm; append-only audit table
  (6-year retention); KMS encryption; secrets (ICS URL, OAuth refresh tokens, API keys) in Secrets
  Manager; least-privilege IAM.
- Treat calendar/ICS URLs as credentials. Never scrape the Headway or Osmind portals.

---

## 6. Action items

**Emails to send now (both are gatekept by humans, so start the clock):**

1. **support@mdhub.ai** — request v1 API key + FHIR OAuth client credentials for the practice.
   Ask specifically: (a) is the full FHIR R4 resource set (esp. `DocumentReference`,
   `Subscription` webhooks, `Appointment`) enabled for customer tenants or still rolling out?
   (b) is there an audio-upload/session-create endpoint beyond the documented transcript retrieval?
   (c) any Osmind write-back on the roadmap? (d) BAA paperwork.
2. **Osmind CSM / support** — ask what API/integration access an existing practice can get under the
   ISV/partner program (mention Keragon advertises "any action and trigger available through
   Osmind's API"), whether webhooks exist for partners, and whether the practice can get Claim.MD
   account credentials for claims data.

**Verify inside the brother's accounts (30 minutes of clicking):**

3. Headway Sigmund → Settings → Calendar: turn on Google sync ("Export to Google") and copy the
   "Export Sigmund Calendar" ICS URL. Check what fields actually appear in synced events.
4. Check whether Headway sends the provider booking/cancellation notification emails; capture raw
   samples for the parser. (Client-side emails are documented; provider-side isn't.)
5. Osmind → Schedule: connect Google Calendar sync; confirm events show as "Osmind Appointment"
   and measure sync latency. Copy the iCal subscription URL. Try a Visualize CSV export.
6. Confirm whether the practice is a Headway **group** (admin payments-report CSV exists) or solo
   (no documented CSV).

**Set up compliance rails:**

7. Google Workspace tenant (if not already) + accept BAA in Admin console; AWS account + accept BAA
   in AWS Artifact.

**Strategic question to settle with him before building big:** Headway now bundles a free EHR + AI
scribe, Osmind bundles billing/RCM, and mdhub now sells its own EHR — all three are converging on
each other's territory. Confirm the three-tool stack is staying before investing beyond flow #1
(the reconciliation ledger — which is valuable even if the stack later shrinks to two tools).

---

## Appendix: source quality notes

- Four parallel deep-research passes (one per platform + one on middleware/HIPAA), 300+ tool calls,
  primary sources fetched directly wherever possible (docs sites probed by URL, live API gateways
  probed for real error signatures, Zapier catalog queried via its own API, help centers read via
  their Zendesk JSON APIs).
- Where two sources conflicted (e.g., whether Headway provider-side booking emails exist), the more
  primary source won and the conflict is flagged inline as a verification item.
- Unknowns that only vendor conversations can resolve are listed in §6 rather than guessed.

