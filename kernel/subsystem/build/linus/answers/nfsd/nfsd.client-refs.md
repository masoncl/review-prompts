| Counter | Prevents | Who waits |
|---|---|---|
| `cl_rpc_users` | `mark_client_expired_locked()` succeeding | `force_expire_client()`, on `expiry_wq` |
| `cl_ref` in `cl_nfsdfs` | `__free_client()` freeing the memory; nothing else | nobody |
| `cl_cb_inflight` | `__destroy_client()` getting past `nfsd4_shutdown_callback()` | `nfsd4_shutdown_callback()` |

- `cl_rpc_users`: does not hold off `force_expire_client()` once its wait has
  passed. Server-side walks that pin test `is_client_expired()` under
  `client_lock` first, as `nfsd4_revoke_states()` does.
- `cl_ref` helpers: `nfsd4_put_client()` puts. There is no get helper that
  takes a `struct nfs4_client`; takers call `kref_get()` on
  `cl_nfsdfs.cl_ref`, or `get_nfsdfs_client()` on an nfsdfs inode.
  drop_client(), get_nfs4_client() and put_nfs4_client() are not in this tree.
- `cl_cb_inflight`: raised by `nfsd4_run_cb()` for every callback; for one
  that was queued and has `cb_ops`, dropped by `nfsd41_destroy_cb()` after
  the `release` op returns.
- A callback: gets `cl_cb_inflight` from `nfsd4_run_cb()` and holds a
  reference that keeps alive the object that embeds its
  `struct nfsd4_callback`, for example `sc_count` for CB_RECALL. `cl_cb_null`
  holds none.
- A callback also takes `cl_ref` by hand in two cases: CB_RECALL_ANY in
  `deleg_reaper()`, and CB_OFFLOAD in `nfsd4_send_cb_offload()`. The `release`
  op puts it.
- A running async copy: holds no client counter. `cp_clp` is a bare pointer.
- What keeps `cp_clp` valid: the copy is on `clp->async_copies`, and
  `nfsd4_shutdown_copy()` joins its kthread before `free_client()`.
- **Potentially unsafe usage**: taking a copy off `clp->async_copies` and
  then using its client.
  - Unsafe: when nothing pins the client, because `nfsd4_shutdown_copy()` can
    no longer find the copy and `__destroy_client()` proceeds; the last
    `nfs4_put_copy()` then locks `cl_lock` of a freed client in
    `nfs4_put_stid()`.
  - Safe: take `cl_ref` under `async_lock` before unlinking, as
    `nfsd4_cancel_copy_by_sb()` does; `__free_client()` runs only at the last
    `nfsd4_put_client()`.
  - Safe: from the client's own compound, as `nfsd4_offload_cancel()` does;
    `cstate->clp` holds `cl_rpc_users`.
  - Safe: inside `__destroy_client()`, as `nfsd4_shutdown_copy()` does before
    `free_client()`.
