- Dispatcher reference: put by `__handle_ksmbd_work()` in
  `fs/smb/server/server.c`, after `encrypt_resp` and before
  `ksmbd_conn_write()`; `work->sess` is not cleared afterwards.
- `ksmbd_free_work_struct()`: puts no session.
- `ksmbd_user_session_get()`: called only by the lookup functions and the
  procfs show functions; apart from the session tables, no object that
  outlives the request holds a session reference.
- `sess` in `struct oplock_info`: set by `alloc_opinfo()` with no reference;
  for where it is set to NULL and set again, see "Oplock object lifetime".
- `sess->user`: freed only by `ksmbd_session_destroy()`; a session reference
  keeps it alive.
- `smb2_sess_setup()`: assigns `work->sess` with no put of an earlier value;
  as the first command `work->sess` is NULL on entry, because
  `smb2_check_user_session()` does no lookup for `SMB2_SESSION_SETUP_HE`.
- **Unsafe usage**: putting `work->sess` in a handler and leaving the pointer
  set; `__handle_ksmbd_work()` puts it a second time.
  - Safe: put, then set `work->sess = NULL`, as the failure path of
    `smb2_sess_setup()` and `smb2_check_user_session()` do.
- **Potentially unsafe usage**: storing in `work->sess` a pointer that carries
  no reference.
  - Unsafe: on a work that reaches the put at `send:` in
    `__handle_ksmbd_work()`; the count drops below what the owners hold and
    `ksmbd_session_destroy()` runs early.
  - Safe: on a work that never passes through `__handle_ksmbd_work()`, cleared
    again while the lending work still holds its reference, as
    `smb2_send_interim_work()` does around `encrypt_resp`.
- **Unsafe usage**: using `work->sess` of a work that outlives its request;
  the dispatcher has put the reference and `ksmbd_session_destroy()` frees
  the session on the last put.
  - Safe: look the session up again by id and put it after use, as
    `smb2_send_notify_cancelled()` does with `ksmbd_session_lookup()`.
- **Potentially unsafe usage**: acting on a session from
  `ksmbd_session_lookup_slowpath()` for the current connection.
  - Unsafe: when nothing ties the session to the connection; the global table
    holds the sessions of every client.
  - Safe: after the connection is found in `sess->ksmbd_chann_list`, as the
    re-authentication branch of `smb2_sess_setup()` does with
    `lookup_chann_list()` and `ksmbd_session_lookup_all_states()` does with
    `xa_load()` under `sess->chann_lock`.
