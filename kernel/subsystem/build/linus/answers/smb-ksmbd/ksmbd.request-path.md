- `handle_ksmbd_work()`: calls `__handle_ksmbd_work()` once; the per-command
  loop is inside `__handle_ksmbd_work()` in `fs/smb/server/server.c`.
- Reader throttle: `ksmbd_conn_handler_loop()` waits while `conn->req_running`
  would exceed `server_conf.max_inflight_req` (default `SMB2_MAX_CREDITS`), not
  `conn->vals->max_credits`.
- Minimum sizes in the reader: `SMB1_MIN_SUPPORTED_PDU_SIZE`,
  `SMB2_MIN_SUPPORTED_PDU_SIZE`, `SMB2_TRANSFORM_MIN_SUPPORTED_PDU_SIZE` in
  `fs/smb/server/connection.c`; there are no SMB1_MIN_SUPPORTED_HEADER_SIZE or
  SMB2_MIN_SUPPORTED_HEADER_SIZE here.
- Compressed PDU (`SMB2_COMPRESSION_TRANSFORM_ID`): the reader thread replaces
  `conn->request_buf` with the decompressed PDU in `ksmbd_decompress_request()`
  before `ksmbd_smb_request()`; failure ends the connection loop.
- `queue_ksmbd_work()`: calls `ksmbd_init_smb_server()` first; if that fails it
  returns 0, no work is queued, no response is sent, the reader keeps going.
- Once per message, before the loop, on a transform header: `decrypt_req`,
  then `ksmbd_decompress_work_request()` if the plaintext is a compression
  transform, then a re-check of `ProtocolId` and of
  `sizeof(struct smb2_pdu)`.
- Failure of decrypt, decompress or that re-check: `ksmbd_conn_abort()` and
  return; no response. Failure of `allocate_rsp_buf`: return; no response.
- Per command, in this order:
  1. `check_user_session`, for every command including the first;
  2. `get_ksmbd_tcon` when step 1 returned > 0, then `STATUS_ACCESS_DENIED` if
     the share has `KSMBD_SHARE_FLAG_ENCRYPT_DATA` and `work->encrypted` is
     false;
  3. `__process_request()`;
  4. `set_rsp_credits` under `conn->credits_lock`;
  5. `smb2_complete_request_open()`;
  6. `is_chained_smb2_message()`, which advances to the next command;
  7. `set_sign_rsp`, on the response at `ksmbd_resp_buf_curr()`.
- `__process_request()` with `work->sess->sign` set, `work->encrypted` false
  and an unsigned request: `STATUS_ACCESS_DENIED` and `SERVER_HANDLER_ABORT`,
  before `check_sign_req` is considered.
- `check_conn_state()` returning 1: `__process_request()` returns
  `SERVER_HANDLER_CONTINUE` without running the message check or the handler.
- `SERVER_HANDLER_ABORT` is returned for: failed `ksmbd_verify_smb_message()`,
  command >= `conn->max_cmds`, NULL `proc`, the two signing failures, and
  `work->send_no_response` after the handler. The dispatcher calls
  `smb2_complete_request_open()` and breaks the loop, so steps 4, 6 and 7 do
  not run for that command.
- `goto send` (skipping the rest of the loop): session failure, tree connect
  failure, the share encryption test, and `set_rsp_credits` returning < 0.
- ksmbd has no `is_chained_work()`; that name is a static function in
  `kernel/workqueue.c`. `is_chained_smb2_message()` in
  `fs/smb/server/smb2pdu.c` is the chain test.
- Once per message at `send:`, in order: `smb2_complete_request_open()`,
  release of a leftover `work->credit_charge`, `ksmbd_tree_connect_put()`,
  `smb3_preauth_hash_rsp()`, `ksmbd_compress_response()` when
  `work->compress_response`, `encrypt_resp`, `ksmbd_user_session_put()`,
  `ksmbd_conn_write()`.
