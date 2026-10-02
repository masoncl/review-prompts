- Binding flag: `SMB2_SESSION_REQ_FLAG_BINDING` in `fs/smb/common/smb2pdu.h`;
  there is no SMB2_SESSION_FLAG_BINDING.
- Zero `SessionId`: always takes the new-session branch, whatever the flags.
- Binding on `SMB311_PROT_ID`: `conn->cipher_type` must also equal the cipher
  of the connection in the first entry of `sess->ksmbd_chann_list`, else
  `-EINVAL`; the check sits between the dialect check and the
  `SMB2_FLAGS_SIGNED` check.
- Binding flag with a dialect below `SMB30_PROT_ID` and a non-zero
  `SessionId`: `-EACCES`.
- Binding flag on SMB3 without `KSMBD_GLOBAL_FLAG_SMB3_MULTICHANNEL`: handled
  by the re-authentication branch, not rejected with `-EACCES`.
- Re-authentication branch: has no `user_guest()` test; that test is in the
  binding branch only.
- Re-authentication of an `SMB2_SESSION_EXPIRED` session: `-EFAULT`, unless
  `sess->kerberos_expiry` is set and has passed; then
  `work->session_setup_reauth` is set and the state goes back to
  `SMB2_SESSION_IN_PROGRESS`.
- Same-user check on a valid session: done by `ksmbd_compare_user()` inside
  `ntlm_authenticate()` and `ksmbd_krb5_authenticate()`, after the branch
  checks; a mismatch returns `-EKEYREJECTED`.
- `SMB2_SESSION_VALID` and `ksmbd_conn_set_good()`: set by
  `smb2_sess_setup()` itself, after the authenticate function returns 0,
  unless `ksmbd_conn_need_reconnect()` is true.
- `register_session_channel()`: returns `-ESHUTDOWN` when `sess->tearing_down`
  is set and `-ENOSPC` at `KSMBD_MAX_CHANNELS`.
- Failure, non-binding session in `SMB2_SESSION_IN_PROGRESS`:
  `ksmbd_session_unregister()` removes it from the tables at once; the state
  is not changed.
- Failure, non-binding session not in progress: `sess->state` becomes
  `SMB2_SESSION_EXPIRED` and `sess->kerberos_expiry` 0; it stays in the tables.
- Failure, binding request: the failure path does not change the session
  state.
- Failure, `work->sess`: put and set to NULL, except for a binding request
  whose session is already in `work->sess`; that reference stays so the error
  response can be signed, and the dispatcher puts it.
- Failure, channels: the failure path does not call `ksmbd_chann_del()`; it is
  static in `fs/smb/server/mgmt/user_session.c` and called only by
  `ksmbd_conn_sessions_cleanup()`.
- Failure, `struct preauth_session`: removed only when the dialect is
  `SMB311_PROT_ID` and the request has the binding flag.
- Failure, connection state: changed only for a user with
  `KSMBD_USER_FLAG_DELAY_SESSION`; it is need-reconnect during the sleep and
  need-setup after it.
- `conn->mechToken`: freed on success too; `conn->binding` is reset to false
  on failure.
