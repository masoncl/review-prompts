- `NFSD4_COPY_F_STOPPED`: set only by `nfsd4_stop_copy()`, before
  `kthread_stop()`; the worker neither sets nor tests it.
- Worker stop test: `kthread_should_stop()` in `_nfsd_copy_file_range()`.
- `NFSD4_COPY_F_STOPPED` reader: only `nfsd4_has_active_async_copies()`.
- `NFSD4_COPY_F_CB_ERROR`: set by `nfsd4_cancel_copy_by_sb()` together with
  `nfserr = nfserr_admin_revoked`; while set, neither the worker nor
  `nfsd4_stop_copy()` overwrites `nfserr`. It does not mean CB_OFFLOAD
  failed.
- `NFSD4_COPY_F_OFFLOAD_DONE`: set by `nfsd4_cb_offload_release()`, and by
  `nfsd4_send_cb_offload()` when `cp_clp` is NULL; only the reaper reads it.
- `refcount` in `struct nfsd4_async_copy` has four kinds of holder:

  | Reference | Taken in | Dropped in |
  |---|---|---|
  | list membership | `nfsd4_copy()`, `refcount_set()` to 1 | by whoever unlinked the copy |
  | kthread | `nfsd4_copy()`, before `wake_up_process()` | end of `nfsd4_do_async_copy()` |
  | callback | `nfsd4_send_cb_offload()` | `nfsd4_cb_offload_release()` |
  | canceller | `find_async_copy()`, `nfsd4_unhash_copy()`, `nfsd4_cancel_copy_by_sb()` | inside `nfsd4_stop_copy()` |

- Last `nfs4_put_copy()`: calls `nfs4_put_stid()` on `cp_stid`; that removes
  the stateid from `cl_stateids` and runs `nfsd4_free_async_copy_stid()`.
- `cp_stid.sc_count`: stays at 1 for the whole life of the copy.
- `cp_copy.cp_clp` and `cp_stid.sc_client`: uncounted pointers; a client
  reference (`cl_nfsdfs.cl_ref`) is held only across CB_OFFLOAD and inside
  `nfsd4_cancel_copy_by_sb()`.
- `nfsd4_copy()` order: `kthread_create()`, `get_task_struct()`, kthread
  reference, `wake_up_process()`, then `list_add()` to `async_copies`; the
  worker can finish before the copy is on the list.
- Worker order in `nfsd4_do_async_copy()`:
  1. store `nfserr` (skipped when `NFSD4_COPY_F_CB_ERROR` is set)
  2. set `NFSD4_COPY_F_COMPLETED`
  3. `atomic_dec()` of `pending_async_copies`
  4. `nfsd4_send_cb_offload()`, which queues the callback and does not wait
  5. drop the kthread reference
- The worker never unlinks the copy from `async_copies`.
- `cp_clp == NULL`: marks a cancelled copy; `nfsd4_send_cb_offload()` then
  sends nothing.
- Four paths make the copy unfindable, each unlinking under `async_lock`:
  - `nfsd4_async_copy_reaper()`, from `nfs4_laundromat()`: only once
    `NFSD4_COPY_F_OFFLOAD_DONE` is set and `cp_ttl` (from
    `NFSD_COPY_INITIAL_TTL`) has counted down to 0.
  - `find_async_copy()`, for OFFLOAD_CANCEL: also clears `cp_clp`.
  - `nfsd4_unhash_copy()`, for `nfsd4_shutdown_copy()`: also clears `cp_clp`.
  - `nfsd4_cancel_copy_by_sb()`, from `fs/nfsd/nfsctl.c`: leaves `cp_clp`
    set, so a worker that is still running sends CB_OFFLOAD with
    `nfserr_admin_revoked`.
- `find_async_copy()`: not a plain lookup; use it only to cancel.
- `nfsd4_offload_status()`: uses `find_async_copy_locked()` with `async_lock`
  held throughout and takes no reference.
- `nfsd4_stop_copy()`: calls `kthread_stop()` unconditionally; this relies on
  the `get_task_struct()` in `nfsd4_copy()`.
- `nfsd4_stop_copy()` and `cleanup_async_copy()`: neither unlinks the copy;
  both call `release_copy_files()` and `nfs4_put_copy()`.
- Over the cap: `nfsd4_copy()` returns `nfserr_jukebox`; there is no fallback
  to a synchronous copy.
- `nfs4_alloc_copy_stid()` or `kthread_create()` failure in `nfsd4_copy()`:
  also `nfserr_jukebox`.
- **Unsafe usage**: calling `nfsd4_stop_copy()` on a copy that is still on
  `async_copies`; the reaper or a second canceller can then run
  `release_copy_files()` on it at the same time, with no lock.
  - Safe: take a reference and unlink under `async_lock`, call
    `nfsd4_stop_copy()`, then call `nfs4_put_copy()` once more for the list
    reference, as `nfsd4_offload_cancel()` and `nfsd4_shutdown_copy()` do.
- **Potentially unsafe usage**: a `nfs4_put_copy()` that may drop the last
  reference.
  - Unsafe: when nothing keeps the `struct nfs4_client` alive;
    `nfs4_put_stid()` locks `sc_client->cl_lock`.
  - Safe: in `nfsd4_shutdown_copy()`, which `__destroy_client()` calls before
    `free_client()`.
  - Safe: in `nfsd4_cb_offload_release()`, when the callback was queued
    before `__destroy_client()` reached `nfsd4_shutdown_callback()`;
    `nfsd41_destroy_cb()` ends `cl_cb_inflight` only after the release hook,
    and `nfsd4_shutdown_callback()` waits for it.
  - Safe: in `nfsd4_cancel_copy_by_sb()`, which holds `cl_nfsdfs.cl_ref`
    until after its last put.
