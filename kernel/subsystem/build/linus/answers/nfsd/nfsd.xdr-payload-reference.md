- `nfsd4_write()` passes `wr_payload` to `nfsd_vfs_write()` in
  `fs/nfsd/vfs.c`, which calls `xdr_buf_to_bvec()` into `rqstp->rq_bvec`.
  There is no svc_fill_write_vector() in this tree.
- `nfsd4_decode_setxattr()`: `nfsd4_vbuf_from_vector()` copies into
  `svcxdr_tmpalloc()` memory only when the value is larger than the head of
  the subsegment; otherwise `setxa_buf` points into the receive buffer.
- `svcxdr_savemem()`: returns the `xdr_inline_decode()` pointer unchanged
  unless it is the stream's scratch buffer; names, opaques and the tag from
  it normally point into the receive buffer too.
- Lifetime: decoder output, in place or from `svcxdr_tmpalloc()`, may be
  used by the handler, the encoder and `op_release`, all of which run in the
  nfsd thread before `nfsd4_release_compoundargs()`.
- **Unsafe usage**: keeping a pointer the decoder produced in an object that
  outlives the RPC.
  - Safe: copy it into separately allocated memory before the handler
    returns, as `nfsd4_copy()` does for `cp_src` with `dup_copy_fields()`.
