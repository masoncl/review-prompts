- Run time, per unset member; there is no NULL test that turns a missing
  entry into `nfserr_notsupp` or `nfserr_op_illegal`:

| Unset | Result |
|---|---|
| `nfsd4_dec_ops` entry | called unchecked in `nfsd4_decode_compound()` |
| `op_rsize_bop` | `BUG_ON()` in `nfsd4_max_reply()` during decode |
| `op_func` | called unchecked in the loop |
| `nfsd4_enc_ops` entry | `BUG_ON()` in `nfsd4_encode_operation()` |

- `nfsd4_enc_ops` `BUG_ON()`: reached only when the encoder would run, that
  is on success or with `OP_NONTRIVIAL_ERROR_ENCODE`.
- `nfsd4_max_reply()` exempts only `OP_ILLEGAL` and `nfserr_notsupp`. The
  all-zero `nfsd4_ops` entries in this tree (for example `OP_DELEGPURGE`)
  survive because their decoder is `nfsd4_decode_notsupp()`.
- Array bounds: `nfsd4_encode_operation()` tests the opnum against
  `ARRAY_SIZE()` of `nfsd4_enc_ops`; the decode and dispatch paths make no
  such test. `nfsd4_dec_ops` and `nfsd4_ops` are indexed by any opnum that
  `nfsd4_opnum_in_range()` accepts, so raising `LAST_NFS42_OP` without an
  entry at that index in both reads past the array.
- The three tables are shared by all minor versions.
  `nfsd4_opnum_in_range()` has only an upper bound per minor version, so a
  v4.0 opnum is accepted in v4.1 and v4.2. A version restriction goes in
  the decoder, as in `nfsd4_decode_release_lockowner()`.
- `op->u` in the inline `iops` is not zeroed between requests: `pc_argzero`
  of COMPOUND stops at `iops` in `struct nfsd4_compoundargs`.
- **Unsafe usage**: an `op_release`, encoder or `op_rsize_bop` that reads a
  field of `op->u` the decoder does not set on every return path.
  - Safe: the decoder clears the struct first; `nfsd4_decode_read()` does
    `memset()` and `nfsd4_read_release()` tests `rd_nf`.
- **Unsafe usage**: a decoder that takes memory or a reference outside
  `argp->to_free` and relies on `op_release` to drop it.
  - Unsafe: `op_release` runs only for ops the loop reached; an op decoded
    after the one that ended the compound never gets it.
  - Safe: allocate with `svcxdr_tmpalloc()`, which
    `nfsd4_release_compoundargs()` frees for every decoded op, as
    `nfsd4_decode_acl()` does.
