- Key: the dentry pointer, `ci->m_de`; `__ksmbd_inode_lookup()` compares
  `ci->m_de == de`. There is no m_inode member.
- Sharing: opens through the same dentry, named streams of that file
  included; a hard link through another dentry gets its own object.
- `m_lock`: a `struct rw_semaphore`, so it sleeps.
- Nesting: `m_lock` is taken outside the table rwlocks, for example in
  `ksmbd_close_disconnected_durable_delete_on_close()` (`global_ft.lock`) and
  `ksmbd_close_fd_app_instance_id()` (`ft->lock`).
- `m_flags`: every access in `fs/smb/server/vfs_cache.c` after
  `ksmbd_inode_init()` is under `m_lock`.
- Delete-pending on a stream handle: recorded per handle in
  `fp->stream_del_pending` under `fp->f_lock`, not in `m_flags`.
- `ksmbd_fd_set_delete_pending()` and `ksmbd_fd_clear_delete_pending()`:
  what `set_file_disposition_info()` calls; they pick the per-handle flag for
  a stream and `S_DEL_PENDING` otherwise.
- `ksmbd_inode_pending_delete()`: true for `S_DEL_PENDING`; for a stream
  handle also true for `fp->stream_del_pending`.
- `ksmbd_query_inode_status()`: reports
  `KSMBD_INODE_STATUS_PENDING_DELETE` for `S_DEL_PENDING` only.
- `ksmbd_fd_set_delete_on_close()`: tests only `ksmbd_stream_fd()`; the
  `file_info` argument is unused; `smb2_open()` tests
  `FILE_DELETE_ON_CLOSE_LE`.
- `__ksmbd_inode_close()` on a stream handle: removes the xattr named
  `fp->stream.name` when `S_DEL_ON_CLS_STREAM` or `fp->stream_del_pending`
  is set.
- `__ksmbd_inode_close()` on every close: turns `S_DEL_ON_CLS` into
  `S_DEL_PENDING` before it drops `m_count`.
- After that first close: `ksmbd_inode_pending_delete()` is true for the
  remaining handles, and `smb2_open()` fails a new open with `-EBUSY`.
- Unlink: `__ksmbd_inode_close()` calls `ksmbd_vfs_unlink()` when `m_count`
  reaches zero and `S_DEL_PENDING` is set.
- `ksmbd_inode_put()`: on the last reference frees the object without
  testing `m_flags`; only `__ksmbd_inode_close()` calls `ksmbd_vfs_unlink()`.
