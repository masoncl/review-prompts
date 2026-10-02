- Two arrays: `rq_pages` holds the call and `rq_respages` holds the reply.
- `svc_init_buffer()` in `net/sunrpc/svc.c` allocates each array separately
  with `rq_maxpages + 1` entries; `rq_respages` is not a pointer into
  `rq_pages`.
- `rq_next_page` and `rq_page_end` point into `rq_respages`.
- `svc_alloc_arg()` sets `rq_arg.pages` to `rq_pages + 1`; `svc_process()`
  sets `rq_res.pages` to `&rq_respages[1]`.

| Where | What it does to the reply pointers |
|---|---|
| `svc_init_buffer()` | `rq_next_page = rq_respages + rq_maxpages`, so the first refill covers all `rq_maxpages` slots |
| `svc_alloc_arg()` in `net/sunrpc/svc_xprt.c` | refills `rq_respages` up to the old `rq_next_page`, then sets `rq_next_page = rq_respages`, `rq_page_end = &rq_respages[rq_maxpages]`, and stores NULL at `rq_page_end[0]` |
| `svc_rdma_recvfrom()` | sets `rq_next_page = rq_respages` |
| `svc_process()` | sets `rq_next_page = &rq_respages[1]` |
| `svc_rqst_release_pages()` | releases and NULLs the slots from `rq_respages` up to `rq_next_page`; leaves `rq_next_page` unchanged |

- `net/sunrpc/svcsock.c` assigns neither `rq_respages` nor `rq_next_page`.
- `svc_alloc_arg()` does not scan the whole array for NULL slots: the value
  it finds in `rq_next_page` bounds its refill of `rq_respages`, and a NULL
  slot at or above it is not refilled.
- `rq_pages` refill: `svc_alloc_arg()` refills only the first
  `rq_pages_nfree` entries, which a transport sets when it takes call pages
  out of the array.
- `svc_rqst_replace_page()` bounds `rq_next_page` by `rq_respages` and
  `rq_page_end`, not by `rq_pages`.
