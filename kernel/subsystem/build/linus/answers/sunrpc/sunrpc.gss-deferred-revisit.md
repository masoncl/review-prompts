- Tests of `rq_deferred`: exactly three, in `svcauth_gss_verify_header()`,
  `svcauth_gss_unwrap_integ()` and `svcauth_gss_unwrap_priv()`;
  `svcauth_gss_accept()` has none of its own.
- `svcauth_gss_verify_header()` on a revisit: still decodes the verifier and
  checks its flavor and length, then skips the header `gss_verify_mic()`, the
  `MAXSEQ` test and `gss_check_seq_num()`.
- `svcauth_gss_unwrap_integ()` on a revisit: returns 0 without running the
  body `gss_verify_mic()` or `xdr_truncate_decode()`.
- `svcauth_gss_unwrap_priv()` on a revisit: decodes the length word, skips the
  length checks and `gss_unwrap()`, and still decodes and compares the
  embedded sequence number.
- `svc_defer()`: saves `rq_arg.len` bytes of the request as it stands at
  deferral, plus addresses and `rq_xprt_ctxt`; it saves no verification
  result, and `svc_revisit()` restores none.
- Deferral point: `svcauth_gss_set_client()` runs after
  `svcauth_gss_accept()`, so the body has already been unwrapped when the copy
  is made.
- Repeating `gss_unwrap()`: wrong; the first pass decrypted in place and
  shrank the buffer, so the saved bytes are plaintext.
- Repeating the body `gss_verify_mic()`: wrong; `xdr_truncate_decode()` had
  already subtracted the checksum from `rq_arg.len`, so the saved copy no
  longer carries the complete message.
- Context-init path: `svcauth_gss_proc_init()` and
  `svcauth_gss_legacy_init()` have no `rq_deferred` test; a request deferred
  by the `cache_check()` on `rsi_cache` is processed again in full.
