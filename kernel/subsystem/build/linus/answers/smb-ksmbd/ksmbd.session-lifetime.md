- `__session_create()` in `fs/smb/server/mgmt/user_session.c`: sets `refcnt`
  to 2 and itself adds the session to `sessions_table`.
- Table reference: one, shared by `sessions_table` and `conn->sessions`.
- Second reference: returned to `smb2_sess_setup()`, which stores it in
  `work->sess`; `smb2_sess_setup()` takes no extra get for a new session.
- There is no ksmbd_expire_session(), ksmbd_sessions_deregister() or
  SMB2_SESSION_TIMEOUT in this tree.
- `ksmbd_session_register()`: takes no reference; returns `-ENOSPC` when
  `ksmbd_too_many_session_setups()` counts `KSMBD_MAX_PENDING_SESSIONS`
  in-progress sessions on the connection.
- `ksmbd_session_register()` failure: unhashes the session and puts the table
  reference; the caller still owns its own reference.
- Paths that drop the table reference:

| Path | Condition | How |
|---|---|---|
| `ksmbd_session_register()` | its own failure | `ksmbd_user_session_put()` |
| `ksmbd_too_many_session_setups()` | `SMB2_SESSION_IN_PROGRESS`, `refcnt <= 1`, idle past `KSMBD_UNAUTHENTICATED_CONN_TIMEOUT` | `ksmbd_session_destroy()` directly |
| `ksmbd_session_unregister()` | session still hashed | `ksmbd_user_session_put()` |
| `ksmbd_conn_sessions_cleanup()` | this connection had a channel on the session or holds it in `conn->sessions`, and the channel list is empty once that channel is deleted | `atomic_dec_and_test()`, then destroy |

- `ksmbd_session_unregister()`: one caller, the failure path of
  `smb2_sess_setup()`; it also erases the session from `conn->sessions` of
  every channel connection.
- `ksmbd_expire_sessions()`: only changes `SMB2_SESSION_VALID` to
  `SMB2_SESSION_EXPIRED` once `sess->kerberos_expiry` has passed; drops no
  reference.
- `smb2_session_logoff()` and `destroy_previous_session()`: set
  `SMB2_SESSION_EXPIRED` and drop no reference; the session stays in both
  tables until one of the four paths above runs.
- `ksmbd_session_destroy()`: frees the tree connects, file table, `sess->user`,
  RPC handles, channel list and `Preauth_HashValue` along with the session.
