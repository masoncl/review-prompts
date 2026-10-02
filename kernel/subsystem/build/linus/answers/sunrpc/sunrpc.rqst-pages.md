- Two arrays, allocated separately in `svc_init_buffer()`: `rq_pages` holds
  the Call, `rq_respages` holds the Reply; `rq_respages` is not a pointer
  into `rq_pages`.

| Field | Array | Meaning |
|---|---|---|
| `rq_maxpages` | both | usable entries per array; each allocation has one more entry, a NULL sentinel |
| `rq_pages_nfree` | `rq_pages` | number of leading entries `svc_alloc_arg()` must refill |
| `rq_next_page` | `rq_respages` | next reply slot; also the end of the range released and refilled |
| `rq_page_end` | `rq_respages` | `&rq_respages[rq_maxpages]`, set by `svc_alloc_arg()` |

- `svc_serv_maxpages()` sizes each array, not the pair.
- `svc_init_buffer()` allocates no pages; it sets `rq_pages_nfree` and
  `rq_next_page` so that the first `svc_alloc_arg()` fills both arrays.
- `svc_alloc_arg()` does not scan the whole arrays: it refills
  `rq_pages[0 .. rq_pages_nfree)` and `rq_respages` up to `rq_next_page`,
  then resets `rq_next_page` to `rq_respages`.
- `svc_rqst_release_pages()` walks `rq_respages` only; `svc_xprt_release()`
  releases no `rq_pages` entries.
- A reply slot at or past `rq_next_page` when the request ends is neither
  released nor refilled; `nfsd4_encode_operation()` and the NFSv3 readdir
  code keep `rq_next_page` in step with `xdr->page_ptr` for that reason.
- `net/sunrpc/svcsock.c` writes neither `rq_respages` nor `rq_next_page`;
  `svc_process()` sets `rq_next_page` to `&rq_respages[1]`.
- **Unsafe usage**: a receive path that sets an `rq_pages` entry to NULL and
  leaves it outside `rq_pages[0 .. rq_pages_nfree)`; `svc_alloc_arg()` does
  not refill it and the next receive uses a NULL page.
  - Safe: move the leading n entries out, NULL each, and set
    `rq_pages_nfree` to n, as `svc_tcp_save_pages()` and
    `svc_rdma_clear_rqst_pages()` do.
  - Safe: overwrite an entry with another page after releasing the old one,
    with no count, as `svc_tcp_restore_pages()` and `svc_rdma_read_complete()`
    do.
  - Safe: NULL `rq_respages` entries below `rq_next_page` in a send path, as
    `svc_rdma_save_io_pages()` does; the reply refill covers that range.
