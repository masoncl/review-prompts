- Models take `conn->session_lock` and `sessions_table_lock` to be rwlocks.
  Here they are `struct rw_semaphore`, as are `sess->chann_lock` and
  `sess->rpc_lock`; none may be taken in a cancel callback. `conn_list` is
  keyed by `conn->inet_hash` for TCP; SMB Direct connections are added with
  key 0. `inode_hash_lock` remains an rwlock.
- Models look for ksmbd_vfs_kern_path_locked(). There is no such function
  here; `ksmbd_vfs_kern_path_start_removing()` in `fs/smb/server/vfs.c` is
  the locked lookup.
- Models take the handler's lookup reference to be all a request holds on an
  open. Here `smb2_set_request_open()` also counts the request on the handle
  by channel sequence when its caller passes `verify_chseq` and the dialect
  is `SMB30_PROT_ID` or later; `smb2_complete_request_open()` undoes the
  count.
- Models expect an interim_entry member in `struct ksmbd_work`. There is no
  interim_entry here.
- Models take CHANGE_NOTIFY to be unimplemented or an ordinary blocking
  handler. Here `__ksmbd_close_fd()` completes a parked CHANGE_NOTIFY with
  `STATUS_NOTIFY_CLEANUP`.
- Models know no compression path. Here response compression is requested
  only by `smb2_read()`, which sets `work->compress_response`.
- Models know no per-share encryption check. Here `smb2_tree_connect()`
  refuses a share with `KSMBD_SHARE_FLAG_ENCRYPT_DATA` when
  `smb3_encryption_negotiated()` is false.
- Models know no session expiry timer. Here
  `ksmbd_session_expiration_worker()` in `fs/smb/server/connection.c` runs
  `ksmbd_expire_sessions()` and aborts idle connections older than
  `KSMBD_UNAUTHENTICATED_CONN_TIMEOUT` with no valid or expired session. The
  dispatcher maps `-EKEYEXPIRED` to `STATUS_NETWORK_SESSION_EXPIRED`.
- Models take logoff to only mark the session expired. Here
  `smb2_session_logoff()` and `destroy_previous_session()` first set
  `sess->tearing_down` under `sess->chann_lock` and set the bound
  connections to `KSMBD_SESS_NEED_RECONNECT` with
  `ksmbd_all_conn_set_status()`.
- Models take a durable reconnect to need only `fp->conn == NULL` and an
  unexpired timeout. Here `ksmbd_lookup_durable_fd()` also refuses
  `durable_reconnect_disabled`, and for a handle with an opinfo
  `smb2_check_durable_oplock()` compares the owner with
  `ksmbd_vfs_compare_durable_owner()`.
- Models do not say where file ids start. Here ids start at
  `KSMBD_START_FID`; see `fs/smb/server/vfs_cache.h`.
- Models take `smb2_lock()` to link each lock on `conn->lock_list` as it is
  granted. Here it publishes the batch on `conn->lock_list` and
  `fp->lock_list` only after the response is pinned.
- Models know no procfs interface. Here `fs/smb/server/proc.c` is built under
  `CONFIG_PROC_FS`; most show functions are outside it, beside their data,
  for example `proc_show_clients()` takes `conn_list_lock`,
  `show_proc_sessions()` takes `sessions_table_lock` and `proc_show_files()`
  takes `global_ft.lock`; `ksmbd_session_destroy()` removes the per-session
  entry.
