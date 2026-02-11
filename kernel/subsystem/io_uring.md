# io_uring Subsystem Details

## Zero-Copy Lifetime Management

Releasing registered buffers while zero-copy transmission is still in flight
causes use-after-free. This happens when `buf_node` is attached to the
io_uring request (`req`) instead of the notification request (`notif`),
because `req` completes before the network or block layer finishes with
the buffers.

**Key Objects**:
- `req` (struct io_kiocb): The io_uring request, completed when the operation finishes
- `notif` (struct io_kiocb): The notification request, completed when zero-copy transmission finishes
- `buf_node` (struct io_rsrc_node): Reference to registered buffer, must live until transmission completes

**Lifetime Rules**:
1. Normal requests: `req` lifetime = operation lifetime
2. Zero-copy requests: `req` lifetime < buffer usage lifetime
3. Zero-copy buffer references must be attached to `notif`, not `req`
4. The `notif` is completed via callback (`io_tx_ubuf_complete()`) when network/block layer releases buffers

**Zero-Copy Operations**:
- `IORING_OP_SEND_ZC`: Zero-copy send
- `IORING_OP_SENDMSG_ZC`: Zero-copy sendmsg (vectored)

Internally, these opcodes set `MSG_ZEROCOPY` on `msg_flags` via `io_send_zc_prep()`.

## Request Lifecycle

**Normal Operation**:
```
prep → issue → complete → cleanup
```

**Zero-Copy Operation**:
```
prep → issue → req complete → [buffers still in use] → notif callback → notif complete
                     ↑                                                           ↑
                req cleanup                                              buf_node cleanup
```

## Resource Attachment Rules

- Files: Attach to `req->file_node` (released at req cleanup)
- Buffers (normal ops): Attach to `req->buf_node` (released at req cleanup)
- Buffers (zero-copy ops): Attach to `notif->buf_node` (released at notif cleanup)
- Network sockets: Accessed through `req->file`, lifetime managed by file references

## Buffer Import Attachment

When a zero-copy operation imports a registered buffer, the import call
determines which `io_kiocb` the `buf_node` is attached to. Both
`io_import_reg_buf()` and `io_import_reg_vec()` call
`io_find_buf_node()`, which attaches `buf_node` directly to the
passed `io_kiocb`. The `io_kiocb` that receives the
`buf_node` is the first argument to `io_import_reg_buf()` and the
third argument to `io_import_reg_vec()`.

**Correct attachment** — pass the `notif`:
```c
io_import_reg_buf(sr->notif, ...)
io_import_reg_vec(ITER_SOURCE, &msg_iter, sr->notif, ...)
```

**Incorrect attachment** — pass the `req`:
```c
io_import_reg_buf(req, ...)
io_import_reg_vec(ITER_SOURCE, &msg_iter, req, ...)
```

**REPORT as bugs**: Any buffer import call in a zero-copy operation that
passes `req` instead of `notif` (or `sr->notif` / `zc->notif` — both
are `struct io_sr_msg *`, named differently across functions).

## Vectored vs Non-Vectored Consistency

When reviewing new vectored zero-copy operations, compare with the
non-vectored equivalent. `IORING_OP_SEND_ZC` uses `io_send_zc_import()`
which correctly calls `io_import_reg_buf(sr->notif, ...)`.
`IORING_OP_SENDMSG_ZC` and any new vectored variants must follow the same
pattern. Inconsistency between vectored and non-vectored buffer attachment
is a strong signal for a bug.

## Quick Checks

- **Notif allocation before import**: Verify `io_alloc_notif()` is called
  before any buffer import in zero-copy paths. The notif (typically
  `sr->notif` or `zc->notif`) must exist before it can receive `buf_node`.
- **Zero-copy flag detection**: Operations using `IORING_OP_SEND_ZC`,
  `IORING_OP_SENDMSG_ZC`, or `IORING_RECVSEND_FIXED_BUF` with a
  zero-copy opcode all require buffer lifetime validation.
