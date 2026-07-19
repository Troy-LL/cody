# Confetti Club demo recording

`record-demo.mjs` drives a full party through the browser: a host tab plus two player tabs walk the lobby, Trivia Blitz, Would You Rather, and Imposter Word end to end, saving screenshots to `shots/`.

## Setup

```bash
cd demo
npm install
# the app must be built once:
cd ../app && npm install && npm run build && cd ../demo
```

## Record a video (headful, slowed down)

```bash
SLOWMO=120 PAUSE=1500 node record-demo.mjs
```

Chrome opens visibly; capture the window with your screen recorder. The script boots the app itself on a free port. To drive an app you already started, set `BASE_URL=http://localhost:3000`.

Heads up: `npm run dev` in `app/` overwrites the production build in `.next`. If the dev server has run since the last build, re-run `npm run build` in `app/` first, or the self-booted server will fail to start (the script prints the server's output when that happens).

## CI / smoke mode (headless)

```bash
HEADLESS=1 node record-demo.mjs
```

Exit code 0 plus ~14 screenshots in `shots/` means the whole flow worked.

## Options

| Env var | Meaning | Default |
| --- | --- | --- |
| `BASE_URL` | Use an already-running app instead of booting one | boots `next start` |
| `CHROME_PATH` | Chrome binary | `/usr/local/bin/google-chrome` |
| `HEADLESS=1` | Headless mode | headful |
| `SLOWMO` | Milliseconds of slow-mo per browser op | `0` |
| `PAUSE` | Extra dwell on each notable screen (ms) | `600` |
