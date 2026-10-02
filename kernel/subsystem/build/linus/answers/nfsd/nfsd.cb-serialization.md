- Workqueue: per client, `cl_callback_wq` from `alloc_ordered_workqueue()` in
  `alloc_client()`; any callback's work item runs
  `nfsd4_process_cb_update()` when a flag is set, not only `cl_cb_null`.
- `cl_cb_session`: an `__rcu` pointer, set to NULL in `create_client()` and
  after that written with `rcu_assign_pointer()` from the workqueue only;
  sessions are freed with `kfree_rcu()` in `__free_session()`.
- **Unsafe usage**: reading `cl_cb_session` in RPC context without RCU, or
  using the session after `rcu_read_unlock()`; `cl_cb_inflight` does not pin
  the session.
  - Safe: `rcu_read_lock()`, `rcu_dereference()`, NULL test, as
    `nfsd41_cb_get_slot()` and `nfsd4_cb_sequence_done()` do.
  - Safe: `rcu_access_pointer()` for a NULL test only, as `nfsd4_cb_prepare()`
    does.
- `cl_cb_state`: not serialised; a plain `int` written by
  `nfsd4_mark_cb_state()` from nfsd threads, the workqueue and RPC context.
- `nfsd4_mark_cb_down()` and `nfsd4_mark_cb_fault()`: do nothing while
  `NFSD4_CLIENT_CB_UPDATE` is set.
- `NFSD4_CLIENT_CB_UPDATE`: set only in `nfsd4_probe_callback()`.
- `nfsd4_change_callback()`: sets no flag and queues nothing; its caller calls
  `nfsd4_probe_callback()`.
- `nfsd4_mark_cb_fault()`: asks for no rebuild; the state reaches the client
  as `SEQ4_STATUS_BACKCHANNEL_FAULT`.
- `NFSD4_CLIENT_CB_KILL`: `nfsd4_process_cb_update()` drops the RPC client,
  cred and xprt, then returns before clearing UPDATE or writing
  `cl_cb_session`.
- Backchannel slots: `se_cb_slot_avail` and `se_cb_highest_slot` in
  `struct nfsd4_session`, updated under `se_lock`; no cl_cb_slot_avail or
  cl_cb_seq_nr exists.
