- `ksmbd_open_fd()`: allocates only the volatile id, in
  `work->sess->file_table`.
- `ksmbd_open_durable_fd()`: allocates the persistent id in `global_ft`;
  `smb2_open()` calls it right after `ksmbd_open_fd()` and fails with
  `-ENOMEM` when `has_file_id(fp->persistent_id)` is false.
- Both idr entries share the one initial reference; registering in
  `global_ft` takes none.
- Initial reference while `FP_NEW`: belongs to the opener.
  `ksmbd_mark_fp_closed()` returns 1 for a handle that is not `FP_INITED`, so
  teardown drops only its own transient reference.
- `ksmbd_update_fstate()`: returns `int`. `FP_NEW` to `FP_INITED` fails with
  `-ENOENT` when the state is no longer `FP_NEW` or `volatile_id` was
  cleared; `smb2_open()` then puts the handle.
- `ksmbd_lookup_fd_fast()`: makes the same `fp->tcon == work->tcon` test
  (`__sanity_check()`) as `ksmbd_lookup_fd_slow()`.
- `ksmbd_lookup_foreign_fd()`: the session-table lookup with no tcon test.
- Paths that drop the table's reference, for example `ksmbd_close_fd()` and
  `__close_file_table_ids()`: remove the idr entry and set `volatile_id` to
  `KSMBD_NO_FID` under `ft->lock` first, so a later final close does no
  `idr_remove()` on the putter's table.
- `__put_fd_final()` with `fp->conn == NULL`: calls
  `__ksmbd_close_fd(NULL, fp)` and does not decrement `open_files_count`.
- `__put_fd_final()` otherwise: uses the putter's `work->sess->file_table`
  and `work->conn->stats.open_files_count`, not the opener's.
- `__ksmbd_close_fd()` with a NULL table: skips `__ksmbd_remove_fd()`, so it
  does not unlink `fp->node` from `m_fp_list`.
- `__ksmbd_remove_durable_fd()`: sets `fp->persistent_id` to `KSMBD_NO_FID`
  after `idr_remove()`.
- `set_close_state_blocked_works()`: not called from the final close; it runs
  earlier, for example from `ksmbd_close_fd()` and `ksmbd_mark_fp_closed()`.
- `__ksmbd_close_fd()`: drops the inode reference through
  `__ksmbd_inode_close()`, not `ksmbd_inode_put()`; closes the file with
  `fput()`.
- `__ksmbd_close_fd()` also: unlinks each `struct ksmbd_lock` from its
  connection and calls `ksmbd_vfs_posix_lock_unblock()`; sends and frees the
  works parked on `fp->notify_pendings`; puts `fp->conn`; frees
  `fp->owner.name`.
- Final close may sleep: it takes `m_lock`, and calls `ksmbd_conn_write()`
  for each work parked on `fp->notify_pendings`.
