#!/usr/bin/env node
// QA edge probes, independent of the developer's smoke suite.
// Usage: node probes.mjs <baseUrl>   (app must already be running)

const base = process.argv[2];
if (!base) {
  console.error("usage: node probes.mjs <baseUrl>");
  process.exit(2);
}

let passed = 0;
function assert(ok, label) {
  if (!ok) throw new Error(`ASSERT FAILED: ${label}`);
  passed += 1;
  console.log(`  ok: ${label}`);
}

const json = async (pathname, init, expectStatus) => {
  const res = await fetch(`${base}${pathname}`, init);
  const body = await res.json().catch(() => null);
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

async function makeParty() {
  const created = (await post("/api/rooms", { name: "Hana", emoji: "🦖" }, 201)).body.room;
  const code = created.code;
  const host = created.you;
  const p2 = (await post(`/api/rooms/${code}/join`, { name: "Iggy", emoji: "🍕" }, 200)).body.room.you;
  const p3 = (await post(`/api/rooms/${code}/join`, { name: "Juno", emoji: "🌵" }, 200)).body.room.you;
  return { code, host, p2, p3 };
}

async function main() {
  console.log("[probe: imposter tie vote → escape]");
  {
    const { code, host, p2, p3 } = await makeParty();
    await act(code, host, { type: "startGame", game: "imposter" });
    const roles = {};
    for (const id of [host, p2, p3]) roles[id] = (await view(code, id)).view.you;
    const ids = [host, p2, p3];
    const imposter = ids.find((id) => roles[id].role === "imposter");
    const crew = ids.filter((id) => id !== imposter);
    await act(code, host, { type: "imposter/startVote" });
    // Everyone votes in a cycle so the tally is 1-1-1: a tie, nobody accused.
    await act(code, ids[0], { type: "imposter/vote", suspect: ids[1] });
    await act(code, ids[1], { type: "imposter/vote", suspect: ids[2] });
    await act(code, ids[2], { type: "imposter/vote", suspect: ids[0] });
    const v = (await view(code, host)).view;
    assert(v.kind === "reveal", "tie vote still reaches reveal");
    assert(v.accused === null, "tie vote accuses nobody");
    assert(v.caught === false, "imposter escapes on a tie");
    assert(v.gained[imposter] === 250, "escaped imposter gains 250");
    assert(crew.every((id) => (v.gained[id] ?? 0) === 0), "crew gain nothing on escape");
  }

  console.log("[probe: WYR tie → both sides score]");
  {
    const { code, host, p2 } = await makeParty();
    await act(code, host, { type: "startGame", game: "wyr" });
    await act(code, host, { type: "wyr/vote", side: "a" });
    await act(code, p2, { type: "wyr/vote", side: "b" });
    // Third player abstains; host force-reveals a 1-1 tie.
    await act(code, host, { type: "wyr/advance" });
    const v = (await view(code, host)).view;
    assert(v.kind === "reveal" && v.countA === 1 && v.countB === 1, "1-1 tie revealed");
    assert(v.gained[host] === 25 && v.gained[p2] === 25, "both tied sides gain 25");
  }

  console.log("[probe: join mid-game rejected]");
  {
    const { code, host } = await makeParty();
    await act(code, host, { type: "startGame", game: "trivia" });
    await post(`/api/rooms/${code}/join`, { name: "Late", emoji: "🛸" }, 409);
    assert(true, "joining a running game returns 409");
  }

  console.log("[probe: partial answers on host force-reveal]");
  {
    const { code, host, p2 } = await makeParty();
    await act(code, host, { type: "startGame", game: "trivia" });
    await act(code, host, { type: "trivia/answer", choice: 0 });
    await act(code, p2, { type: "trivia/answer", choice: 1 });
    // Third player never answers; host reveals anyway.
    await act(code, host, { type: "trivia/advance" });
    const room = await view(code, host);
    const v = room.view;
    assert(v.kind === "reveal", "host can reveal with partial answers");
    const juno = room.players.find((p) => p.name === "Juno");
    assert((v.gained[juno.id] ?? 0) === 0, "unanswered player gains 0");
  }

  console.log("[probe: outsider actions rejected]");
  {
    const { code } = await makeParty();
    await act(code, "not-a-real-player", { type: "backToLobby" }, 403);
    assert(true, "unknown playerId gets 403");
    await json(`/api/rooms/${code}?player=not-a-real-player`, undefined, 403);
    assert(true, "unknown playerId cannot read the room");
  }

  console.log(`\nPROBES PASS (${passed} assertions)`);
}

main().catch((error) => {
  console.error(`\nPROBES FAIL: ${error.message}`);
  process.exit(1);
});
