- NFSv4 resync: the `release:` label at the end of `nfsd4_encode_operation()`
  in `fs/nfsd/nfs4xdr.c` sets `rq_next_page = xdr->page_ptr + 1`.
- That resync runs for every operation that reaches
  `nfsd4_encode_operation()`, including the early exits that jump to
  `release:`.
- `nfs4svc_encode_compoundres()` does not touch `rq_next_page`.
- `svcxdr_init_encode()` starts `xdr->page_ptr` at `rq_res.pages - 1`, which is
  `&rq_respages[0]`.
- NFSv2 and NFSv3 encoders, and `nfsd4_encode_splice_read()`, sync in the
  other direction: `svcxdr_encode_opaque_pages()` in
  `include/linux/sunrpc/svc.h` sets `xdr->page_ptr = rq_next_page - 1`.
- There is no common NFSv2/v3 resync; the procedure must have moved
  `rq_next_page` past the payload pages before `pc_encode` runs.
- `nfsd3_proc_read()` records `resp->pages` and lets `nfsd_read()` advance
  `rq_next_page`.
- **Potentially unsafe usage**: leaving `rq_next_page` anywhere but one past
  the last page the reply uses.
  - Unsafe: when a slot the reply uses is at or above `rq_next_page`;
    `svc_rqst_release_pages()` and `svc_alloc_arg()` skip it, so the next
    request writes into a page that may still be queued for sending.
  - Safe: when `rq_next_page` is above the last page used, as
    `nfsd_iter_read()` leaves it after a short read;
    `svc_rqst_release_pages()` releases every slot below `rq_next_page` and
    `svc_alloc_arg()` refills them.
  - Safe: `nfsd3_init_dirlist_pages()` advances over the whole buffer, and
    `nfsd3_proc_readdir()` then sets `rq_next_page = resp->xdr.page_ptr + 1`
    only to avoid recycling unused pages.
