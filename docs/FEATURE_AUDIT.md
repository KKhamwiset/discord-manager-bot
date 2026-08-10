# Feature audit

Audit basis: repository baseline `447ed18` and the permission/API/backup hardening implemented in this change set. Baseline defects are labeled separately from current change-set behavior. “Implemented” means the code path is present; deployment-specific Discord, MongoDB, Hermes, and recovery behavior still requires the staged verification described in the README.

## Status legend

| Mark | Meaning |
| --- | --- |
| Working | The main path is implemented and has a coherent caller/context model. |
| Context-limited | The feature works only in a specific Discord context, external service, or configuration. |
| Incomplete | A user-visible path exists, but the data flow or behavior is not end to end. |
| Unsafe | The path can bypass intended authorization, expose sensitive data, or perform an unexpectedly broad/destructive action. |

Prefix commands accept `b`, `B`, `t`, `T`, or a bot mention. “Hybrid” means both prefix and slash registration; “prefix” means message command only. All server commands are also subject to the `guild_config` channel policy. The default policy allows all channels; whitelist entries can allow all commands, allow only selected commands, or exclude selected commands.

## Caller and surface matrix

| Caller or subsystem | What works now | Boundaries and defects | Target behavior |
| --- | --- | --- | --- |
| Normal user in DM | General utilities that do not touch guild state: `ping`, `hello`, `xdd`, `test`, `rick`, `info`, `wd`, and `help`. Student-ID slash writes do not themselves read a guild. Server-scoped prefix/hybrid commands now return an explicit server-only response. | Baseline server commands dereferenced `ctx.guild`, member roles, or guild channels and often raised errors. `xdd` remains unsafe content; `test` remains an unfinished visible command. | Keep fail-closed context checks and make help filter or label commands by context. |
| Normal user in a server | Read-only utilities, schedule reads/writes, restaurant choice/listing, and role listing, subject to channel policy and external dependencies. | Academic reads and student-ID writes still use incompatible schemas. Several actions still depend on the bot's own Discord permissions and hierarchy. | Implemented permission target: administration mutations use native Discord permissions; ordinary users retain read/self-service paths. Add consistent bot-permission diagnostics and audit. |
| Member with Manage Guild | Native Manage Server now authorizes channel-policy administration, restaurant-list mutation, `id`, `pause`, and `resume`. Bot owners and administrators also pass this check. | Baseline checked for a role literally named `Moderator`. The current command changes are not persisted to an audit log, and maintenance state remains in memory. | Native authorization and explicit DM rejection are implemented; durable audit remains roadmap work. |
| Member with Manage Roles | Native Manage Roles now authorizes role create/delete/assign/remove. Caller/target/role and bot hierarchy checks run before mutations. | Discord still requires the bot member to have Manage Roles and adequate hierarchy. Deletion remains immediate with no confirmation/audit. | Permission and hierarchy target is implemented; confirmation and durable audit remain. |
| Member with Manage Threads | Native Manage Threads now authorizes adding a user to the configured thread and running the hidden thread cleanup command. | Both commands are hard-wired to `TRIO`; `thread-nuke` has a source-coded preservation allowlist and removes every other non-bot member. | Permission/context target is implemented; dry-run, confirmation, DB-backed preservation, and audit are still required before treating bulk removal as safe. |
| Bot owner | Manual encrypted `backup` and `restart`; owner status also bypasses the native caller-permission checks. | Discord role hierarchy still cannot be bypassed. `restart` depends on the host Hermes CLI. The baseline backup uploaded plaintext ZIP data and read deprecated `MAIN_DB`. | Manual encrypted backup and owner-only restart are implemented; recovery must be tested offline before scheduling is enabled. |
| Dashboard/API user | Public overview/command inventory and Discord OAuth login. Dashboard authorization and command/channel mutations now require a valid JWT plus a live bot-authoritative Manage Server, Administrator, or bot-owner result; permission-authority outages fail closed. | The command toggle still only writes `command_config`; the bot neither loads nor enforces it, and the list response reports the live in-memory flag instead of the stored value. | Strong `JWT_SECRET` and one live permission authority are implemented. Wire runtime toggles and audit writes. |
| Heartbeat agent | A bot-authored message containing `HEARTBEAT_EMOJI` in the configured channel refreshes liveness; timeout changes the presence to sleeping and recovery restores it. | The system relies on an external Hermes cron/message path and Discord message-content access. Defaults and a gateway-specific author exception are embedded in code. Dashboard “heartbeat” is inferred from bot readiness rather than heartbeat age. | Explicit deployment configuration, observable last-seen/age, portable restart integration, and separate ready-versus-heartbeat states. |
| Backup scheduler | On the server instance, the daily task creates and delivers an encrypted `.mbak` only when `BACKUP_ENABLED=true` and configuration is valid. | Baseline started solely from `INSTANCE`, read `MAIN_DB`, shell-built `mongoexport`, wrote plaintext collection JSON and ZIP files in the working directory, and uploaded the plaintext ZIP. Backup history and automated restore verification still do not exist. | Fixed target is implemented: canonical live DB selection with legacy fallback, explicit enable and server-instance gates, credential-protected exporter configuration, base64 X25519 public-key encryption with no plaintext fallback, temporary-directory cleanup, operator-visible failure codes, and digest-pinned offline recovery tooling. |

