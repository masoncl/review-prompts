- Oplock break connection: `smb2_oplock_break_conn_get()` reads `opinfo->conn`
  under `down_read(&ci->m_lock)` and takes its own `ksmbd_conn_get()`; the
  worker drops that reference with `ksmbd_conn_put()`.
- Lease break connection: `smb2_lease_break_conn_get()` uses `opinfo->conn`
  when it is set and not `ksmbd_conn_releasing()`.
- Version 2 lease fallback: otherwise `smb2_lease_break_conn_get()` uses
  `lease->l_lb->conn`, the connection held by the client's
  `struct lease_table`, read under `read_lock(&lease_list_lock)`.
- No usable connection: the sender returns `ksmbd_invalidate_durable_fd()` for
  `opinfo->fid`, sends nothing and does not call `wait_for_break_ack()`; it
  does not change the holder's `level` or `op_state`.
- `ksmbd_invalidate_durable_fd()` on a disconnected file (`fp->conn` NULL):
  also sets `durable_timeout` to 1 and wakes `dh_wq`, which marks the handle
  expired for `ksmbd_durable_scavenger()`.
- `opinfo_get_list()`: returns NULL when the first entry of `m_op_list` has a
  NULL or releasing `conn`, so `smb_grant_oplock()` then grants as if the
  inode had no holder.
- `smb2_lease_break_noti()` with `sync` true: sends inline even in
  `OPLOCK_ACK_WAIT`; only `smb_break_all_levII_oplock_rename()` passes true.
- `smb_break_all_levII_oplock_for_delete()`: sends no notification to level II
  oplock holders, it sets their `level` to `SMB2_OPLOCK_LEVEL_NONE` directly;
  lease holders still go through `oplock_break()`.
- `__smb2_oplock_break_noti()`: looks the file up with
  `ksmbd_lookup_global_fd()` from `br_info->fid` and sends nothing when it is
  gone.
