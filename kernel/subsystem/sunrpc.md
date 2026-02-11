# SunRPC Subsystem Details

## Overview

SunRPC (`net/sunrpc/`) provides the RPC transport layer for NFS and
related services. Includes client (`rpc_clnt`, `rpc_task`, `xprt`) and
server (`svc_serv`, `svc_rqst`, `svc_xprt`) infrastructure, with TCP,
UDP, and RDMA transports plus RPCSEC_GSS authentication.

| Files | Domain |
|-------|--------|
| `svc.c`, `svc_xprt.c`, `clnt.c`, `sched.c`, `xprt.c` | Core |
| `svcsock.c`, `xprtsock.c` | Socket |
| `xprtrdma/svc_rdma_*.c`, `xprtrdma/*.c` | RDMA |
| `auth_gss/*.c`, `svcauth_gss.c`, `gss_krb5_*.c` | GSS |

## Transport References for Async Work

Queuing async work (via `queue_work()` or `queue_delayed_work()`)
that references a transport without holding a reference causes
use-after-free when the transport is destroyed before the work runs.

- **Server**: call `svc_xprt_get()` before queuing; release with
  `svc_xprt_put()` in the work handler. Both are `kref`-based; see
  `include/linux/sunrpc/svc_xprt.h`.
- **Client**: call `xprt_get()` before queuing; release with
  `xprt_put()` in the work handler. See `include/linux/sunrpc/xprt.h`.

**REPORT as bugs**: `queue_work()` or `queue_delayed_work()` calls
that reference a transport without a preceding `svc_xprt_get()` or
`xprt_get()`.

## Transport State Flags

Accessing a transport without checking its state flags causes
use-after-free (operating on a closed transport) or invalid
operations (sending on a disconnected transport).

**Server flags** (in `xpt_flags`, defined in
`include/linux/sunrpc/svc_xprt.h`):

| Flag | Meaning |
|------|---------|
| `XPT_BUSY` | Transport enqueued or receiving |
| `XPT_CONN` | Connection pending |
| `XPT_CLOSE` | Dead or dying |
| `XPT_DATA` | Data pending |
| `XPT_DEAD` | Transport closed |

**Client flags** (in `xprt->state`, defined in
`include/linux/sunrpc/xprt.h`):

| Flag | Meaning |
|------|---------|
| `XPRT_CONNECTED` | Transport connected |
| `XPRT_CONNECTING` | Connection in progress |
| `XPRT_CLOSE_WAIT` | Waiting for close |
| `XPRT_CLOSING` | Transport shutting down |

Check `XPT_CLOSE`/`XPT_DEAD` (server) or
`XPRT_CONNECTED`/`XPRT_CLOSING` (client) before transport access.

## XPT_BUSY Lifecycle (server)

If `XPT_BUSY` is not cleared after processing, the transport is
permanently stuck — no further receives will be scheduled.

`svc_xprt_received()` in `net/sunrpc/svc_xprt.c` clears `XPT_BUSY`
and re-enqueues the transport. Every exit path from
`svc_handle_xprt()` must call `svc_xprt_received()`, including
reservation failures and error paths.

**REPORT as bugs**: Exit paths from transport processing that skip
`svc_xprt_received()`, leaving `XPT_BUSY` set permanently.

## Thread Pool Shutdown (server)

Failing to call `svc_exit_thread()` on all thread stop paths leaves
`SP_VICTIM_REMAINS` set in the pool flags, causing the controller
thread to hang waiting for it to clear.

`svc_exit_thread()` in `net/sunrpc/svc.c` decrements thread counts,
frees the `svc_rqst`, and calls
`clear_and_wake_up_bit(SP_VICTIM_REMAINS, ...)`. When `kthread_stop()`
wins a race against voluntary exit, the controller must still call
`svc_exit_thread()`.

## Page Array Bounds (server)

Writing beyond `rq_pages[]` bounds causes buffer overflow and memory
corruption.

`svc_rqst_replace_page()` in `net/sunrpc/svc.c` checks
`rq_next_page` against `rq_pages[0]` and `rq_pages[rq_maxpages]`
before replacing. Any code that advances `rq_next_page` must
verify it stays within bounds.

## Deferred Request Context (server)

Incorrect handoff of `rq_xprt_ctxt` between a request and its
deferred copy causes double-free of the transport context.

When deferring: set `dr->xprt_ctxt = rqstp->rq_xprt_ctxt` then
`rqstp->rq_xprt_ctxt = NULL`. On revisit: reverse the assignment.
Both sides must be updated atomically — leaving both non-NULL means
both will attempt to free the same context.

## RPC Task State Machine (client)

Each `call_*` state function must set `tk_action` to the next state.
If `tk_action` is NULL the task is exiting — modifying `tk_status`
at that point corrupts the final result. See `net/sunrpc/clnt.c`
for the state machine (`call_start`, `call_reserve`,
`call_reserveresult`, `call_refresh`, etc.).

