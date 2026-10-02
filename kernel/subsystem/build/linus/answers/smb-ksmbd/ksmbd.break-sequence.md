- Wait primitive: `wait_for_break_ack()` uses
  `wait_event_interruptible_timeout()` on `opinfo->oplock_q`; there is no
  op_end_wq and no OPLOCK_WAIT_BREAK.
- State constants in `fs/smb/server/oplock.h`: `OPLOCK_STATE_NONE`,
  `OPLOCK_ACK_WAIT`, `OPLOCK_CLOSING`.
- Oplock holder: the wait is called from `smb2_oplock_break_noti()`, not from
  `oplock_break()` itself.
- Lease holder with write or handle caching: `oplock_break()` sets
  `OPLOCK_ACK_WAIT` but skips `wait_for_break_ack()` when `open_trunc` is set
  and the lease state is exactly `SMB2_LEASE_READ_CACHING_LE |
  SMB2_LEASE_HANDLE_CACHING_LE`.
- Lease break chain: after an acknowledged break `oplock_break()` jumps to
  `again` and sends a further break while the lease is still incompatible;
  each step has its own 35 second wait.
- Timeout with holder in `OPLOCK_CLOSING`: `wait_for_break_ack()` changes
  nothing and returns `false`.
- Timeout on a lease: `lease_update_oplock_levels()` lowers `level` to none on
  every open that shares the lease, not only on the one that was broken.
- After a timeout the caller of `wait_for_break_ack()` calls
  `ksmbd_invalidate_durable_fd()` in `fs/smb/server/vfs_cache.c`, which sets
  `durable_reconnect_disabled` on the holder's file and returns `-ENOENT` on
  every path.
- `oplock_break()` after a timeout: returns `-ENOENT`, not 0.
- `smb_grant_oplock()` on `-ENOENT`: goes to `set_lev`; the request is capped
  at `SMB2_OPLOCK_LEVEL_II` unless the holder was a durable open, which keeps
  the requested level.
- `smb_grant_oplock()` on `-EAGAIN` (oplock holder closed during the break):
  rechecks `ksmbd_smb_check_shared_mode()` and grants the requested level.
- Other callers of `oplock_break()`, for example
  `__smb_break_all_levII_oplock()`: ignore the return value.
- Late oplock acknowledgement: `smb20_oplock_break_ack()` answers a replayed
  request (`smb3_hdr_replay()`) in `OPLOCK_STATE_NONE` with the current level
  and success; a non-replay gets an error status.
- Late lease acknowledgement: `lookup_lease_in_table()` returns only an opinfo
  whose `op_state` is `OPLOCK_ACK_WAIT`, so `smb21_lease_break_ack()` answers
  `STATUS_UNSUCCESSFUL`.
