#!/usr/bin/env node
// Walks a full Confetti Club party (host + 2 players in three tabs) through
// the lobby and all three mini-games, saving screenshots to shots/.
//
// Env:
//   BASE_URL    use an already-running app (otherwise boots `next start` from ../app)
//   CHROME_PATH path to Chrome binary   (default: /usr/local/bin/google-chrome)
//   HEADLESS=1  run headless (for CI); default is headful for video recording
//   SLOWMO=<ms> slow every puppeteer op down, e.g. SLOWMO=120 for a watchable pace
//   PAUSE=<ms>  extra dwell time on each notable screen (default 600, use ~1500 for video)

import { spawn } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const demoDir = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(demoDir, "..", "app");
const shotsDir = path.join(demoDir, "shots");

const CHROME = process.env.CHROME_PATH ?? "/usr/local/bin/google-chrome";
const HEADLESS = process.env.HEADLESS === "1";
const SLOWMO = Number(process.env.SLOWMO ?? 0);
const PAUSE = Number(process.env.PAUSE ?? 600);
// Interval polling, not the raf default: headless Chrome throttles rAF in
// backgrounded tabs, which deadlocks waits on the two player pages.
const WAIT = { timeout: 30000, polling: 250 };

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let shotCounter = 0;
async function shot(page, label) {
  shotCounter += 1;
  const file = path.join(shotsDir, `${String(shotCounter).padStart(2, "0")}-${label}.png`);
  await page.screenshot({ path: file });
  console.log(`  shot: ${path.basename(file)}`);
}

function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.listen(0, "127.0.0.1", () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
    srv.on("error", reject);
  });
}

async function waitForServer(base, server, getOutput, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (server && server.exitCode !== null) {
      throw new Error(
        `App server exited with code ${server.exitCode} before becoming ready. Output:\n${getOutput()}`,
      );
    }
    try {
      if ((await fetch(base)).ok) return;
    } catch {
      // not up yet
    }
    await sleep(300);
  }
  throw new Error(`App not reachable at ${base}.${server ? ` Server output:\n${getOutput()}` : ""}`);
}

const pageNames = new WeakMap();

// Node-side polling instead of puppeteer's waitForSelector: that API polls via
// requestAnimationFrame, which hidden/backgrounded headless tabs never fire,
// so waits on the non-focused player tabs would hang forever.
async function pollPage(page, testid, predicate, label) {
  const selector = `[data-testid="${testid}"]`;
  const deadline = Date.now() + WAIT.timeout;
  while (Date.now() < deadline) {
    const ok = await page.evaluate(predicate, selector);
    if (ok) return;
    await sleep(WAIT.polling);
  }
  throw new Error(`[${pageNames.get(page) ?? "?"}] timed out: ${label} ${testid}`);
}

function waitFor(page, testid) {
  return pollPage(
    page,
    testid,
    (sel) => {
      const el = document.querySelector(sel);
      if (!el) return false;
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    },
    "waitFor",
  );
}

async function click(page, testid) {
  await pollPage(
    page,
    testid,
    (sel) => {
      const el = document.querySelector(sel);
      return Boolean(el) && !el.disabled;
    },
    "click",
  );
  await page.evaluate((sel) => document.querySelector(sel).click(), `[data-testid="${testid}"]`);
}

async function waitForCount(page, testidPrefix, min) {
  const deadline = Date.now() + WAIT.timeout;
  const selector = `[data-testid^="${testidPrefix}"]`;
  while (Date.now() < deadline) {
    const count = await page.evaluate((sel) => document.querySelectorAll(sel).length, selector);
    if (count >= min) return;
    await sleep(WAIT.polling);
  }
  throw new Error(`[${pageNames.get(page) ?? "?"}] timed out waiting for ${min}+ ${testidPrefix}`);
}

async function joinFlow(page, base, { code, name, emoji, host }) {
  await page.bringToFront();
  await page.goto(base, { waitUntil: "networkidle2" });
  if (!host) {
    await click(page, "tab-join");
    await page.type('[data-testid="join-code"]', code);
  }
  await page.type('[data-testid="player-name"]', name);
  await click(page, `landing-emoji-${emoji}`);
  await click(page, "submit-enter");
  await waitFor(page, "room-code-header");
}

