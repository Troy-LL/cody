#!/usr/bin/env node
// End-to-end API smoke: boots `next start`, then plays a full round of all
// three games over HTTP as host + two players, asserting phases and scores.
// Exit 0 = all pass. Requires `npm run build` first.

import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

let passed = 0;
function assert(ok, label) {
  if (!ok) throw new Error(`ASSERT FAILED: ${label}`);
  passed += 1;
  console.log(`  ok: ${label}`);
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
    if (server.exitCode !== null) {
      throw new Error(
        `Server exited with code ${server.exitCode} before becoming ready. Output:\n${getOutput()}`,
      );
    }
    try {
      const res = await fetch(base);
      if (res.ok) return;
    } catch {
      // server not up yet
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`Server did not become ready at ${base}. Output:\n${getOutput()}`);
}

async function main() {
  const port = await freePort();
  const base = `http://127.0.0.1:${port}`;
  const server = spawn("node", ["node_modules/next/dist/bin/next", "start", "-p", String(port)], {
    cwd: appDir,
    stdio: ["ignore", "pipe", "pipe"],
  });
  let serverOutput = "";
  const collect = (chunk) => {
    serverOutput = (serverOutput + chunk).slice(-4000);
  };
  server.stdout.on("data", collect);
  server.stderr.on("data", collect);
  const getOutput = () => serverOutput.trim() || "(no output)";
  const kill = () => {
    if (!server.killed) server.kill("SIGTERM");
  };
  process.on("exit", kill);

  try {
    await waitForServer(base, server, getOutput);
    console.log(`Server ready at ${base}`);

    const json = async (pathname, init, expectStatus) => {
      const res = await fetch(`${base}${pathname}`, init);
      const body = await res.json();
      if (expectStatus !== undefined && res.status !== expectStatus) {
        throw new Error(`${pathname}: expected ${expectStatus}, got ${res.status}: ${JSON.stringify(body)}`);
      }
      return { status: res.status, body };
    };
    const post = (pathname, payload, expectStatus) =>
      json(
        pathname,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) },
        expectStatus,
      );
    const act = (code, playerId, action, expectStatus = 200) =>
      post(`/api/rooms/${code}/action`, { playerId, action }, expectStatus);
    const view = async (code, playerId) =>
      (await json(`/api/rooms/${code}?player=${playerId}`, undefined, 200)).body.room;

    // --- Room lifecycle ---
    console.log("\n[rooms]");
    const created = (await post("/api/rooms", { name: "Ava", emoji: "🦩" }, 201)).body.room;
    const code = created.code;
    const ava = created.you;
    assert(/^[A-Z]{4}$/.test(code), `room code is 4 letters (${code})`);
    assert(created.hostId === ava, "creator is host");

    const ben = (await post(`/api/rooms/${code}/join`, { name: "Ben", emoji: "🪩" }, 200)).body.room.you;
    const cleo = (await post(`/api/rooms/${code}/join`, { name: "Cleo", emoji: "🐙" }, 200)).body.room.you;
    assert((await view(code, ava)).players.length === 3, "three players in room");

    await post(`/api/rooms/${code}/join`, { name: "ava", emoji: "🦖" }, 409);
    assert(true, "duplicate name rejected with 409");
    await json(`/api/rooms/ZZZZ?player=${ava}`, undefined, 404);
    assert(true, "unknown room returns 404");
    await act(code, ben, { type: "startGame", game: "trivia" }, 403);
    assert(true, "non-host cannot start a game");

    // --- Trivia Blitz ---
    console.log("\n[trivia]");
    await act(code, ava, { type: "startGame", game: "trivia" });
    let v = (await view(code, ava)).view;
    assert(v.game === "trivia" && v.kind === "question" && v.index === 0, "trivia starts at question 1");
    assert(!("correct" in v), "correct answer is not leaked during question phase");

    const players = [
      { id: ava, name: "Ava" },
      { id: ben, name: "Ben" },
      { id: cleo, name: "Cleo" },
    ];
    for (let q = 0; q < 5; q++) {
      const choices = {};
      for (let i = 0; i < players.length; i++) {
        choices[players[i].id] = i; // Ava→0, Ben→1, Cleo→2
        await act(code, players[i].id, { type: "trivia/answer", choice: i });
      }
      v = (await view(code, ava)).view;
      assert(v.kind === "reveal", `question ${q + 1} auto-reveals once all answered`);
      for (const p of players) {
        const gained = v.gained[p.id] ?? 0;
        if (choices[p.id] === v.correct) {
          assert(gained >= 100, `${p.name} answered correctly and gained ${gained} (>=100)`);
        } else {
          assert(gained === 0, `${p.name} answered wrong and gained nothing`);
        }
      }
      await act(code, ava, { type: "trivia/advance" });
    }
    v = (await view(code, ava)).view;
    assert(v.game === "trivia" && v.kind === "final", "trivia reaches final after 5 questions");
    await act(code, ava, { type: "backToLobby" });
    assert((await view(code, ava)).view.game === "lobby", "back to lobby after trivia");

    // --- Would You Rather ---
    console.log("\n[would-you-rather]");
    await act(code, ava, { type: "startGame", game: "wyr" });
    const scoresBefore = Object.fromEntries((await view(code, ava)).players.map((p) => [p.id, p.score]));
    await act(code, ava, { type: "wyr/vote", side: "a" });
    await act(code, ben, { type: "wyr/vote", side: "a" });
    await act(code, cleo, { type: "wyr/vote", side: "b" });
    const wyrRoom = await view(code, ava);
    v = wyrRoom.view;
    assert(v.kind === "reveal" && v.countA === 2 && v.countB === 1, "vote split is 2 vs 1");
    assert(v.gained[ava] === 25 && v.gained[ben] === 25 && (v.gained[cleo] ?? 0) === 0, "majority side gains 25 each");
    const avaNow = wyrRoom.players.find((p) => p.id === ava);
    assert(avaNow.score === scoresBefore[ava] + 25, "score total updated");
    for (let round = 1; round < 4; round++) {
      await act(code, ava, { type: "wyr/advance" });
      for (const p of players) await act(code, p.id, { type: "wyr/vote", side: "a" });
    }
    await act(code, ava, { type: "wyr/advance" });
    v = (await view(code, ava)).view;
    assert(v.game === "wyr" && v.kind === "final", "wyr reaches final after 4 rounds");
    await act(code, ava, { type: "backToLobby" });

    // --- Imposter Word ---
    console.log("\n[imposter]");
    await act(code, ava, { type: "startGame", game: "imposter" });
    const roles = {};
    for (const p of players) {
      const pv = (await view(code, p.id)).view;
      assert(pv.game === "imposter" && pv.kind === "discuss", `${p.name} sees the discussion screen`);
      roles[p.id] = pv.you;
    }
    const imposter = players.find((p) => roles[p.id].role === "imposter");
    const crew = players.filter((p) => roles[p.id].role !== "imposter");
    assert(imposter && crew.length === 2, "exactly one imposter assigned");
    assert(!("word" in roles[imposter.id]), "imposter does not receive the secret word");
    assert(crew.every((p) => typeof roles[p.id].word === "string"), "crew members receive the secret word");

    await act(code, ava, { type: "imposter/startVote" });
    await act(code, crew[0].id, { type: "imposter/vote", suspect: imposter.id });
    await act(code, crew[1].id, { type: "imposter/vote", suspect: imposter.id });
    await act(code, imposter.id, { type: "imposter/vote", suspect: crew[0].id });
    v = (await view(code, ava)).view;
    assert(v.kind === "reveal" && v.caught === true && v.accused === imposter.id, "imposter caught by majority vote");
    assert(
      crew.every((p) => v.gained[p.id] === 100) && (v.gained[imposter.id] ?? 0) === 0,
      "correct accusers gain 100 each",
    );
    await act(code, ava, { type: "imposter/advance" });
    v = (await view(code, ava)).view;
    assert(v.game === "imposter" && v.kind === "final", "imposter reaches final");
    await act(code, ava, { type: "backToLobby" });
    assert((await view(code, ava)).view.game === "lobby", "back in the lobby with scores kept");

    console.log(`\nSMOKE PASS (${passed} assertions)`);
  } finally {
    kill();
  }
}

main().catch((error) => {
  console.error(`\nSMOKE FAIL: ${error.message}`);
  process.exit(1);
});