## Command inventory

### Core and information

| Command and aliases | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `id` (intended `idc`) | Hybrid | Manage Guild, server | Context-limited. The decorator uses `alias=["idc"]` rather than `aliases=["idc"]`, so `idc` is not registered. It DMs the current channel/thread ID. |
| `ping` | Hybrid | Anyone, DM/server | Working; reports Discord websocket latency. |
| `hello` | Prefix | Anyone, DM/server | Working; simple greeting. |
| `xdd` (`xdx`) | Hybrid | Anyone, DM/server | Unsafe. The random response list contains inappropriate racial content; remove that content before promoting the command. |
| `test` | Hybrid | Developer only | Incomplete and visibly listed. It sends the fixed text `amath 10+20`; hide or remove it from production command sync. |
| `rick` (`ing`) | Hybrid | Anyone, DM/server | Context-limited to custom emoji availability; amount parsing silently returns on non-integers and clamps out-of-range values to 10. |
| `info` | Prefix | Anyone, DM/server | Working; shows bot instance, latency, server/DM, and cached user count. |
| `wd` | Hybrid | Anyone, DM/server | Context-limited to a third-party currency endpoint. It uses synchronous `requests.get` in the event-loop thread, so a slow request can stall bot handling. |
| `help` | Hybrid | Anyone, DM/server | Incomplete. It enumerates loaded commands but does not filter by caller permission, guild/DM context, channel policy, or runtime toggle state. |

### Academic schedule

| Command and aliases | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `addstdid` | Slash | Self-service, DM/server | Incomplete. Writes one `std_id` document keyed by numeric `user_id`; response is ephemeral. No format validation or field encryption is present. |
| `edit_stdid` | Slash | Self-service, DM/server | Incomplete for the same schema and data-protection reasons as `addstdid`. Naming is inconsistent with `addstdid`. |
| `examschedule` (`ex`, `exam`) | Prefix | Normal server user | Incomplete. Reads a guild aggregate document and calls the configured academic endpoint; it cannot consume the documents written by `addstdid`/`edit_stdid`. |
| `addclass` (`asch`, `ac`) | Prefix | Normal server user | Context-limited interactive write to the caller's schedule. Requires MongoDB and component interactions. |
| `editclass` (`ec`, `esch`) | Prefix | Normal server user | Context-limited interactive edit; assumes guild context and existing schedule data. |
| `myschedule` (`msch`, `mc`) | Prefix | Normal server user | Context-limited read of self or a resolved member; assumes guild context. |
| `delclass` (`delsch`, `dc`) | Prefix | Normal server user | Context-limited interactive delete; only the first 25 generated options can be selected. |

