- `smb2_validate_credit_charge()`: on success adds the charge to
  `conn->outstanding_credits` and stores it in `work->credit_charge`, except
  for `SMB2_CANCEL`, where it returns 0 and takes nothing; it does not change
  `conn->total_credits`. On any failure it takes nothing.
- Gate: `conn->vals->req_capabilities & SMB2_GLOBAL_CAP_LARGE_MTU`; every
  table in `fs/smb/server/smb2ops.c` sets that bit statically. The server code
  does not use a field named `capabilities`.
- Required charge: `SMB2_QUERY_DIRECTORY` counts too, by
  `OutputBufferLength`.
- `smb2_set_rsp_credits()`: subtracts the charge from `total_credits` and
  `outstanding_credits`, clears `work->credit_charge`, then adds the grant to
  `total_credits`.
- Grant: also capped by `conn->seq_low + KSMBD_CMD_SEQ_WINDOW -
  conn->seq_high`, so it can be 0; the grant extends `seq_high` and sets the
  new bits in `seq_bitmap`.
- `CreditRequest` in the response: `smb2_set_rsp_credits()` writes the grant
  only when the command has `NextCommand == 0`, as the sum in
  `work->credits_granted`.
- `smb2_set_rsp_credits()` returns `-EINVAL` when `total_credits` exceeds
  `conn->vals->max_credits` or the charge exceeds `total_credits`; the
  dispatcher sets `STATUS_INVALID_PARAMETER` and goes to `send:`.
- Handler error with a response: `__process_request()` returns
  `SERVER_HANDLER_CONTINUE`, so `smb2_set_rsp_credits()` runs as usual.
- `SERVER_HANDLER_ABORT` (failed message check, bad command, signing failure,
  `send_no_response`): `smb2_set_rsp_credits()` does not run. At `send:`,
  `__handle_ksmbd_work()` subtracts `work->credit_charge` from
  `outstanding_credits`; `total_credits` is unchanged and nothing is granted.
- Session or tree connect failure: reaches `send:` before the message check;
  `work->credit_charge` is 0 and nothing is released or granted.
- `smb2_send_interim_resp()`: copies the header at `ksmbd_resp_buf_next()`
  before credits are set for that command; it changes no credit state.
- `conn->credits_lock`: held for every access to `total_credits`,
  `outstanding_credits`, `seq_low`, `seq_high` and `seq_bitmap` on the SMB2
  request path; `smb2_set_rsp_credits()` runs with it held by the dispatcher.