Failing to set `tk_action` causes the task to stall permanently.
Setting `tk_action` after the task has been freed causes corruption.

## Slot Release (client)

`xprt_release()` must occur on all paths after `xprt_reserve()`
succeeds. Failing to release slots causes slot exhaustion — all
subsequent RPC calls block waiting for a slot that will never become
available.

## Congestion Window (client)

Updates to `xprt->cong` must hold `transport_lock`. Racing updates
corrupt the congestion window, causing either excessive outstanding
requests (overload) or artificial throttling (stalls).

## Timeout Overflow (client)

After exponential backoff shifts, `rq_timeout` can overflow. It must
be clamped: `if (rq_timeout > to_maxval) rq_timeout = to_maxval`.
Overflowed timeouts wrap to small values, causing spurious retransmits.

## rq_flags Atomicity (server)

`rq_flags` in `struct svc_rqst` must be modified with `set_bit()` /
`clear_bit()`, not `__set_bit()` / `__clear_bit()`. The non-atomic
variants race with `svc_xprt_enqueue()` which tests these flags
concurrently.

## Socket Transport

### Short Read/Write Handling

TCP may return fewer bytes than requested. Socket receive loops must
continue until the full message is read or use `MSG_WAITALL` for
fixed-size reads (e.g., the 4-byte record marker). Treating a short
read as complete causes data corruption or partial processing.

### Record Marker Bounds

The incoming record size from the 4-byte TCP record marker must be
validated before allocating buffers. An unchecked record size from a
malicious client can cause memory exhaustion or integer overflow.

### Listener Callback Inheritance (server)

Child sockets inherit `sk_user_data` from the listener. Socket
callbacks must check `sk->sk_state == TCP_LISTEN` before
dereferencing `sk_user_data` as a `struct svc_sock`, because the
child socket's `sk_user_data` may not yet be initialized.

### Callback Teardown (client)

Socket callback teardown must follow this sequence to prevent races
with in-flight callbacks:

1. `lock_sock(sk)`
2. `xs_restore_old_callbacks()` — restores original socket callbacks
3. `sk->sk_user_data = NULL`
4. `release_sock(sk)`
5. `sock_release()`

See `xs_reset_transport()` in `net/sunrpc/xprtsock.c`.

### Cork Balance (server)

Every `tcp_sock_set_cork(sk, true)` must have a matching
`tcp_sock_set_cork(sk, false)` on all paths including errors. A
leaked cork prevents TCP from sending buffered data.

### Reconnection Backoff (client)

Use `xprt_reconnect_delay()` and `queue_delayed_work()`, not
immediate `queue_work()`. Immediate reconnection without backoff
causes connection storms that overwhelm the server. See
`xs_connect()` in `net/sunrpc/xprtsock.c`.

### NOFS Allocation (client)

Socket operations in the NFS write-back path must use
`memalloc_nofs_save()` / `memalloc_nofs_restore()` to prevent
deadlock during memory reclaim. See `xs_stream_data_receive_workfn()`
and `xs_udp_data_receive_workfn()` in `net/sunrpc/xprtsock.c`.

### State Flag Barriers

Use `smp_mb__after_atomic()` between related flag changes to ensure
consistent state visibility across CPUs.

### New XPRT_SOCK_* Flags (client)

When adding a new `XPRT_SOCK_*` flag, add the corresponding
`clear_bit()` in `xs_sock_reset_state_flags()` in
`net/sunrpc/xprtsock.c`. Flags that persist across transport reset
cause stale state on reconnection.

### Write Space Callback (server)

`svc_write_space()` in `net/sunrpc/svcsock.c` must call
`svc_xprt_enqueue()` when write space becomes available. The server
couples read and write — it stops reading when it cannot write.
Missing the write-space wakeup deadlocks the transport.

## RDMA Transport

### DMA Mapping Lifecycle

DMA mappings must persist until the completion callback fires.
Unmapping before completion causes use-after-free and data
corruption. Check `ib_dma_map_sg()` return — `mr_nents == 0` is a
failure. Unmap in the completion handler or after a synchronous wait.

### MR/FRWR Invalidation Before Reuse

Memory Regions must complete invalidation before reuse.
`frwr_unmap_sync()` in `net/sunrpc/xprtrdma/frwr_ops.c` blocks
until invalidation completes. `frwr_unmap_async()` does not block —
do not reuse the MR immediately after an async invalidate.

### Completion Status Check

Only `wr_cqe` and `status` are reliable in work completions. Check
`wc->status == IB_WC_SUCCESS` before accessing `byte_len` or other
fields. Accessing other fields on a failed completion reads garbage.

### Device Removal Handling

