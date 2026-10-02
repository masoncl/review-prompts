- `nfsd_splice_read()`: page-cache pages placed in the reply, no copy.
- `nfsd_iter_read()`: `vfs_iocb_iter_read()` into `rq_bvec` built from reply
  pages; it does not call `vfs_iter_read()`.
- `nfsd_direct_read()`: reached only from inside `nfsd_iter_read()`.
- There is no rq_splice_ok in this tree, and `nfsd_read_splice_ok()` makes no
  transport test.
- `nfsd_read_splice_ok()`: returns false first if `nfsd_disable_splice_read`
  is set, then for `RPC_AUTH_GSS_KRB5I` and `RPC_AUTH_GSS_KRB5P`.
- NFSv4 READ and READ_PLUS splice only when all of these hold:
  - `nfsd_read_splice_ok()` was true in `nfsd4_decode_compound()`;
  - the compound holds one READ or READ_PLUS in total;
  - the estimated non-read reply fits in `PAGE_SIZE` less the auth slack;
  - the read is the last operation: `nfsd4_read()` in `fs/nfsd/nfs4proc.c`
    clears `argp->splice_ok` when `nfsd4_last_compound_op()` is false;
  - `file->f_op->splice_read` is set.
- READ_PLUS: `nfsd4_encode_read_plus_data()` makes the same choice as
  `nfsd4_encode_read()`; `nfsd4_read()` serves both operations.
- `nfsd4_encode_splice_read()` does not fall back to `nfsd4_encode_readv()`:
  it returns `nfserr_serverfault` if `xdr->buf->page_len` is non-zero and
  `nfserr_resource` if the head has no room left.
- Read I/O mode: the switch on `nfsd_io_cache_read` at the top of
  `nfsd_iter_read()`.
- `NFSD_IO_DIRECT` read: used only if `nf->nf_dio_read_offset_align` is
  non-zero and `rqstp->rq_res.page_len` is zero; otherwise the read is done as
  for `NFSD_IO_DONTCACHE`.
- Selecting `NFSD_IO_DONTCACHE` or `NFSD_IO_DIRECT` for reads sets
  `nfsd_disable_splice_read`, so splice stops for all versions and exports;
  see `nfsd_io_cache_read_set()` in `fs/nfsd/debugfs.c`.
- Clearing `nfsd_disable_splice_read` resets `nfsd_io_cache_read` to
  `NFSD_IO_BUFFERED` (`nfsd_dsr_set()`); setting the mode back to buffered
  does not re-enable splice.
