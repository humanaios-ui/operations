# HumanAIOS MCP Service v0.2.0 (Z1 draft) — local, bounded, read-only

This is an **installable MCP adapter** for the existing HumanAIOS **Unit Zero** Claude-based terminal agent (`tools/haios_cli.py`). It uses the same **HumanAIOS operations checkout** as its context source but does **not** execute the legacy CLI, run arbitrary commands, grant governance authority, or provide agent tools for writing to GitHub.

**State:** proposed software; unit tests are offline/synthetic. Deployment and external ChatGPT connection are **not verified**. The bridge is not a full Witness, persistent user-data plane, agent orchestrator, or general-purpose remote AI gateway.

## What v0.2 means by "Witness"

The intended transfer is **Unit Zero's conversational Witness role and bounded self-model**, not migration of Claude model state, consciousness, or old chat history. HumanAIOS-as-organism is a design metaphor; subjective awareness is **NOT_ESTABLISHED**. The local context files are *manually copied snapshots* and not live synchronized GitHub state. The Phase-0 Witness service obligations are authoritative for research interpretation; no production consent/data plane is authorized. See [`WITNESS_INTEGRATION_V0_2.md`](WITNESS_INTEGRATION_V0_2.md).

The Anthropic Messages API now uses **streaming** after the operator verified that a full-context nonstreaming request raised `ReadError` while a streamed request succeeded on the Mac. One isolated **operator-reported candidate E2** MCP call passed on 2026-11-19 using source commit `1c40658814853ff7a721567c524929d8b7795051`; it is **not** independent attestation, an installed service, or deployment. All three public documents were clipped to the bounded model context. See the receipt on PR #1012. A response SHA-256 is an unsigned content digest, not an attestation.

**Resource Miner adapter:** Optional, disabled by default. Set `HAIOS_RESOURCE_MINER_ORIGIN=http://127.0.0.1:8766` **only after running and verifying a compatible public Resource Miner listener on that port**, then restart the LaunchAgent to load that nonsecret environment setting. Do not add private objectives, applicant identifiers or credentials to this public query. The tool issues snapshot-only public candidate queries; it will never run scans, private HackerOne API discovery or grant eligibility evaluation. Never expose the local listener publicly. No manual credential placement in plists is required.

## Tools

| MCP tool | What it does | Boundary |
|---|---|---|
| `haios_status` | Show local public file presence/hashes and configuration | No API/network call |
| `haios_read_document` | Read one of 7 explicitly allowed public governance files | No arbitrary paths; 16,000-character max; SHA-256 and truncation |
| `haios_talk` | Stream Claude using 3 named, bounded source files | No tool execution; model output, not canonical evidence |
| `haios_self_model` | Enumerate actual local service capabilities, hashes, absence and limits | No sentience/personhood claim; no execution |
| `haios_find_resources` | Optional **public snapshot-only** Resource Miner query | Explicit objective, allowlisted origin/fields; no private sources, eligibility or scans |

`haios_talk` returns an opaque `session_id` for later turns. At most 8 sessions are held **in process memory only**, with 30-minute idle expiry. Process restart clears them. No user identity, account separation, durable memory, database, analytics, or audit-log mechanism is claimed. Treat it as a **single-operator pilot**; do not make it public.

The documents transmitted to Anthropic when you invoke `haios_talk` are `CURRENT.md`, `REGISTERED.md`, and `GOVERNANCE.md` (at most 6,000 characters each). The response reports exactly what was included and whether each document was clipped; it does not silently claim every repository file is loaded. Other documents can be read by explicitly calling `haios_read_document`, but are not transmitted to Anthropic by that read.

## Repair note (v0.1.1)

The previous installer accidentally required `START_HERE.md`, which may be absent from a valid operations checkout. The service requires the canonical `CURRENT.md` and `REGISTERED.md` pair; the macOS installer additionally copies `GOVERNANCE.md` as the third required context file. Failed installs that exited at the usage message did not write credentials or create a LaunchAgent.

## Requirements

- Python 3.13 on the operator's Intel Mac for the reviewed isolated pilot (Python 3.15 failed a `cryptography` source build); provider API access is used **only** after explicit per-request consent.
- An existing operations checkout containing `CURRENT.md` and `REGISTERED.md` as regular files. `START_HERE.md` is optional.
- Anthropic API key held **locally**, never in the repository.
- Python MCP v2 and Anthropic SDK (installed with this package). `mcp>=2.2,<3` matches the operations repository's declared SDK major; consult `tools/requirements.txt` before a future upgrade.

## Standalone use versus repository use

This package has no runtime requirement to be placed inside a git repository. You can unpack the archive anywhere writable by your user and pass the absolute operations checkout through `--repo`. For a repo-backed code review, it lives at `services/haios_mcp/` on its draft branch. Do not overwrite local dirty files.

## Install (portable; local MCP stdio)

For a repository installation, from `operations-staging` root (or replace the path with an unpacked standalone copy):

