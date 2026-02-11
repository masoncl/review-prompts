# NFSD Client State Transitions

Incorrect client state transitions cause protocol violations (client
receives unexpected errors), resource leaks (courtesy clients
accumulate without expiry, exhausting memory), or premature state
destruction (active client's stateids destroyed while still in use).

## Client Lifecycle

`struct nfs4_client` is created by `SETCLIENTID` (NFSv4.0) or
`EXCHANGE_ID` (NFSv4.1+). Confirmation is tracked by the
`NFSD4_CLIENT_CONFIRMED` flag in `cl_flags`, not by `cl_state`.

The `cl_state` field (defined in `fs/nfsd/state.h`) tracks the
client's lease state:

| State | Meaning | Set by |
|-------|---------|--------|
| `NFSD4_ACTIVE` | Confirmed, active (default) | Initial state |
| `NFSD4_COURTESY` | Lease expired, kept as courtesy | `nfs4_get_client_reaplist()` |
| `NFSD4_EXPIRABLE` | Courtesy client to be expired due to conflict | `nfs4_laundromat()`, `try_to_expire_client()` |

Transitions are: `NFSD4_ACTIVE` → `NFSD4_COURTESY` →
`NFSD4_EXPIRABLE` → destroyed.

## Confirmation (cl_flags)

A client starts unconfirmed. `NFSD4_CLIENT_CONFIRMED` is set in
`cl_flags` after successful `SETCLIENTID_CONFIRM` (v4.0) or
`CREATE_SESSION` (v4.1+). Other `cl_flags`:

- `NFSD4_CLIENT_STABLE` — client on stable storage.
- `NFSD4_CLIENT_RECLAIM_COMPLETE` — client has completed reclaim.
- `NFSD4_CLIENT_CB_UPDATE` / `NFSD4_CLIENT_CB_KILL` — callback
  state management flags.

## Courtesy Client Handling

When a client's lease expires but it still holds state (open files,
delegations, locks), the server transitions it to `NFSD4_COURTESY`
rather than immediately destroying it. This allows the client to
reclaim state if it reconnects.

`nfs4_get_client_reaplist()` in `fs/nfsd/nfs4state.c` transitions
`NFSD4_ACTIVE` clients with expired leases and no active RPCs
(`cl_rpc_users == 0`) to `NFSD4_COURTESY`.

Courtesy clients are promoted to `NFSD4_EXPIRABLE` via
`try_to_expire_client()` when:
- A lease/lock/share reservation conflict arises with the courtesy
  client's state.
- The transition uses `cmpxchg(&clp->cl_state, NFSD4_COURTESY,
  NFSD4_EXPIRABLE)` for atomicity; see `fs/nfsd/state.h`.

The laundromat (`nfs4_laundromat()` in `fs/nfsd/nfs4state.c`)
periodically scans the client LRU and reaps `NFSD4_EXPIRABLE`
clients and stateless courtesy clients.

**REPORT as bugs**: Code that transitions a client to
`NFSD4_COURTESY` without checking `cl_rpc_users`, or that allows
courtesy clients to accumulate without bound (missing laundromat
reaping or missing conflict-driven expiry).

## Client Destruction

`expire_client()` in `fs/nfsd/nfs4state.c` destroys a client:
releases all stateids, sessions, delegations, and removes the client
from hash tables. `mark_client_expired_locked()` marks the client
for destruction under `nn->client_lock`.

The client's `cl_rpc_users` (atomic_t) prevents destruction while
RPCs are in progress — `get_client_locked()` increments it and
`put_client_renew_locked()` decrements it and renews the lease.

## Grace Period

During server boot, a grace period allows clients to reclaim
pre-existing state. `NFSD4_CLIENT_RECLAIM_COMPLETE` in `cl_flags`
tracks whether a client has finished reclaiming. Non-reclaim
operations that require state (new opens, locks) are rejected with
`nfserr_grace` during this period.

## Quick Checks

- **Courtesy client limits**: verify that courtesy clients are
  bounded — either by laundromat expiry or by conflict-driven
  `NFSD4_EXPIRABLE` transitions.
- **cl_rpc_users around state transitions**: verify `cl_rpc_users`
  is checked before transitioning to `NFSD4_COURTESY` to avoid
  destroying state for an active client.
- **Atomicity of cl_state changes**: `cl_state` transitions use
  `cmpxchg()` when racing with other threads (e.g., laundromat vs.
  conflict resolution).
