# XDR Encode/Decode Failure Handling

Committing a state change (closing a file, revoking a delegation,
modifying a stateid) before verifying that the XDR response encode
succeeds leaves the server in a state the client never learns about.
The client retries the operation, which now fails because the state
has already changed, causing permanent inconsistency.

## Decode Failures

All `xdr_stream_decode_*()` return values must be checked before
using the decoded data. On failure, return `nfserr_bad_xdr` without
modifying any server state. The decode functions in
`fs/nfsd/nfs4xdr.c` consistently follow this pattern.

## Encode Failures and State Ordering

The critical rule: **state changes must not commit if a subsequent
XDR encode fails**.

NFSv4 compound operations in `fs/nfsd/nfs4proc.c` perform the
operation and then encode the response. If the encode step fails
(e.g., `xdr_reserve_space()` returns NULL), the client never
receives the response. If the server has already committed the state
change, the client will retry and hit an error because the state
already changed.

```c
// CORRECT — defer state commit until encode succeeds
tmp_state = perform_operation();
status = xdr_stream_encode_*(...);
if (status < 0) {
    undo_operation(tmp_state);
    return nfserr_resource;
}
commit_state(tmp_state);

// WRONG — state committed before encode
commit_state_change();  // e.g., close file, revoke delegation
status = xdr_stream_encode_*(...);
if (status < 0)
    return nfserr_resource;  // too late, state already changed
```

**REPORT as bugs**: Operations in `fs/nfsd/nfs4proc.c` that modify
persistent server state (close, lock, delegation return, open
downgrade) before the encode step has been verified to succeed.

## Buffer Space Reservation

Before encoding variable-length data, buffer space must be reserved
with `xdr_reserve_space()` or `xdr_reserve_space_vec()`. Encoding
without reservation can overflow the response buffer.

`xdr_reserve_space()` returns NULL if insufficient space remains.
`xdr_reserve_space_vec()` returns a negative error code. Both must
be checked.

## Quick Checks

- **Decode return values**: every `xdr_stream_decode_*()` call must
  have its return value checked before using the decoded data.
- **Encode before commit**: for state-modifying operations, verify
  the encode happens before the state change commits, or that the
  state change can be rolled back on encode failure.
- **Space reservation**: `xdr_reserve_space()` and
  `xdr_reserve_space_vec()` return values must be checked for
  NULL / negative before writing to the buffer.