Academic schema defect: the write path stores `{user_id, std_id}` as an individual document in `std_id`, while `examschedule` looks up `{guild_id}` and scans a `member_id` array containing `{user_id, std_id}`. These are different schemas, so a successful student-ID write does not make the exam read path work. Repair requires one canonical schema and a migration/read-compatibility plan; it does not justify deleting legacy records.

### Restaurants

| Command and aliases | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `arand` (`asr`, `asrand`, `assr`) | Prefix | Manage Guild, server | Context-limited mutation. Invocation alias selects standard versus special type; the naming is opaque. |
| `nrand` (`sr`, `ssr`) | Prefix | Normal server user | Working with configured restaurant data. Exclusions are accepted only through a colon-shaped parameter, and empty-result copy always says “standard” even for `ssr`. |
| `lrand` (`ls`) | Prefix | Normal server user | Working list view with chunked embeds. Footer examples assume the `t` prefix. |
| `drand` (`dres`) | Prefix | Manage Guild, server | Context-limited exact-name deletion. No history, soft delete, or confirmation. |

### Roles

| Command and aliases | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `createrole` (`cr`, `makerole`) | Prefix | Manage Roles, server | Native Manage Roles and bot-permission checks are implemented. New roles are created below the bot; Discord API failures still depend on deployment permissions. |
| `deleterole` (`dr`, `delrole`) | Prefix | Manage Roles, server | Native permission and hierarchy checks are implemented, but deletion is still immediate without confirmation or audit. |
| `listrole` (`lr`, `roles`) | Prefix | Normal server user | Working read-only listing for a guild, member, or role; server-only. |
| `removerole` (`removerolefromuser`, `rr`) | Prefix | Manage Roles, server | Native Manage Roles plus caller, target-member, target-role, and bot hierarchy checks are implemented. |
| `addrole` (`arole`, `ar`) | Prefix | Manage Roles, server | The baseline had no guard. Native Manage Roles and hierarchy checks are now implemented. |

Discord role operations always require the bot member itself to have Manage Roles and to sit above every target role. Caller permission alone is insufficient.

### Channels and threads

| Command and aliases | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `add-user-to-thread` (`aut`) | Hybrid | Manage Threads, server | Context-limited to the thread ID in `TRIO`. On success it also appends the user ID to `guild_config.tnt_allowed_users`, but `thread-nuke` does not read that field. |
| `thread-nuke` (`nt`) | Hybrid, hidden | Manage Threads, configured thread | Unsafe bulk action. It uses a source-coded preservation set, not `tnt_allowed_users`, and has no confirmation, dry run, or audit record. |
| `channel-remove` | Hybrid | Manage Guild, server | Working DB mutation. Removing the last configured channel reverts the guild to allow-all, which is fail-open and should be explicit to the operator. |
| `command-allow-all` | Hybrid | Manage Guild, server | Context-limited. In whitelist mode it adds one command to every cached text channel and active thread; the name implies changing global mode but does not. |
| `command-add` | Hybrid | Manage Guild, server | Context-limited. It cannot bootstrap an empty/default config and stores the supplied alias/name rather than consistently storing the qualified canonical name. |
| `channel-configure` | Hybrid | Manage Guild, server | Working core policy write for `all`, `only`, or `exclude`, subject to command-name validation. User-facing examples still reference obsolete command names/prefixes. |
| `channel-list` | Hybrid | Manage Guild, server | Working read of resolvable configured channels; stale channel IDs are silently omitted. |

The bot's global check enforces `guild_config` at invocation time, so dashboard channel edits can affect runtime policy. This is distinct from the dashboard command toggle, which is DB-only and has no runtime enforcement.

### Maintenance, heartbeat, and backup

