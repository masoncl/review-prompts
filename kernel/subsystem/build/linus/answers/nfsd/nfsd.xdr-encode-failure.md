- `op_rsize_bop` returns bytes, not words; the in-tree estimates other than
  `nfsd4_getattr_rsize()` include `op_encode_hdr_size` (opnum and status)
  and multiply by `sizeof(__be32)`.
- `nfsd4_check_resp_size()` knows no session limit of its own; it compares
  against `rq_res.buflen`. `nfsd4_sequence()` lowered that with
  `xdr_restrict_buflen()` to at most `maxresp_cached` or `maxresp_sz`, less
  `rq_auth_slack`.
- `nfsd4_sequence()` fails with `nfserr_rep_too_big` or
  `nfserr_rep_too_big_to_cache` when `xdr_restrict_buflen()` fails, before
  any later op runs.
- Encoder failure after the handler ran: `nfsd4_encode_operation()` turns
  `nfserr_resource` into `nfserr_rep_too_big_to_cache` or
  `nfserr_rep_too_big` when there is a session, truncates the op to opnum
  plus status, and the compound ends. The operation's effect is not undone.
- `op_rsize_bop` is called from `nfsd4_max_reply()` during decode, before
  any handler has run, and also for an op whose decoder failed. The in-tree
  estimates use only decoded arguments and `nfsd4_max_payload()`.
- **Unsafe usage**: an `OP_MODIFIES_SOMETHING` op whose encoder can emit
  more bytes than `op_rsize_bop` returned.
  - Safe: a fixed worst case that covers every field the encoder writes, as
    `nfsd4_write_rsize()` does for `nfsd4_encode_write()`.
