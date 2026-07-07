# Atlas — Personal Mission Control

Atlas is the face of your personal "Jarvis" system: a single-page dashboard that
puts your day in one place.

## What it does

- **Daily Briefing** — a panel where your Claude "brain" (see the
  [`AtlasClaude`](https://github.com/msingh0920/AtlasClaude) repo) drops a
  morning summary of Slack, Google Drive, GitHub, and monday.com activity.
- **Today's Tasks** — quick task list with done/undone tracking.
- **Quick Capture** — an autosaving scratchpad for brain dumps.
- **Connected Apps** — a customizable launcher grid for every app in your life
  (Gmail, Calendar, Drive, Slack, GitHub, monday, Figma, Canva, Netlify, Claude…).

Everything is **local-first**: your tasks, notes, briefing, and app list live in
your browser's localStorage. No backend, no accounts, no tracking.

## Run it

There is no build step. Either:

```sh
# open directly
open index.html

# or serve it
npx serve .
```

## Deploy it

Deployment config lives in the [`deploy`](https://github.com/msingh0920/deploy)
repo (Netlify-ready). Any static host works — it's one HTML file.

## The three-repo system

| Repo          | Role      | What's inside                                        |
|---------------|-----------|------------------------------------------------------|
| `atlas`       | The face  | This dashboard                                       |
| `AtlasClaude` | The brain | Claude Code config + skills (`/briefing`, `/weekly-review`, `/capture`) that connect your real apps |
| `deploy`      | The ship  | Netlify deployment config for the dashboard          |