async function main() {
  fs.rmSync(shotsDir, { recursive: true, force: true });
  fs.mkdirSync(shotsDir, { recursive: true });

  let base = process.env.BASE_URL ?? null;
  let server = null;
  let serverOutput = "";
  if (!base) {
    const port = await freePort();
    base = `http://127.0.0.1:${port}`;
    console.log(`Booting next start from ${appDir} on ${base} (run \`npm run build\` there first)`);
    server = spawn("node", ["node_modules/next/dist/bin/next", "start", "-p", String(port)], {
      cwd: appDir,
      stdio: ["ignore", "pipe", "pipe"],
    });
    const collect = (chunk) => {
      serverOutput = (serverOutput + chunk).slice(-4000);
    };
    server.stdout.on("data", collect);
    server.stderr.on("data", collect);
  }
  const getOutput = () => serverOutput.trim() || "(no output)";
  const killServer = () => {
    if (server && !server.killed) server.kill("SIGTERM");
  };
  process.on("exit", killServer);
  await waitForServer(base, server, getOutput);

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: HEADLESS,
    slowMo: SLOWMO,
    protocolTimeout: 60000,
    defaultViewport: { width: 1280, height: 800 },
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--window-size=1320,900",
      "--disable-background-timer-throttling",
      "--disable-backgrounding-occluded-windows",
      "--disable-renderer-backgrounding",
    ],
  });

  try {
    // sessionStorage is per-tab, so three tabs are three independent players.
    const host = await browser.newPage();
    const max = await browser.newPage();
    const pip = await browser.newPage();
    const everyone = [host, max, pip];
    pageNames.set(host, "Zoe(host)");
    pageNames.set(max, "Max");
    pageNames.set(pip, "Pip");
    browser.__pages = everyone;

    console.log("[lobby]");
    await host.bringToFront();
    await host.goto(base, { waitUntil: "networkidle2" });
    await shot(host, "landing");
    await joinFlow(host, base, { name: "Zoe", emoji: "🦩", host: true });
    await waitFor(host, "room-code");
    const code = await host.$eval('[data-testid="room-code"]', (el) => el.textContent.trim());
    console.log(`  room code: ${code}`);
    await shot(host, "lobby-host-alone");

    await joinFlow(max, base, { code, name: "Max", emoji: "👾", host: false });
    await joinFlow(pip, base, { code, name: "Pip", emoji: "🐙", host: false });
    await host.bringToFront();
    await waitForCount(host, "player-chip-", 3);
    await sleep(PAUSE);
    await shot(host, "lobby-three-players");

    // ---- Trivia Blitz ----
    console.log("[trivia]");
    await click(host, "start-trivia");
    for (let q = 0; q < 5; q++) {
      for (const page of everyone) await waitFor(page, "trivia-question-screen");
      if (q === 0) {
        await host.bringToFront();
        await sleep(PAUSE);
        await shot(host, "trivia-question");
      }
      await click(host, "answer-0");
      await click(max, "answer-1");
      if (q === 0) {
        await max.bringToFront();
        await shot(max, "trivia-answer-locked");
      }
      await click(pip, "answer-2");
      await waitFor(host, "trivia-reveal-screen");
      if (q === 0) {
        await host.bringToFront();
        await sleep(PAUSE);
        await shot(host, "trivia-reveal");
      }
      await click(host, "advance");
    }
    await waitFor(host, "podium");
    await host.bringToFront();
    await sleep(PAUSE);
    await shot(host, "trivia-podium");
    await click(host, "back-to-lobby");

    // ---- Would You Rather ----
    console.log("[would-you-rather]");
    await waitFor(host, "start-wyr");
    await click(host, "start-wyr");
    for (let round = 0; round < 4; round++) {
      for (const page of everyone) await waitFor(page, "wyr-vote-screen");
      if (round === 0) {
        await host.bringToFront();
        await sleep(PAUSE);
        await shot(host, "wyr-vote");
      }
      await click(host, "vote-a");
      await click(max, "vote-a");
      await click(pip, "vote-b");
      await waitFor(host, "wyr-reveal-screen");
      if (round === 0) {
        await host.bringToFront();
        await sleep(PAUSE);
        await shot(host, "wyr-split-results");
      }
      await click(host, "advance");
    }
    await waitFor(host, "podium");
    await shot(host, "wyr-podium");
    await click(host, "back-to-lobby");

    // ---- Imposter Word ----
    console.log("[imposter]");
    await waitFor(host, "start-imposter");
    await click(host, "start-imposter");
    const roles = new Map();
    for (const [page, name] of [
      [host, "Zoe"],
      [max, "Max"],
      [pip, "Pip"],
    ]) {
      await waitFor(page, "imposter-discuss-screen");
      await click(page, "role-card");
      let isImposter = null;
      const deadline = Date.now() + WAIT.timeout;
      while (Date.now() < deadline && isImposter === null) {
        isImposter = await page.evaluate(() => {
          if (document.querySelector('[data-testid="imposter-badge"]')) return true;
          if (document.querySelector('[data-testid="secret-word"]')) return false;
          return null;
        });
        if (isImposter === null) await sleep(WAIT.polling);
      }
      if (isImposter === null) throw new Error(`[${name}] role card never revealed a role`);
      roles.set(name, { page, isImposter });
      console.log(`  ${name}: ${isImposter ? "IMPOSTER" : "crew"}`);
    }
    const imposterName = [...roles.entries()].find(([, r]) => r.isImposter)[0];
    const crewNames = [...roles.keys()].filter((n) => n !== imposterName);
    const imposterPage = roles.get(imposterName).page;
    await imposterPage.bringToFront();
    await sleep(PAUSE);
    await shot(imposterPage, "imposter-secret-role");
    const crewPage = roles.get(crewNames[0]).page;
    await crewPage.bringToFront();
    await shot(crewPage, "imposter-crew-word");

    await click(host, "start-vote");
    for (const name of crewNames) {
      const { page } = roles.get(name);
      await waitFor(page, "imposter-vote-screen");
      await click(page, `vote-player-${imposterName}`);
    }
    await waitFor(imposterPage, "imposter-vote-screen");
    await click(imposterPage, `vote-player-${crewNames[0]}`);
    await waitFor(host, "imposter-reveal-screen");
    await host.bringToFront();
    await sleep(PAUSE);
    await shot(host, "imposter-reveal");
    await click(host, "advance");
    await waitFor(host, "podium");
    await sleep(PAUSE);
    await shot(host, "party-final-scores");
    await click(host, "back-to-lobby");
    await waitFor(host, "room-code");
    await shot(host, "back-in-lobby");

    console.log(`\nDEMO PASS: ${shotCounter} screenshots in ${shotsDir}`);
  } catch (error) {
    for (const page of browser.__pages ?? []) {
      const name = pageNames.get(page) ?? "unknown";
      const file = path.join(shotsDir, `fail-${name.replace(/[^a-zA-Z]/g, "")}.png`);
      await page.screenshot({ path: file }).catch(() => {});
      console.error(`  failure screenshot: ${file}`);
    }
    throw error;
  } finally {
    await browser.close();
    killServer();
  }
}

main().catch((error) => {
  console.error(`\nDEMO FAIL: ${error.message}`);
  process.exit(1);
});
