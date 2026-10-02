- Models take ksmbd to have no message id window. This tree has one:
  `smb2_check_sequence_number()` in `fs/smb/server/smb2misc.c`, called at the
  end of `ksmbd_smb2_check_message()`, after the credit charge check.
- State: `seq_low`, `seq_high` and `seq_bitmap` in `struct ksmbd_conn`
  (`fs/smb/server/connection.h`); the granted range is `[seq_low, seq_high)`,
  a set bit means granted and not yet used.
- Lock: `conn->credits_lock`; there is no separate sequence lock. The credit
  check and the sequence check are two separate critical sections.
- Ids consumed by a request: `CreditCharge` consecutive ids from `MessageId`,
  or 1 when `CreditCharge` is 0.
- Rejected: `MessageId + charge` wraps, any part of the range is outside
  `[seq_low, seq_high)`, or any id in it has its bit clear (already used).
- On rejection: `ksmbd_smb2_check_message()` calls `ksmbd_conn_set_exiting()`
  and returns 1; it does not call `ksmbd_conn_abort()`.
- Result for the request: `__process_request()` sets
  `STATUS_INVALID_PARAMETER` and aborts the loop; the response still goes to
  `ksmbd_conn_write()`; the reader loop ends at its next `ksmbd_conn_alive()`
  test.
- On acceptance: the bits are cleared and `seq_low` advances past used ids.
- `SMB2_CANCEL`: exempt, consumes no id.
- Compound: each command is checked with its own `MessageId`.
- Window growth: only in `smb2_set_rsp_credits()`, by the credits granted.
- Start: `ksmbd_conn_alloc()` sets the window to id 0 only. An SMB1 negotiate
  consumes id 0 in `ksmbd_verify_smb_message()`.
- `KSMBD_CMD_SEQ_WINDOW`: 8192, indexes `seq_bitmap` as a ring;
  `init_smb2_max_credits()` clamps `max_credits` to `SMB2_MAX_CREDITS` to match.
- `struct ksmbd_conn` has no req_hdr_id field and no field named `credits`.
