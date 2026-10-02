- `svc_rqst_replace_page()` checks one thing: that `rq_next_page` lies from
  `rq_respages` to `rq_page_end`, both ends included; it does not look at
  `rq_pages` or at `page`.
- At `rq_page_end` the call succeeds and writes the sentinel entry that
  `svc_init_buffer()` allocates; one slot further it returns `false`.
- Returns `bool`; on `false` nothing is stored and `rq_next_page` does not
  move.
- Displaced page: goes through `svc_rqst_page_release()` into `rq_fbatch`
  (`struct svc_rqst` has no rq_batch field), freed when the batch fills or in
  `svc_rqst_release_pages()`; it is not passed to `put_page()` directly.
- New page: the function takes its own reference with `get_page()`; the
  caller keeps the one it has.
- `svc_rqst_replace_page()` has no position argument and touches no `rq_res`
  field: the caller keeps `rq_next_page` at the reply's next data slot and
  maintains `rq_res.page_base` and `rq_res.page_len`.
- `nfsd_splice_actor()` in `fs/nfsd/vfs.c` is the only caller.
- **Unsafe usage**: counting a page's bytes into `rq_res.page_len` after
  `svc_rqst_replace_page()` returned `false`; the reply then covers a page
  it does not hold.
  - Safe: fail the read first, as `nfsd_splice_actor()` returns `-EIO`
    before it adds `sd->len`.
- **Potentially unsafe usage**: installing the page that already sits in
  `*(rq_next_page - 1)`.
  - Unsafe: when the reply data so far ends inside that page, so
    `rq_res.page_base + rq_res.page_len` is not page aligned; the page would
    be listed twice for one contiguous range.
  - Safe: when the data so far ends on a page boundary; the same page can
    legitimately repeat, and `nfsd_splice_actor()` skips the call only in the
    unaligned case.
- **Unsafe usage**: splicing pages into a reply whose `rq_res.page_len` is
  already nonzero from XDR encoding; `nfsd_splice_actor()` sets
  `rq_res.page_base` only when `rq_res.page_len` is 0.
  - Safe: refuse first, as `nfsd4_encode_splice_read()` returns
    `nfserr_serverfault` when `xdr->buf->page_len` is nonzero.
  - Safe: with no test in `nfsd_read()`, reached only from the NFSv2 and
    NFSv3 READ procedures; `svc_process()` set `rq_res.page_len` to 0 and
    nothing is encoded into pages before the procedure runs.
