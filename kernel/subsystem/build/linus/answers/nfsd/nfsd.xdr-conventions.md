- Every entry of `nfsd4_dec_ops` returns `__be32`; none returns bool.
  `nfsd4_decode_compound()`, its caller `nfs4svc_decode_compoundargs()` and
  the xdrgen functions return bool.
- `nfsd4_decode_compound()` returns false (`nfsd_dispatch()` then answers
  `rpc_garbage_args`) only when the tag, minor version, op count or an
  opnum cannot be read, the tag exceeds `NFSD4_MAX_TAGLEN`, or an
  allocation fails (`svcxdr_savemem()` of the tag, `vcalloc()` of
  `argp->ops`). A failing op decoder never makes it return false.
- `svcxdr_tmpalloc()` memory: freed by `nfsd4_release_compoundargs()` in
  `fs/nfsd/nfs4xdr.c`, the `pc_release` of COMPOUND. `svc_process()` calls
  it through `svc_release_rqst()` after `svc_send()`, and also when the
  request is dropped.
- `args->ops`, when not the inline `iops`: freed there with
  `kvfree_rcu_mightsleep()`, not `vfree()`.
- Encoder return value: `nfsd4_encode_operation()` stores it in
  `op->status`. The function returns void; the loop reads `op->status`
  afterwards.
