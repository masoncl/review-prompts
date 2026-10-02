- `opinfo_get_list()`: static in `fs/smb/server/oplock.c`, takes `ci`,
  `skip_fp` and `snapshot`, and looks only at the first entry of `m_op_list`.
- `m_op_list` walk with deferred break: see `__smb_break_all_levII_oplock()`
  and `smb_send_parent_lease_break_noti()`.
- `smb2_open()`: reads the level through `opinfo_get()`; there is no
  smb2_lease_break_ack(), the handler is `smb21_lease_break_ack()`.
- `opinfo->o_lease`: shared with other opens, so `state`, `new_state` and
  `epoch` can change under a held opinfo reference; test `is_lease` first.
- `o_lease->l_lb`: set to NULL by `lease_del_table()`; read it under
  `read_lock(&lease_list_lock)`, as `smb2_lease_break_conn_get()` does.
- **Potentially unsafe usage**: dereferencing `fp->f_opinfo` without
  `opinfo_get()`.
  - Unsafe: outside `rcu_read_lock()`, or after `rcu_read_unlock()`;
    `opinfo_put()` frees through `call_rcu()`.
  - Safe: inside `rcu_read_lock()` with `rcu_dereference()`, for fields of the
    opinfo and of `o_lease`, as `proc_show_files()` in
    `fs/smb/server/vfs_cache.c`; `__free_opinfo()` drops the lease reference
    only in the RCU callback.
  - Safe: `opinfo_get()` paired with `opinfo_put()`, as
    `smb20_oplock_break_ack()`.
- **Potentially unsafe usage**: dereferencing `opinfo->conn` or `opinfo->sess`
  with only an opinfo reference.
  - Unsafe: outside `ci->m_lock`, while `session_fd_check()` can run; it puts
    the connection and sets both pointers to NULL under
    `down_write(&ci->m_lock)`.
  - Safe: under `down_read(&ci->m_lock)`, test `conn` for NULL and
    `ksmbd_conn_releasing()`, and take `ksmbd_conn_get()` before unlocking, as
    `smb2_oplock_break_conn_get()`.
- **Potentially unsafe usage**: dereferencing `opinfo->o_fp`.
  - Unsafe: with only an opinfo reference and no `ci->m_lock`;
    `__ksmbd_close_fd()` frees the file after `close_id_del_oplock()`.
  - Safe: under `ci->m_lock` for an opinfo found on `m_op_list`, as
    `opinfo_get_list()`; `opinfo_del()` needs the write lock before the file is
    freed.
  - Safe: look the file up by `opinfo->fid` with `ksmbd_lookup_global_fd()`, as
    `__smb2_oplock_break_noti()`.
  - Safe: in the close path of that file, as `opinfo_del()`.
  - Safe: reach the inode through the `ci` argument of `oplock_break()`, which
    the caller pins.
- **Unsafe usage**: calling `oplock_break()` while holding `ci->m_lock`; it can
  sleep for the acknowledgement, the close that ends the wait needs the write
  lock in `opinfo_del()`, and `smb2_oplock_break_conn_get()` takes the read
  lock itself.
  - Safe: take references under the lock, queue them with
    `oplock_break_add()`, and break after `up_read()`, as
    `__smb_break_all_levII_oplock()`.
- **Potentially unsafe usage**: writing `opinfo->op_state`.
  - Unsafe: on an opinfo already on `m_op_list` or in `fp->f_opinfo`, without
    `opinfo->state_lock` or over `OPLOCK_CLOSING`; `close_id_del_oplock()`
    makes that state final.
  - Safe: under `state_lock`, write only when the state is not
    `OPLOCK_CLOSING`, as `oplock_break_set_ack_wait()` and
    `smb21_lease_break_ack()`.
  - Safe: the first store before the opinfo is published, as `alloc_opinfo()`.
