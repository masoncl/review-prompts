- `struct ksmbd_conn`: three separate counters. `refcnt` is the lifetime
  count (`ksmbd_conn_get()`, `ksmbd_conn_put()`); `r_count` counts works in
  flight and `ksmbd_conn_handler_loop()` waits for it to reach 0 before
  teardown; `req_running` feeds the idle waits and the in-flight cap.
- `conn->status`: its values are `KSMBD_SESS_NEW`, `KSMBD_SESS_GOOD` and the
  rest of that enum in `fs/smb/server/connection.h`, despite the name.
  Session state is separate: `sess->state`, with `SMB2_SESSION_EXPIRED`,
  `SMB2_SESSION_IN_PROGRESS` and `SMB2_SESSION_VALID`.
- `struct ksmbd_transport`: not embedded in the conn. `conn->transport`
  points to one embedded in `struct tcp_transport` or
  `struct smb_direct_transport`, and it points back through `conn`.
- `struct ksmbd_conn_ops`: only `process_fn` and `terminate_fn`, in one
  static `default_conn_ops` in `fs/smb/server/connection.c`;
  `conn->conn_ops` is never assigned.
- `struct smb_version_ops` (`conn->ops`): the per-dialect hooks for session
  and tree lookup, signing, encryption and credits.
  `struct smb_version_cmds` (`conn->cmds`) is the command table.
- Global containers: connections are in hashtable `conn_list` under rwsem
  `conn_list_lock`; lease tables are on list `lease_table_list` under rwlock
  `lease_list_lock` in `fs/smb/server/oplock.c`.
- `conn->sessions`: holds only sessions created on that conn;
  `ksmbd_session_register()` is the only store.
- Conn bound by multichannel: tied to the session only by its entry in
  `sess->ksmbd_chann_list`, indexed by the conn pointer; the session is
  found in `sessions_table`, see the fallback in
  `ksmbd_session_lookup_all_states()`.
- `struct channel`: created only when `conn->dialect` is at least
  `SMB30_PROT_ID`, in `register_session_channel()`; `chann->conn` is an
  uncounted pointer.
- `struct ksmbd_user`: not refcounted. The session owns it and
  `ksmbd_session_destroy()` frees it; `tree_conn->user` is a copy of the
  pointer `sess->user`.
- `work->sess` and `work->tcon`: counted references, taken by
  `smb2_check_user_session()` and `smb2_get_ksmbd_tcon()`, dropped at the end
  of `__handle_ksmbd_work()`. Later commands of a compound reuse the first
  command's pair.
- Break notification work: `request_buf` holds a
  `struct oplock_break_info` or `struct lease_break_info`, not an SMB
  header; `work->sess` is copied from `opinfo->sess` without a reference; it
  runs `__smb2_oplock_break_noti()` or `__smb2_lease_break_noti()`.
- Blocking byte-range lock: `smb2_lock()` sleeps in
  `ksmbd_vfs_posix_lock_wait()` inside the handler; the work does not outlive
  it.
- `global_ft` in `fs/smb/server/vfs_cache.c`: holds every open, not only
  durable ones; `smb2_open()` assigns a persistent id to each. An oplock
  break notification finds its open there by `opinfo->fid`.
- Detached durable handle: `fp->conn` and `fp->tcon` are `NULL` and
  `fp->volatile_id` is `KSMBD_NO_FID`; it stays in `global_ft` and on
  `m_fp_list`. `session_fd_check()` also clears `conn` and `sess` of every
  opinfo on the inode that has the same conn, and `conn` of the handle's
  locks; `ksmbd_reopen_durable_fd()` restores them for the handle's own
  opinfo and locks.
- `struct ksmbd_inode`: keyed by dentry (`m_de`), not by `struct inode`; see
  `__ksmbd_inode_lookup()`. Some walkers of `m_fp_list` compare
  `file_inode()` themselves, for example `ksmbd_smb_check_shared_mode()` and
  `ksmbd_lookup_fd_inode()`.
- `m_fp_list`: the list that share-mode checks walk, in
  `ksmbd_smb_check_shared_mode()`. `m_op_list` serves oplock and lease
  breaks.
- Stream name and size: in `struct stream` inside `struct ksmbd_file`, not in
  `struct ksmbd_inode`.
- `struct lease`: refcounted and shared, through `lease->open_list`, by the
  opinfos that `same_client_has_lease()` matched by client GUID and lease
  key on one `struct ksmbd_inode`.
- `struct lease_table`: one per client GUID; links `struct lease`, not
  `struct oplock_info`. `lb->conn` is the conn that created it, counted, and
  is the fallback route for a v2 lease break.
- `struct ksmbd_lock`: linked on `fp->lock_list` by `flist` and on
  `conn->lock_list` by `clist`, holding a conn reference while on
  `conn->lock_list`; `llist` is the request-local list inside `smb2_lock()`.
