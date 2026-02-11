# NFSv4 Callback Operations

Sending a callback to a client that has been destroyed, or failing
to track in-flight callbacks, causes use-after-free on the client
structure, leaked RPC resources, or server state that permanently
diverges from what the client believes (e.g., a delegation the
server thinks it recalled but the client never received the recall).

## Callback Types

NFSv4 requires the server to initiate RPCs to clients. The callback
infrastructure in `fs/nfsd/nfs4callback.c` supports:

- `CB_RECALL` — delegation recall.
- `CB_LAYOUTRECALL` — pNFS layout recall.
- `CB_RECALL_ANY` — ask client to return some state.
- `CB_RECALL_SLOT` — ask client to shrink slot table.
- `CB_NOTIFY_DEVICEID` — pNFS device notification.
- `CB_GETATTR` — retrieve delegated attributes.
- `CB_SEQUENCE` — implicit in all NFSv4.1+ callbacks, provides
  session sequencing.

## Callback Lifecycle

Each callback is represented by `struct nfsd4_callback` which
contains `cb_clp` (the target client), `cb_ops` (type-specific
operations), and `cb_held_slot` (backchannel slot).

1. **Queue**: `nfsd4_run_cb()` calls `nfsd41_cb_inflight_begin()`
   to increment `clp->cl_cb_inflight`, then queues the callback
   work.
2. **Execute**: The callback work function calls
   `nfsd4_cb_prepare()` → RPC call → `nfsd4_cb_done()` →
   `cb_ops->done()`.
3. **Complete**: `nfsd4_cb_release()` calls `cb_ops->release()`,
   then `nfsd41_cb_inflight_end()` to decrement `cl_cb_inflight`.

`cl_cb_inflight` (`atomic_t` in `struct nfs4_client`) tracks
outstanding callbacks. Client destruction waits for this counter to
reach zero via `nfsd41_cb_inflight_wait()` before proceeding.

**REPORT as bugs**: Callback code paths where `nfsd41_cb_inflight_end()`
is not called on all exit paths (including error paths), causing
`cl_cb_inflight` to leak and client destruction to hang.

## Callback Connection State

The `cl_cb_state` field in `struct nfs4_client` tracks backchannel
health:

| State | Meaning |
|-------|---------|
| `NFSD4_CB_UP` | Backchannel operational |
| `NFSD4_CB_UNKNOWN` | State not yet determined |
| `NFSD4_CB_DOWN` | Backchannel failed |
| `NFSD4_CB_FAULT` | Permanent backchannel failure |

`nfsd4_mark_cb_down()` sets `NFSD4_CB_DOWN` after callback errors
(`-EIO`, `-ETIMEDOUT`, `-EACCES`); see `nfsd4_cb_done()`.

## Callback Sequencing (NFSv4.1+)

For NFSv4.1+, every callback includes `CB_SEQUENCE`.
`se_cb_seq_nr[]` in `struct nfsd4_session` tracks per-slot sequence
numbers. The sequence number is incremented in
`nfsd4_cb_sequence_done()` after successful completion.

`nfsd4_cb_sequence_done()` handles sequence errors:
- `NFS4ERR_SEQ_MISORDERED` — resets sequence numbers and retries.
- `NFS4ERR_DELAY` — requeues with delay.
- `NFS4ERR_BADSESSION` / `NFS4ERR_DEADSESSION` — destroys the
  callback client connection.

## Delegation Recall Callbacks

`CB_RECALL` is sent via `nfsd4_run_cb(&dp->dl_recall)` where `dp`
is `struct nfs4_delegation`. The delegation must have a reference
held for the duration of the callback (one of the three reference
sources documented in `struct nfs4_delegation`).

On callback failure or timeout, the delegation should be revoked.
`nfsd4_cb_recall_done()` handles this — if the callback fails after
retries, the delegation is marked for revocation.

## Quick Checks

- **cl_cb_inflight balance**: every `nfsd41_cb_inflight_begin()`
  must have a matching `nfsd41_cb_inflight_end()` on all paths.
- **cb_clp validity**: verify the client cannot be destroyed while
  a callback referencing it is in flight.
- **Sequence number updates**: `se_cb_seq_nr` must be incremented
  only after successful `CB_SEQUENCE` completion, not on failure.
- **Callback retry bounds**: verify retry logic has a maximum count
  or timeout to prevent unbounded retries.
