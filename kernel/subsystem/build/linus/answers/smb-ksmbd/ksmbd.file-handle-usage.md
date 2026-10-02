- `smb2_set_request_open()`: takes a second reference with
  `ksmbd_file_get()` and stores it in `work->request_open`.
- `work->request_open`: put by `smb2_complete_request_open()`, which
  `__handle_ksmbd_work()` calls after each command, and by
  `ksmbd_free_work_struct()`; the handler does not put it.
- Handler after `smb2_set_request_open()`: still puts its own lookup
  reference, on the failure return too, as `smb2_set_info()` does.
- `ksmbd_fp_get()`: static in `fs/smb/server/vfs_cache.c`; code outside
  uses `ksmbd_file_get()`.
- `ksmbd_vfs_fsync()`: holds the lookup and the put for `smb2_flush()`.
- Put used after a lookup, by example:

| Lookup | Put | Example |
|---|---|---|
| `ksmbd_lookup_fd_fast()`, `ksmbd_lookup_fd_slow()` | `ksmbd_fd_put()` | `smb2_close()`, `smb2_set_info()` |
| `ksmbd_lookup_fd_inode()` | `ksmbd_fd_put()` | `ksmbd_vfs_check_rename_share()` |
| `ksmbd_lookup_global_fd()` | `ksmbd_fd_put()` | `__smb2_oplock_break_noti()` |
| `ksmbd_lookup_durable_fd()` | `ksmbd_put_durable_fd()` | `parse_durable_handle_context()` |

- `ksmbd_fd_put()` on a handle of another session: the final close skips
  `idr_remove()` on the caller's table only when `volatile_id` is already
  `KSMBD_NO_FID`; the paths that drop the table's reference set that first
  (see "Open file handle lifetime").
- **Potentially unsafe usage**: a final close that passes a NULL table to
  `__ksmbd_close_fd()`, as `ksmbd_put_durable_fd()` does on the last
  reference.
  - Unsafe: while `fp->node` is still linked on `m_fp_list`; the NULL table
    skips `__ksmbd_remove_fd()` and the handle is freed while linked.
  - Safe: after `list_del_init(&fp->node)` under
    `down_write(&fp->f_ci->m_lock)`, as `ksmbd_scavenger_dispose_dh()` and
    `__close_file_table_ids()` do.
- `m_fp_list` walk: `m_lock` is an rwsem; walk under `down_read()`, as
  `ksmbd_smb_check_shared_mode()` does.
- Entries on `m_fp_list` include `FP_NEW` handles: `smb2_open()` links the
  handle before `ksmbd_update_fstate()` sets `FP_INITED`.
- Entries on `m_fp_list` include preserved durable handles with `conn` and
  `tcon` NULL: `__close_file_table_ids()` does not unlink a handle that
  `session_fd_check()` preserved.
- `ksmbd_has_other_active_fd()`: shows the tests a walker makes on such
  entries, `f_state == FP_INITED` and `READ_ONCE()` of `conn` and `tcon`.