```sh
python3 -m venv .venv-haios-mcp
.venv-haios-mcp/bin/python -m pip install -e services/haios_mcp
export HAIOS_REPO_ROOT="$PWD"
# In an interactive Terminal where ANTHROPIC_API_KEY is already set:
.venv-haios-mcp/bin/haios-mcp --transport stdio
```

STDIO mode is designed to be **launched by an MCP client**, not chatted with manually. It emits protocol traffic to stdout. Run an MCP inspector/client against the executable to see its five tools. Configure your local MCP client with an explicit command and environment pointing to your operations checkout; do not put the API key in a world-readable settings file.

### Reversible INTENT-OS E0.3 pilot staging (preferred; no activation)

For the operator's **existing E0.3 checkout**, first inspect and then explicitly stage the v0.2 candidate. The staging command verifies Python 3.13 and the three pinned public document SHA-256 values from the operator's E2 receipt. It creates isolated Application Support directories only after `--stage`, installs an isolated venv, and **does not start a process**, register a LaunchAgent, change E0.3, fetch private data, or make an Anthropic call:

```sh
bash services/haios_mcp/scripts/stage_e03_pilot_macos.sh --preflight "$HOME/intent-os-e0-3-reconciled-test"
# Separate human approval + independent review required before the next command:
# bash services/haios_mcp/scripts/stage_e03_pilot_macos.sh --stage "$HOME/intent-os-e0-3-reconciled-test"
# Read-only ownership and any-port process checks (safe on existing staged pilot):
bash services/haios_mcp/scripts/stage_e03_pilot_macos.sh --rollback-check
# After separate explicit approval, removes only two exact-marker pilot folders:
# bash services/haios_mcp/scripts/stage_e03_pilot_macos.sh --rollback
```

**Rollback safety on this review branch:** `--rollback-check` never removes files and requires Python 3.13. It checks exact marker bytes and rejects linked pilot paths. It asks macOS `lsof` for open files/working directories in either pilot folder (independent of TCP port), checks port 8768, and scans `ps` for any Witness or pilot path; unavailable or ambiguous checks fail closed. `--rollback` runs the guard twice before deleting only the two marked folders. It is **not atomic with process startup**, and still needs independent native-macOS validation before release. Never use `--rollback` to test on the operator's successful staged installation. The fixture regression suite uses disposable temporary HOME paths and must never touch production.

**Partial staging:** if `--stage` stops after both ownership markers are written, rerunning `--stage` intentionally refuses; inspect and run `--rollback-check` first. If either marker is absent, the script refuses automatic deletion and requires manual review. The three public document SHA-256 pins intentionally bind only the recorded E2 snapshot; newer `REGISTERED.md` cannot be silently substituted. No automatic public-snapshot refresh is authorized.

A staged copy cannot answer through INTENT-OS until a separate consented launch, Keychain/credential setup and E0.3 bridge integration have passed review. The existing bridge is off by default and currently does not supply the new `consent=True` MCP argument; **do not enable it** until a separate compatible bridge patch has passed tests. The `haios_talk` tool now rejects requests missing `consent=True` before any provider call; this flag is a client attestation, **not independent proof** of a human click. An approved client must show fresh explicit human consent before each call. No automatic retries or scheduled model calls are authorized.

### macOS LaunchAgent (general background service; not for E0.3 pilot without separate approval)

A loopback-only HTTP service is also provided for user-owned, on-login operation, but the legacy installer **requires explicit Python 3.13** and is **not the reversible E0.3 pilot path**. Do not run it until a separate human installation decision and macOS security review:

```sh
# Run from the unpacked package, e.g. ~/Downloads/haios-mcp-service
bash scripts/install_macos.sh "$HOME/Desktop/HAIOS-Main/operations-staging"
```

The installer:
1. Copies the service into `~/Library/Application Support/HumanAIOS/mcp`, and only the three public governance documents into a protected local **snapshot** at `~/Library/Application Support/HumanAIOS/context` (0600). This avoids Downloads/Desktop background-access blocks. Creates a Python virtual environment in `.../mcp/.venv` and refuses to mutate an already loaded LaunchAgent.
2. Asks for **Anthropic key** and a separate **random HTTP bearer token** using macOS Keychain's interactive prompt; it does not save either secret in a `.env` or LaunchAgent plist. If asked for a token, generate a long random string with `openssl rand -hex 32` **in another private Terminal**. Do not paste it here or into a screenshot.
3. Writes `~/Library/LaunchAgents/ai.humanaios.mcp.plist` with only nonsecret absolute paths (permissions 0600).
4. Starts a per-user launchd job from the stable Application Support directory at `http://127.0.0.1:8768/mcp` with all non-loopback listeners disabled and bearer authorization required **before MCP routing**.

Keychain access under unattended launchd may require user approval/unlocked login Keychain. Check `~/Library/Logs/haios-mcp.log` for startup errors, **never raw secret values**. Changes to `CURRENT.md`/`REGISTERED.md`/`GOVERNANCE.md` in the original checkout are **not** automatically synchronized to the snapshot; refresh it only by an approved, operator-controlled procedure. The code and secrets are not copied from the original checkout at runtime. It does not start cloud hosting or expose a public endpoint.

