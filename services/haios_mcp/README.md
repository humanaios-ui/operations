# HumanAIOS MCP Service v0.1.1 — local, bounded, read-only

This is an **installable MCP adapter** for the existing HumanAIOS **Unit Zero** Claude-based terminal agent (`tools/haios_cli.py`). It uses the same **HumanAIOS operations checkout** as its context source but does **not** execute the legacy CLI, run arbitrary commands, grant governance authority, or provide agent tools for writing to GitHub.

**State:** proposed software; unit tests are offline/synthetic. Deployment and external ChatGPT connection are **not verified**. The bridge is not a full Witness, persistent user-data plane, agent orchestrator, or general-purpose remote AI gateway.

## Tools

| MCP tool | What it does | Boundary |
|---|---|---|
| `haios_status` | Show local public file presence/hashes and configuration | No API/network call |
| `haios_read_document` | Read one of 7 explicitly allowed public governance files | No arbitrary paths; 16,000-character max; SHA-256 and truncation |
| `haios_talk` | Ask Claude using 3 named, bounded source files | No tool execution; model output, not canonical evidence |

`haios_talk` returns an opaque `session_id` for later turns. At most 8 sessions are held **in process memory only**, with 30-minute idle expiry. Process restart clears them. No user identity, account separation, durable memory, database, analytics, or audit-log mechanism is claimed. Treat it as a **single-operator pilot**; do not make it public.

The documents transmitted to Anthropic when you invoke `haios_talk` are `CURRENT.md`, `REGISTERED.md`, and `GOVERNANCE.md` (at most 6,000 characters each). The response reports exactly what was included and whether each document was clipped; it does not silently claim every repository file is loaded. Other documents can be read by explicitly calling `haios_read_document`, but are not transmitted to Anthropic by that read.

## Repair note (v0.1.1)

The previous installer accidentally required `START_HERE.md`, which may be absent from a valid operations checkout. The service and installer now require the canonical `CURRENT.md` and `REGISTERED.md` pair instead. Failed installs that exited at the usage message did not write credentials or create a LaunchAgent.

## Requirements

- Python 3.10+ and internet access to Anthropic API when calling `haios_talk`.
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

STDIO mode is designed to be **launched by an MCP client**, not chatted with manually. It emits protocol traffic to stdout. Run an MCP inspector/client against the executable to see its three tools. Configure your local MCP client with an explicit command and environment pointing to your operations checkout; do not put the API key in a world-readable settings file.

### macOS LaunchAgent (general background service)

A loopback-only HTTP service is also provided for user-owned, on-login operation:

```sh
# Run from the unpacked package, e.g. ~/Downloads/haios-mcp-service
bash scripts/install_macos.sh "$HOME/Desktop/HAIOS-Main/operations-staging"
```

The installer:
1. Creates a local Python virtual environment under `services/haios_mcp/.venv`.
2. Asks for **Anthropic key** and a separate **random HTTP bearer token** using macOS Keychain's interactive prompt; it does not save either secret in a `.env` or LaunchAgent plist. If asked for a token, generate a long random string with `openssl rand -hex 32` **in another private Terminal**. Do not paste it here or into a screenshot.
3. Writes `~/Library/LaunchAgents/ai.humanaios.mcp.plist` with only nonsecret absolute paths (permissions 0600).
4. Starts a per-user launchd job at `http://127.0.0.1:8768/mcp` with all non-loopback listeners disabled and bearer authorization required **before MCP routing**.

Keychain access under unattended launchd may require user approval/unlocked login Keychain. Check `~/Library/Logs/haios-mcp.log` for startup errors, **never raw secret values**. It does not start cloud hosting or expose a public endpoint.

Stop it:

```sh
launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/ai.humanaios.mcp.plist"
```

The HTTP bearer token is meant for **trusted local clients**. Never publish this HTTP port or expose it through a public reverse proxy; this prototype does not implement remote user OAuth, rate limiting, multi-tenant isolation, or a full security audit.

## Connecting to ChatGPT

**ChatGPT cannot connect directly to `localhost`.** Use a supported **Secure MCP Tunnel** with the **stdio mode**, where the tunnel client launches this service as a child process, or use an independently secured OAuth/HTTPS gateway developed separately. The stdio path avoids having to pass the HTTP bearer token through tunnel configuration.

Official documentation: https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

For a stdio tunnel, configure the **Keychain-backed launcher** (if installed through the macOS installer):

```sh
/bin/bash /ABSOLUTE/PATH/haios-mcp-service/scripts/launch_stdio_macos.sh \
  /ABSOLUTE/PATH/operations-staging \
  /ABSOLUTE/PATH/haios-mcp-service
```