| Command or process | Surface | Intended caller/context | Status and evidence |
| --- | --- | --- | --- |
| `pause` | Hybrid | Manage Guild, matching server instance | Context-limited in-memory maintenance mode. It is lost on restart and only `resume` bypasses the paused check. |
| `resume` | Hybrid | Manage Guild, matching server instance | Working for the in-memory flag; restores a hard-coded instance-specific presence rather than reconciling heartbeat state. |
| `restart` | Hybrid | Bot owner, matching server instance | Context-limited and not portable. It assumes `hermes gateway restart` exists, uses Windows-specific background flags only on Windows, does not consume piped output, and is not a robust detached service-manager integration. |
| Heartbeat monitor | Event listener and two-minute task | Configured Hermes/Discord agent | Context-limited. Watches one channel/emoji, marks stale status idle, and restores online status when a current heartbeat is observed. |
| `backup` | Prefix | Bot owner | Encrypted manual run is implemented and intentionally independent of `BACKUP_ENABLED`, enabling staged recovery testing while scheduling is disabled. |
| Scheduled backup | Daily task | Server instance with backup enabled | Requires both `INSTANCE=server` and `BACKUP_ENABLED=true`, the bot's selected canonical database, a destination channel with send/attach permissions, and a strict-base64 X25519 public key. |

## Dashboard and API inventory

| Endpoint or page | Access in code | Status |
| --- | --- | --- |
| `GET /`, `GET /health` | Public | Working basic API metadata/health; health does not verify MongoDB or bot connectivity. |
| `GET /api/stats/overview` | Public | Context-limited aggregation of bot readiness and cached guild metadata. |
| `GET /api/auth/login`, `GET /api/auth/callback` | Public OAuth flow | Callback token logging from the baseline is removed. The dashboard still stores its JWT in `localStorage`, increasing the impact of any script injection. |
| `GET /api/auth/me`, `POST /api/auth/logout` | Any valid JWT | Logout is stateless and does not revoke the token. |
| `GET /api/auth/authorized-user` | Any valid JWT plus live permission lookup | Returns the existing `{authorized: boolean}` shape from current Discord Manage Server, Administrator, or bot-owner state; authority outages fail closed. The legacy `authorize_user` collection remains untouched but is no longer consulted. |
| `GET /api/commands/` | Public at API layer | Working live command inventory; the dashboard passes a token but the route does not require one. |
| `PATCH /api/commands/<name>` | Valid JWT plus live Manage Server/Administrator/bot owner | Authorization now fails closed through the bot permission authority. Still incomplete: it writes `command_config.enabled` only and the bot does not load or enforce it. |
| `GET /api/channels/` | Valid JWT plus live Manage Server/Administrator/bot owner | Working configured-channel list, dependent on the bot permission authority and internal channel-name resolution. |
| `PATCH /api/channels/<id>` | Valid JWT plus live Manage Server/Administrator/bot owner | Server-side authorization is implemented. The DB update is runtime-relevant because the bot's channel check reads this policy. |
| Landing page | Public | Working status preview and Discord sign-in. |
| Dashboard overview | Logged-in user | Working read view; management links are visually gated by the same live permission authority as API writes. |
| Commands page | Logged-in user; toggle control and API write live-permission-gated | Incomplete because the stored toggle has no runtime effect. |
| Channels page | Logged-in user with live Manage Server/Administrator/bot owner | Server authorization and denied/unavailable UI states are implemented; edits remain unaudited. |

`JWT_SECRET` is mandatory. The API now fails startup when it is absent; the baseline's forgeable `dev-secret-key` fallback has been removed.

## Data handling and removed features

- Student IDs are live sensitive fields needed for the external exam lookup. They are currently stored as plaintext. Future protection must use field encryption for the recoverable value; hashing is a separate control and cannot replace encryption when the original ID must be sent to the academic service.
- Backup encryption protects exported artifacts, not the live MongoDB fields.
- Recipient public-key encryption authenticates encrypted frames but not the sender. Offline recovery must pin the ciphertext SHA-256 copied from the trusted bot-authored Discord message before decrypting.
- The homework manager and commands are removed and must not be reintroduced by schedule work.
- If a legacy homework collection still exists, preserve it without deletion. Any archive or deletion requires an explicit retention/migration decision outside this roadmap.

## Prioritized roadmap

1. Runtime toggles / backup history / audit / schema repair / context help.
2. Today / nextclass / reminders / calendar / data controls.
3. Live student-ID field encryption separate from hashing.
4. Restaurant polls / history / self-role / feedback.
