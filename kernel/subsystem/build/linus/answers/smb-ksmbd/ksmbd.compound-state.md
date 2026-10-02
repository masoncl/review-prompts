- `smb_get_msg()` in `fs/smb/server/smb_common.h` returns the first command;
  there is no smb2_get_msg() in this tree.
- `ksmbd_req_buf_next()`, `ksmbd_resp_buf_next()`, `ksmbd_resp_buf_curr()`:
  static inlines in `fs/smb/server/ksmbd_work.h`.
- `smb2_current_req_len()` in `fs/smb/server/smb2pdu.c`: length of the current
  command (`NextCommand`, else the rest of the PDU); it is static.
- `KSMBD_NO_FID` is `INT_MAX`; `has_file_id()` is `id < KSMBD_NO_FID`.
  `SMB2_NO_FID` is the all-ones value. Both are in
  `fs/smb/server/vfs_cache.h`.
- `init_chained_smb2_rsp()` stores `compound_fid` and `compound_pfid` after a
  successful CREATE, and also after a successful FLUSH, READ or WRITE whose
  request carried a real file id.
- Failed CREATE: resets both ids to `KSMBD_NO_FID` and stores the status in
  `work->compound_status`.
- Other failed command: stores `compound_status` only if that request had
  `SMB2_FLAGS_RELATED_OPERATIONS`.
- Next request without `SMB2_FLAGS_RELATED_OPERATIONS`: ids reset to
  `KSMBD_NO_FID`, `compound_status` to `STATUS_SUCCESS`.
- `smb2_compound_has_failed()`: true for a later command when `compound_fid`
  is not a file id and `compound_status` is not `STATUS_SUCCESS`; it writes the
  stored status as the error response. Handlers call it once they have the
  request and response buffers, and return when it is true; search for its
  callers.
- Later response headers: `init_chained_smb2_rsp()` sets
  `SMB2_FLAGS_RELATED_OPERATIONS` on each, whatever the request flag.
- `is_chained_smb2_message()` stops chaining, with no response for the
  remaining commands, when the next header does not fit in the request or
  when fewer than `MAX_CIFS_SMALL_BUFFER_SIZE` bytes of `work->response_sz`
  remain.
- `work->compound_sid`: read only by `smb2_close()`;
  `smb2_check_user_session()` does not use it.
- `smb2_check_user_session()`, later command, beyond the id match:
  - NEGOTIATE, SESSION_SETUP and ECHO return 0, so `get_ksmbd_tcon` is skipped;
  - `ksmbd_conn_good()` false gives `-EIO`;
  - session state other than `SMB2_SESSION_VALID` gives `-EINVAL`, or
    `-EKEYEXPIRED` after Kerberos expiry unless
    `smb2_session_expired_cmd_allowed()` accepts the command.
- `smb2_get_ksmbd_tcon()`, later command, beyond the id match:
  - TREE_CONNECT, CANCEL and LOGOFF return 0 without a check;
  - empty `tree_conns` or `t_state != TREE_CONNECTED` gives `-ENOENT`.
- **Potentially unsafe usage**: taking the request or response with
  `smb_get_msg()`.
  - Unsafe: in a handler that runs with `work->next_smb2_rcv_hdr_off` set; it
    parses the first command and overwrites the first response.
  - Safe: in code that runs once before the loop, as `init_smb2_rsp_hdr()` and
    `smb2_allocate_rsp_buf()` do.
  - Safe: after a test of `work->next_smb2_rcv_hdr_off`, as `__wbuf()` behind
    `WORK_BUFFERS()` does.
- **Potentially unsafe usage**: passing the request's `VolatileFileId` to a
  lookup in a handler that may be a later command.
  - Unsafe: with `ksmbd_lookup_fd_fast()`, which does no substitution; the
    placeholder id finds nothing.
  - Safe: with `ksmbd_lookup_fd_slow()`, which substitutes `compound_fid` and
    `compound_pfid` when `has_file_id()` is false.
  - Safe: after substituting by hand, as `smb2_ioctl()` does before its
    `ksmbd_lookup_fd_fast()` calls.
