# io_uring Subsystem Delta

## io_uring-Specific Patterns [URING]

### Zero-Copy Lifetime Management

**Critical Rule**: Zero-copy operations decouple request completion from buffer release. The network stack or block layer may retain references to buffers long after the io_uring request completes.

**Key Objects**:
- `req` (struct io_kiocb): The io_uring request, completed when the operation finishes
- `notif` (struct io_kiocb): The notification request, completed when zero-copy transmission finishes
- `buf_node` (struct io_rsrc_node): Reference to registered buffer, must live until transmission completes

**Lifetime Rules**:
1. Normal requests: `req` lifetime = operation lifetime
2. Zero-copy requests: `req` lifetime < buffer usage lifetime
3. Zero-copy buffer references must be attached to `notif`, not `req`
4. The `notif` is completed via callback (`io_tx_ubuf_complete()`) when network/block layer releases buffers
5. Registered buffer nodes attached to `req` will be released when `req` completes
6. Registered buffer nodes attached to `notif` will be released when zero-copy completes

**Zero-Copy Operations**:
- `IORING_OP_SEND_ZC`: Zero-copy send
- `IORING_OP_SENDMSG_ZC`: Zero-copy sendmsg (vectored)
- Any operation using `MSG_ZEROCOPY` flag
- Any operation importing registered buffers for zero-copy transmission

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
- Network sockets: Managed separately via sock_hold/sock_put

## Load io_uring specific patterns:
- **ZC-001** (patterns/ZC-001.md): Zero-copy buffer lifetime validation — Mandatory when zero-copy operations use registered buffers
