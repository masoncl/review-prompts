- `prepare`: returns `bool`; false makes `nfsd4_run_cb_work()` call
  `nfsd41_destroy_cb()`: no RPC, no `done`, no requeue, `release` runs.
- `prepare`: runs in the workqueue, at most once per `nfsd4_run_cb()`; skipped
  on a requeue and not rerun on an RPC restart.
- `done`: returns `int`; 1 finished, 0 restart via
  `rpc_restart_call_prepare()` (never a requeue), other values `BUG()`.
- `done` not called, `release` still called: `prepare` false; no
  `cl_cb_client` or `NFSD4_COURTESY`; on 4.1+ when `nfsd4_cb_sequence_done()`
  returns false with neither a requeue nor an RPC restart, for example on
  `-ESERVERFAULT`.
- `release`: runs after `nfsd41_destroy_cb()` cleared
  `NFSD4_CALLBACK_RUNNING`, so the callback may be re-armed by then;
  `nfsd4_cb_notify_release()` relies on it to requeue itself.
- `cl_cb_null` has NULL `cb_ops`: no op is ever called for it.

| Bit | Set by | Cleared by |
|---|---|---|
| `NFSD4_CALLBACK_RUNNING` | caller, or `nfsd4_try_run_cb()` for it, before `nfsd4_run_cb()`; never for `cl_cb_null` | `nfsd41_destroy_cb()`; the caller when it queued nothing, as `nfsd_break_one_deleg()` does |
| `NFSD4_CALLBACK_WAKE` | queuer `nfs4_cb_getattr()` | only `nfsd4_init_cb()` |
| `NFSD4_CALLBACK_REQUEUE` | `nfsd4_requeue_cb()`; `nfsd4_run_cb_work()` on `rpc_call_async()` failure | `nfsd4_run_cb_work()` |

- `nfsd4_run_cb()`: never writes `cb_flags`, and reads it only in the
  `trace_nfsd_cb_queue()` tracepoint.
- `cb_work`: a `struct work_struct` set with `INIT_WORK()`; there is no
  nfsd4_queue_cb_delayed().
- Requeue: `nfsd4_cb_release()` calls `nfsd4_queue_cb()`, an undelayed
  `queue_work()` on the per-client `cl_callback_wq`.
