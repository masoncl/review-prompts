- `nfsd4_run_cb()`: takes only `cl_cb_inflight`; no client refcount, no
  `cl_rpc_users`, and there is no nfsd4_get_client().
- `cl_cb_inflight` dropped: at once when `queue_work()` fails; else in
  `nfsd41_destroy_cb()` after `release`; for a CB_NULL probe that is sent, in
  `nfsd4_cb_probe_release()`.
- Return false: `queue_work()` found `cb_work` pending;
  `NFSD4_CALLBACK_RUNNING` is not consulted.
- Before the call: `cb->cb_clp` must be valid; `nfsd4_run_cb()` dereferences
  it before it takes the inflight count.
- Before the call, for a callback with `cb_ops`: own
  `NFSD4_CALLBACK_RUNNING` by `test_and_set_bit()`, and hold whatever
  `release` drops. `nfsd4_try_run_cb()` does the `test_and_set_bit()` itself
  and queues nothing when the bit was set.
- **Potentially unsafe usage**: ignoring the return of `nfsd4_run_cb()`, or
  using `nfsd4_try_run_cb()`, which returns nothing.
  - Unsafe: a reference was taken for `release` and the bit may already be
    set or the work pending; nothing drops that reference.
  - Safe: caller won `NFSD4_CALLBACK_RUNNING`, which `nfsd41_destroy_cb()`
    clears only once the work is no longer pending, as `nfs4_cb_getattr()`
    does.
  - Safe: `cb_flags` is still as `nfsd4_init_cb()` left it, on a callback
    sent once, as in `nfsd4_send_cb_offload()` and `nfsd4_lm_notify()`.
  - Safe: `cl_cb_null` with no reference taken, as `nfsd4_probe_callback()`
    does.
- **Unsafe usage**: calling `nfsd4_init_cb()` on a callback that may be
  queued or in flight; it zeroes `cb_flags` and re-inits `cb_work`.
  - Safe: at send time on a callback never queued before, as
    `nfsd4_send_cb_offload()` does, once per copy.

| Callback | Caller | Queues with | Holds for `release` |
|---|---|---|---|
| CB_RECALL | `nfsd_break_one_deleg()` | `nfsd4_run_cb()` | `dl_stid.sc_count` via `refcount_inc_not_zero()` |
| CB_OFFLOAD | `nfsd4_send_cb_offload()` | `nfsd4_try_run_cb()` | `cl_nfsdfs.cl_ref` and copy `refcount` |
| CB_NOTIFY_LOCK | `nfsd4_lm_notify()` | `nfsd4_try_run_cb()` | nothing new; the list's `nbl_kref` |

- `nfsd4_send_cb_offload()`: takes `struct nfsd4_async_copy`, and sends
  nothing when `cp_clp` is NULL.
- `nfsd4_lm_notify()`: queues only if it unlinked the entry under
  `blocked_locks_lock`; `nfsd4_cb_notify_lock_release()` puts that reference
  with `free_blocked_lock()`.