On `IB_WC_WR_FLUSH_ERR`, the RDMA device may already be gone. Do
not call `ib_dma_*` functions in flush error paths — the device
pointer may be invalid.

### Post-Send Use-After-Free (server)

The completion handler can fire immediately after `ib_post_send()`
returns, potentially freeing the context. Copy any needed context
fields to stack variables before posting if they are needed for
error handling or tracing after the post call.

### SQ Accounting and Flag Ordering (server)

Call `set_bit(XPT_CLOSE)` BEFORE `svc_rdma_*_ctxt_put()` to prevent
a racing completion from reallocating a freed context before the
close flag is visible.

### CM Event Reference Balance (client)

`RDMA_CM_EVENT_ESTABLISHED` takes a reference via
`rpcrdma_ep_get()` in `net/sunrpc/xprtrdma/verbs.c`.
`RDMA_CM_EVENT_DISCONNECTED` releases via `rpcrdma_ep_put()`.
`DEVICE_REMOVAL` and `ADDR_CHANGE` may fire before `ESTABLISHED` —
the handler must track whether the reference was actually taken.

### Reconnect DMA Remapping (client)

If teardown calls `rpcrdma_regbuf_dma_unmap()`, the reconnect path
must remap buffers before posting receives. Posting with an unmapped
buffer causes `LOCAL_PROT_ERR`.

### Credit Flow Ordering (client)

Call `rpcrdma_post_recvs()` BEFORE `rpcrdma_update_cwnd()`. Opening
credits wakes senders who need posted receives — if receives are not
posted first, the sender hits Receiver Not Ready (RNR) errors.

## GSS Authentication

### Sequence Window Locking (server)

Failing to hold `sd_lock` for all sequence window operations allows
replay attacks — an attacker can reuse a previously accepted
sequence number.

`sd_lock` (spinlock in `struct gss_svc_seq_data`, defined in
`net/sunrpc/auth_gss/svcauth_gss.c`) protects the sequence window
check, advance, and bit-set operations. Verify arithmetic handles
overflow near `MAXSEQ` and underflow in `sd_max - GSS_SEQ_WIN`.

### Context Cache Reference Counting (server)

`gss_svc_searchbyctx()` returns a referenced cache entry. The caller
must use the context and then call `cache_put()`. Accessing the
context after `cache_put()` is use-after-free.

### Cryptographic Result Checking

`gss_verify_mic()`, `gss_wrap()`, and `gss_unwrap()` return
`GSS_S_*` status codes. Proceeding without checking these results
can accept forged or corrupted requests, bypassing authentication.

**REPORT as bugs**: Code paths that call `gss_verify_mic()`,
`gss_wrap()`, or `gss_unwrap()` without checking the return status
and aborting on error.

### Buffer Slack Sizing (client)

For Kerberos v2 (RFC 4121), `au_ralign != au_rslack` because the
checksum follows cleartext. The slack calculation must account for
`GSS_KRB5_TOK_HDR_LEN` plus the checksum size. Incorrect slack
causes buffer overruns during unwrap.

### Credential Lifecycle

- **Server**: call `get_group_info()` before using `rsci->cred`;
  release via `free_svc_cred()`.
- **Client**: call `put_rpccred()` only after all use is complete.

Using credentials after release is use-after-free.

### Upcall Matching

`__gss_find_upcall()` must match `uid`, `service`, and in-flight
state. Insufficient matching criteria can pair the wrong
upcall/downcall, returning the wrong GSS context for a client.

### Deferred Request Verification (server)

Skip re-verification for `rqstp->rq_deferred` requests — they were
already verified on the first pass. Re-verifying wastes CPU and can
fail if the GSS context has been updated between passes.

## Network Namespace

All SunRPC code must respect network namespace boundaries:

- Server transport: `xprt->xpt_net`, `serv->sv_net`.
- Client transport: `xprt->xprt_net`, `clnt->cl_xprt->xprt_net`.
- Socket creation: `sock_create_kern(net, ...)`.
- RDMA: `rdma_create_id(net, ...)`, `rdma_dev_access_netns()`.

**REPORT as bugs**: Code that uses `&init_net` or
`current->nsproxy->net_ns` instead of the transport's or service's
network namespace.

## Quick Checks

- **Transport reference before async work**: every `queue_work()` or
  `queue_delayed_work()` that touches transport state must hold a
  transport reference.
- **XPT_BUSY cleared on all exits**: `svc_xprt_received()` called on
  every exit path from transport processing.
- **New XPRT_SOCK_* flags**: corresponding `clear_bit()` added to
  `xs_sock_reset_state_flags()`.
- **RDMA post-send safety**: context fields copied to stack before
  `ib_post_send()` if needed after the call.
- **GSS return values**: all `gss_verify_mic()` / `gss_wrap()` /
  `gss_unwrap()` returns checked.
