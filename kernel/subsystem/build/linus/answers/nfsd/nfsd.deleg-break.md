- Callers: besides `__break_lease()`, `nfsd_handle_dir_event()` and
  `nfsd_recall_all_dir_delegs()` call `nfsd_break_deleg_cb()` directly,
  under an `flc_lock` they took themselves.
- `__break_lease()`: also holds `file_rwsem` for read around the callback.
- `nfsd_break_deleg_cb()`: sets `fl_break_time` to 0 and
  `fi_had_conflict`, bumps `cl_delegs_in_recall`, and returns false so the
  lease stays.
- `nfsd_break_one_deleg()`: takes the recall reference with
  `refcount_inc_not_zero()`, not a bare `refcount_inc()`.
- Count already zero: `nfsd_break_one_deleg()` clears
  `NFSD4_CALLBACK_RUNNING` and queues nothing.
- Why not a bare increment: `nfsd4_cb_notify_prepare()` and
  `nfsd4_cb_notify_done()` call `nfsd_break_one_deleg()` with no `flc_lock`
  held.
- Queue failure: undone with `refcount_dec()`, not `nfs4_put_stid()`.
- `nfsd4_cb_recall_prepare()`: the lock it takes is `nn->deleg_lock`.
- Courtesy client: `try_to_expire_client()` moves `cl_state` from
  `NFSD4_COURTESY` to `NFSD4_EXPIRABLE`; there is no
  NFSD4_CLIENT_EXPIRABLE flag.
- Courtesy client recall: the callback still calls
  `nfsd_break_one_deleg()`, after `try_to_expire_client()` has made the
  state `NFSD4_EXPIRABLE`; `nfsd4_run_cb_work()` decides whether CB_RECALL
  is sent.
- `nfsd4_run_cb_work()`: gives up before `prepare` when `cl_cb_client` is
  NULL or `cl_state` is `NFSD4_COURTESY`, so the delegation is not put on
  `del_recall_lru`.
- Expiry: `nfs4_get_client_reaplist()` takes an `NFSD4_EXPIRABLE` client
  only if `mark_client_expired_locked()` finds `cl_rpc_users` at 0.
- After expiry: `__destroy_client()` unhashes the client's delegations with
  `SC_STATUS_CLOSED` and removes the leases.
