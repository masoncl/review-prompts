- Before the loop, once: `nfsd_minorversion()` (failure encodes no op at
  all), `nfs41_check_op_ordering()`, `check_if_stalefh_allowed()`. The loop
  itself makes no opnum range test and no SEQUENCE-first test;
  `nfsd4_decode_compound()` did the range test.
- Per-op order in `nfsd4_proc_compound()` in `fs/nfsd/nfs4proc.c`:
  1. `resp->opcnt == NFSD_MAX_OPS_PER_COMPOUND`, minor version 0, client
     sent more ops: `nfserr_resource`.
  2. `op->status` already set: handler skipped; `OP_OPEN` goes through
     `nfsd4_open_omfg()`.
  3. `fh_dentry` NULL: `nfserr_nofilehandle` unless `ALLOWED_WITHOUT_FH`.
  4. Else export has `ex_fslocs.migrated`: `nfserr_moved` unless
     `ALLOWED_ON_ABSENT_FS`.
  5. `fh_clear_pre_post_attrs()`.
  6. `OP_MODIFIES_SOMETHING`: `op_rsize_bop` then
     `nfsd4_check_resp_size()`.
  7. `op_get_currentstateid` if set, then `op_func`.
- `NFSD4_FH_FOREIGN` with `fh_dentry` NULL: the op gets `nfserr_stale`
  unless it is `OP_SAVEFH` or has `ALLOWED_WITHOUT_FH`; so `nfsd4_savefh()`
  can run with no dentry.
- `op_release`: called by the loop, not by `nfsd4_encode_operation()`.
  It runs after the op is encoded, on both the `nfsd4_encode_operation()`
  and the `nfsd4_encode_replay()` path, and also when the handler was
  skipped or failed.
- `op_release` is not called for ops that were decoded but lie after the op
  that ended the loop, nor on the `nfserr_replay_cache` jump.
- `nfsd4_map_status()`: called by `nfsd4_encode_operation()` in
  `fs/nfsd/nfs4xdr.c`, just before it writes the status word; it rewrites
  `op->status`, so the loop sees the mapped value.
- `nfsd4_encode_replay()` path: no `nfsd4_map_status()`; the status is the
  cached `rp_status`.
- Loop end: `status = op->status` is read after encoding, so a handler error,
  a wrongsec failure, or an encode or size failure all end the loop.
- `nfserr_replay_me`: does not end the loop by itself; the loop continues
  when the cached `rp_status` is zero.
- `cstate->status == nfserr_replay_cache` (set by `nfsd4_sequence()`):
  jumps to `out` at once, skipping encode, `op_release` and both `fh_put()`
  calls.
- There is no nfserr_dropit in this tree; `RQ_USEDEFERRAL` is cleared in
  `nfs4svc_decode_compoundargs()` and again in `nfsd4_proc_compound()`, so a
  compound is not deferred once decoding has started.