This launcher reads `ANTHROPIC_API_KEY` from the user login Keychain and provides it only to the child process. Run it only as that user, with an unlocked Keychain. Other platforms may use an equivalent secret-manager mechanism. No tokens in command strings, printed output, or GitHub. Install/test the official tunnel client, associate it with the correct Platform organization and ChatGPT workspace, and add it through **ChatGPT Plugins → Add custom MCP server → Tunnel**. Access depends on your ChatGPT account/workspace and tunnel permissions; no tunnel is created by this package.

**Important:** ChatGPT’s custom remote connections do not accept an arbitrary static bearer token as an end-user credential. The local-only HTTP bearer implementation is not a substitute for OAuth on an Internet-facing service.

### Gate 5 checklist: tunnel identity, permissions, workspace scope, costs

The stdio launcher itself is verified (offline tests, and a live run as the exact
child process a tunnel client would spawn). What is **not** verified by this
package, because it is entirely on OpenAI's side of the boundary, is the tunnel
you point at it. Walk this before treating gate 5 as closed — current as of the
[Secure MCP Tunnel guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels);
re-check against that page, since tunnel mechanics are OpenAI's to change:

- **Identity**
  - [ ] You hold (or can get) a `tunnel_id` from **Platform tunnel settings**, created under the Platform organization that *should* own this HAIOS bridge — not a stray personal org.
  - [ ] The `tunnel-client` runtime API key used to run the client is scoped to that same organization and is treated as a secret (never pasted into chat, a command argument, a log, or a screenshot).
  - [ ] `tunnel-client doctor --profile <name> --explain` reports the client healthy, ready, and polling *before* you test from ChatGPT.
- **Permissions** (Platform tunnel RBAC and ChatGPT workspace access are two separate grants — both are required, neither implies the other)
  - [ ] Whoever **creates/edits** the tunnel has `Tunnels Read + Manage` on the Platform organization.
  - [ ] Whoever **runs `tunnel-client` or selects the tunnel** when adding the ChatGPT app has `Tunnels Read + Use`.
  - [ ] The target ChatGPT **workspace admin** has separately approved adding/using custom MCP servers in that workspace (a Platform org grant does not grant this).
- **Workspace scope**
  - [ ] The tunnel is explicitly associated with the **ChatGPT workspace** you intend to use it from, not only with the Platform organization — an org-only association won't make the tunnel appear when adding the custom MCP server in ChatGPT.
  - [ ] You know exactly which accounts/seats can see and invoke this connector once it's added in that workspace — a personal workspace keeps this single-operator (matching this package's design); a Team/Enterprise workspace means every member with connector access can trigger `haios_talk`, which this prototype's "single-operator pilot" framing assumes does not happen.
  - [ ] If an Enterprise/Edu account mapping doesn't auto-verify, you've gone through OpenAI's manual association override with your account team rather than forcing an unscoped association.
- **Costs**
  - [ ] You've checked your own OpenAI organization's billing/usage dashboard for the tunnel itself — this guide does not publish a tunnel price, so don't assume "free" without confirming there.
  - [ ] Separately from tunnel cost: every `haios_talk` call through the tunnel is a **real Anthropic API call** billed to whatever key is in `ai.humanaios.anthropic` in Keychain — workspace-wide connector access multiplies that exposure, not just tunnel traffic.
  - [ ] You've noted the documented tunnel limits (600 requests/min per tunnel+caller, 120s request deadline, 1,000 queued requests, 10 MiB per request/response) so a runaway client or workspace doesn't silently degrade or queue-stall before anyone notices.
- **Revocation path** (have this ready *before* you connect it, not after)
  - [ ] You know how to stop `tunnel-client` (kill the process) and how to delete/disable the tunnel in Platform tunnel settings.
  - [ ] You know how to unlink the custom MCP server from the ChatGPT workspace independently of stopping the tunnel client.
  - [ ] You know how to rotate the Keychain-held `ai.humanaios.anthropic` key if the tunnel path is ever suspected of being misused, without needing to touch the already-reviewed `launch_stdio_macos.sh`/`core.py` code.

## Security limits and evidence

- Allowlisted relative file **names only**; symbolic links and oversized files rejected.
- No arbitrary path, URL fetch, shell, process launching, SSH, source mutation, GitHub merge, or deployment tools.
- API/provider error messages are deliberately not echoed to clients.
- `haios_talk` transmits prompt/context to Anthropic; normal provider terms apply.
- Local service has no per-person login. Session identifiers are bearer-like handles; keep private.
- Document hashes are content digests, not signatures. They do not prove independently verified upstream state.
- Context files may change while the process is running. Each call reads them anew and reports current hashes.
- Model responses can be mistaken, contain unsafe suggestions, or misunderstand quoted documents. They are **not** ratification or verified service state.
- Exact MCP transport integration, macOS Keychain launch, and live Anthropic calls require environment-specific tests before admission.
- DNS-rebinding protection (hostile `Host`/`Origin` rejection on the HTTP transport) is enforced by the `mcp` SDK's own transport layer, not by this package's code; it is only as strong as staying current with that dependency.

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
