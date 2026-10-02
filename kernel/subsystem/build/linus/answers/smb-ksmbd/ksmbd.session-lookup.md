- `ksmbd_session_lookup_all_states()` in
  `fs/smb/server/mgmt/user_session.c`: returns a session in any state with a
  reference taken.
- `ksmbd_session_lookup_all_states()` fallback: runs
  `ksmbd_session_lookup_slowpath()` whenever `ksmbd_session_lookup()` misses,
  and keeps the result only if `conn` is a key in `sess->ksmbd_chann_list`;
  `conn->binding` is not tested.
- `ksmbd_session_lookup_all()`: `ksmbd_session_lookup_all_states()` plus the
  `SMB2_SESSION_VALID` filter; it has no caller in this tree.
- Dispatcher: `smb2_check_user_session()` calls
  `ksmbd_session_lookup_all_states()` and filters the state itself.
- `smb2_check_user_session()` returns 0 before any lookup for
  `SMB2_NEGOTIATE_HE` and `SMB2_SESSION_SETUP_HE`; `SMB2_ECHO_HE` is not one
  of them.
- `SMB2_ECHO_HE` with a non-zero `SessionId`, as the first command: the
  session is looked up and kept if valid or Kerberos-expired; a miss is not an
  error.
- Kerberos-expired session (`smb2_session_kerberos_expired()`): the handler
  runs with `work->sess` not in `SMB2_SESSION_VALID` for the commands that
  `smb2_session_expired_cmd_allowed()` accepts; other commands that reach the
  state test get `-EKEYEXPIRED`.
- `smb2_check_user_session()` can return an error with `work->sess` still set:
  on `-EKEYEXPIRED`, and on `-ENOENT` for an encrypted request on an expired
  session with `sess->enc`; a later command of a compound keeps `work->sess`
  on every error.
- `smb3_decrypt_req()`: does no session lookup of its own.
- `ksmbd_get_encryption_key()` in `fs/smb/server/auth.c`: for decryption uses
  `ksmbd_session_lookup_all_states()` and accepts `SMB2_SESSION_VALID`, or
  `SMB2_SESSION_EXPIRED` with `sess->enc`; for encryption uses `work->sess`
  with no new reference.
- Re-authentication in `smb2_sess_setup()`: `ksmbd_session_lookup()`, then
  `ksmbd_session_lookup_slowpath()` accepted only if `lookup_chann_list()`
  finds this connection.
