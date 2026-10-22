// Static safety contract for the browser-local collaboration cockpit.
import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../ui/intent-os-collaboration.html", import.meta.url), "utf8");
const js = await readFile(new URL("../ui/intent-os-collaboration.js", import.meta.url), "utf8");
let count = 0;
let passed = true;
function check(name, condition) {
  count += 1;
  passed &&= !!condition;
  console.log(`${condition ? "  ok  " : "  FAIL"} ${name}`);
}

check("page loads a same-origin module", /src="\/intent-os-collaboration\.js"/.test(html));
check("page exposes the five-step rehearsal", ["Verified login", "First-user onboarding", "Finder relationship", "Find work", "Introduction gate"].every((word) => html.includes(word)));
check("page states the non-execution boundary", html.includes("It does not send a message"));
check("client reads the verified session", js.includes('api("/api/session")'));
check("client mines only through the authenticated same-origin proxy", js.includes('api("/api/intent"'));
check("client requests bounded attestation receipts", js.includes('api("/api/collaboration/attest"'));
check("imported receipts are checked by the Worker", js.includes('api("/api/collaboration/verify"'));
check("local data is partitioned by pseudonymous actor", js.includes("session.actor_id") && js.includes("localStorage"));
check("untrusted service and candidate text is rendered as text", js.includes("textContent") && !js.includes("innerHTML") && !js.includes("insertAdjacentHTML"));
check("client never calls an email, messaging, contract, or payment endpoint", !/\/api\/(email|message|contract|payment|send)/i.test(js));
check("real collaborator names and private commission values are absent from public UI", !/David|Empirica|5\s*[–-]\s*10/i.test(html + js));
check("finder and service owner cannot share one actor", js.includes("The finder cannot confirm the service owner side"));

console.log(`${count} checks · COLLABORATION UI ${passed ? "PASS" : "FAIL"}`);
process.exit(passed ? 0 : 2);
