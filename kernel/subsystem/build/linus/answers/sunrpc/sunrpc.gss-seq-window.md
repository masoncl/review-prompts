- `svcauth_gss_accept()`: turns the `SVC_DROP` from
  `svcauth_gss_verify_header()` into `SVC_CLOSE` at its `drop:` label.
- `MAXSEQ` (0x80000000, `include/linux/sunrpc/auth_gss.h`): the test is
  `gc_seq > MAXSEQ`, so `MAXSEQ` itself is accepted.
- Above `MAXSEQ`: `SVC_DENIED` with `rpcsec_gsserr_ctxproblem`, an auth-error
  reply; the connection is not closed.