Stop it:

```sh
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/ai.humanaios.mcp.plist"
```

The HTTP bearer token is meant for **trusted local clients**. Never publish this HTTP port or expose it through a public reverse proxy; this prototype does not implement remote user OAuth, rate limiting, multi-tenant isolation, or a full security audit.

## Controlled v0.2 MCP authentication test (no deployment)

From a separate, unpacked v0.2 candidate bundle, run:

```sh
"$HOME/Library/Application Support/HumanAIOS/mcp/.venv/bin/python" \
  /ABSOLUTE/PATH/TO/haios-mcp-service/scripts/smoke_auth_macos.py
```

This test uses the **already-installed MCP dependencies**, but loads v0.2 source
from its unpacked candidate directory with `PYTHONPATH` in an isolated child.
It binds an ephemeral **127.0.0.1** port, proves that missing and incorrect
bearer credentials return HTTP 401, authenticates from macOS Keychain,
initializes the MCP client, checks the exact five v0.2 tools, calls
`haios_status` and `haios_self_model`, prints a timestamp and unsigned
SHA-256 digest, then terminates only the temporary child process.
It does **not** reinstall software, change LaunchAgent settings, use the Claude
API, transmit a prompt, or enable Resource Miner. v0.1.1 can keep running.
The resulting receipt proves local client observation, not a public tunnel or
production readiness. Never paste secrets or session IDs into an issue.

## Connecting to ChatGPT

**ChatGPT cannot connect directly to `localhost`.** Use a supported **Secure MCP Tunnel** with the **stdio mode**, where the tunnel client launches this service as a child process, or use an independently secured OAuth/HTTPS gateway developed separately. The stdio path avoids having to pass the HTTP bearer token through tunnel configuration.

Official documentation: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

For a stdio tunnel, configure the **Keychain-backed launcher** (if installed through the macOS installer):

```sh
/bin/bash "$HOME/Library/Application Support/HumanAIOS/mcp/scripts/launch_stdio_macos.sh" \
  "$HOME/Library/Application Support/HumanAIOS/context" \
  "$HOME/Library/Application Support/HumanAIOS/mcp"
```

This launcher reads `ANTHROPIC_API_KEY` from the user login Keychain and provides it only to the child process. Run it only as that user, with an unlocked Keychain. Other platforms may use an equivalent secret-manager mechanism. No tokens in command strings, printed output, or GitHub. Install/test the official tunnel client, associate it with the correct Platform organization and ChatGPT workspace, and add it through **ChatGPT Plugins → Add custom MCP server → Tunnel**. Access depends on your ChatGPT account/workspace and tunnel permissions; no tunnel is created by this package.

**Important:** ChatGPT’s custom remote connections do not accept an arbitrary static bearer token as an end-user credential. The local-only HTTP bearer implementation is not a substitute for OAuth on an Internet-facing service.

## Security limits and evidence

- Allowlisted relative file **names only**; symbolic links and oversized files rejected.
- No arbitrary path, URL fetch, shell, process launching, SSH, source mutation, GitHub merge, or deployment tools. `haios_find_resources` is the one **explicit exception**: it can issue a bounded HTTP POST to a fixed `127.0.0.1` Resource Miner `/api/intent` endpoint, only when the operator opts in.
- API/provider error messages are deliberately not echoed to clients.
- `haios_talk` transmits prompt/context to Anthropic; normal provider terms apply.
- Local service has no per-person login. Session identifiers are bearer-like handles; keep private.
- Document hashes are content digests, not signatures. They do not prove independently verified upstream state.
- Context files may change while the process is running. Each call reads them anew and reports current hashes.
- Model responses can be mistaken, contain unsafe suggestions, or misunderstand quoted documents. They are **not** ratification or verified service state.
- Exact MCP transport integration, macOS Keychain launch, and live Anthropic calls require environment-specific tests before admission.

### Offline tests

```sh
PYTHONPATH=services/haios_mcp/src python3 -m unittest discover -s services/haios_mcp/tests -v
python3 -m compileall -q services/haios_mcp/src
```

No network, credentials, or installed MCP SDK are needed for offline core tests.

## Readiness gates

1. Independent code + security review (including CodeRabbit).
2. Test SDK v2 handshake and `tools/list` via MCP Inspector against the exact branch.
3. Test Claude API conversation, clipped document claims, session expiry, and restart loss.
4. Test HTTP unauthenticated denial and hostile `Origin`/`Host` requests on the actual macOS runtime.
5. Review private tunnel identity, permissions, workspace scope, and costs.
6. Human-controlled governance admission before merge or production deployment.

**Authority: NONE.** Installing this service does not authorize a user account scan, resource claim, model evaluation, auto-execution, private data upload, or use as a production personal Witness.
