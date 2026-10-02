- `OP_MODIFIES_SOMETHING`: does not cache anything. It makes the loop call
  `op_rsize_bop` (unchecked for NULL) and `nfsd4_check_resp_size()` before
  the handler, and makes `warn_on_nonidempotent_op()` complain if the reply
  is later truncated.
- `OP_CACHEME`: selects the xid-based DRC, not the session slot.
  `nfsd4_decode_compound()` sets `ntli_cachetype` in
  `struct nfsd_thread_local_info` to `RC_REPLBUFF` if any op has the flag,
  and forces `RC_NOCACHE` when the minor version is non-zero.
- Session slot caching: decided by the client's `cachethis` in
  `nfsd4_sequence()` (`NFSD4_SLOT_CACHETHIS`), by no flag in
  `enum nfsd4_op_flags`.
- `OP_NONTRIVIAL_ERROR_ENCODE`: `nfsd4_encode_operation()` calls the encoder
  although `op->status` is set. In `nfsd4_ops` it is on LOCK, LOCKT, SETATTR
  and SETCLIENTID.
- `ALLOWED_WITHOUT_FH` does not imply `ALLOWED_ON_ABSENT_FS`: with a current
  filehandle on a migrated export, an op with only `ALLOWED_WITHOUT_FH` gets
  `nfserr_moved`.
- **Potentially unsafe usage**: `ALLOWED_WITHOUT_FH` on an op whose handler
  uses `cstate->current_fh`.
  - Unsafe: when the handler dereferences `fh_dentry` or `fh_export`
    without a test; the loop lets it run with both NULL.
  - Safe: the handler tests `fh_dentry` first, as `nfsd4_reclaim_complete()`
    does.
  - Safe: the handler replaces the filehandle, as `nfsd4_putrootfh()` does
    with `fh_put()` and `exp_pseudoroot()`.
- **Unsafe usage**: `OP_NONTRIVIAL_ERROR_ENCODE` with an encoder that
  encodes result fields without looking at its `nfserr` argument, or that
  returns `nfs_ok` when `nfserr` was set.
  - Unsafe: the encoder runs when the handler was skipped (decode error, no
    filehandle, size check), so result fields are unset; its return value
    replaces `op->status`.
  - Safe: switch on `nfserr` and return it, as `nfsd4_encode_lock()` and
    `nfsd4_encode_setattr()` do.
