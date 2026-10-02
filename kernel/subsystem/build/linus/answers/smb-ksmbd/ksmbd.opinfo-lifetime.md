- Free path: `opinfo_put()` -> `free_opinfo()` -> `call_rcu()` with
  `free_opinfo_rcu()` -> `__free_opinfo()`; there is no opinfo_free_rcu() and
  `kfree_rcu()` is not used.
- `__free_opinfo()`: runs in the RCU callback, so it drops the opinfo's
  references on `conn` and on the lease only after the grace period.
- `opinfo->o_lease`: a counted reference on a `struct lease` that other opens
  may share; `free_lease()` is only `lease_put()`, see "Lease objects and
  tables".
- `opinfo->conn`: counted, taken with `ksmbd_conn_get()` in `alloc_opinfo()`,
  dropped in `__free_opinfo()` or earlier by `session_fd_check()` in
  `fs/smb/server/vfs_cache.c`.
- `session_fd_check()`: under `down_write(&ci->m_lock)` it puts `conn` and sets
  `conn` and `sess` to NULL on every opinfo of the inode whose `conn` is the
  file's connection, not only on the file's own opinfo.
- `ksmbd_reopen_durable_fd()`: sets `conn` (new reference) and `sess` again,
  under the same write lock, for opinfos with NULL `conn` and `o_fp == fp`.
- `opinfo->sess`, `opinfo->o_fp`, `o_lease->ci`: plain pointers, no reference.
- `opinfo->o_fp`: set in `smb_grant_oplock()` just before `opinfo_add()`; an
  opinfo held by another task can outlive the file.
- `close_id_del_oplock()`: first calls `smb_lazy_parent_lease_break_close()`
  when `fp->reserve_lease_break` is set.
- `close_id_del_oplock()`: sets `op_state` to `OPLOCK_CLOSING` whatever the old
  state, under `opinfo->state_lock`, clears bit 0 of `pending_break` in the same
  section, then wakes `oplock_q`, `oplock_brk` (lease only) and the bit waiters.
- `close_id_del_oplock()`: zeroes `breaking_cnt` only for a lease that was in
  `OPLOCK_ACK_WAIT`.
- `close_id_del_oplock()`: drops the file's reference with a bare
  `atomic_dec()` and its own with `opinfo_put()`.
- `opinfo_del()`: for a lease calls `lease_del_open()`, which unlinks the
  opinfo from `lease->open_list` and takes the lease off the client table only
  when that list becomes empty.
- Wait queues in `struct oplock_info`: `oplock_q` and `oplock_brk`; there is no
  op_end_wq.
