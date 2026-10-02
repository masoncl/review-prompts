- `svc_defer()` refuses a request on two tests only: `rq_arg.page_len`
  non-zero, or `RQ_USEDEFERRAL` clear in `rq_flags`. There is no
  rq_usedeferral field, and no test for backchannel or transport type.
- `RQ_USEDEFERRAL`: `svc_process_common()` sets it for every request.
  NFSv4 clears it in `nfs4svc_decode_compoundargs()` and
  `nfsd4_proc_compound()`, both after `svc_authenticate()` and
  `pg_authenticate`, so cache lookups during authentication can still defer
  an NFSv4 request.
- The defer hook has a caller outside the cache: `nlmsvc_defer_lock_rqst()`
  in `fs/lockd/svclock.c` calls `rq_chandle.defer`; `retry_deferred_block()`
  later calls `revisit`.
- `svc_revisit()`: sets `XPT_DEFERRED` under `xpt_lock` before it tests
  `too_many` and `XPT_DEAD`, so the bit can be set with nothing queued;
  `svc_deferred_dequeue()` clears it on finding the list empty.
- `free_deferred()`: calls `xpo_release_ctxt` on `dr->xprt_ctxt` before
  `kfree()`; a bare `kfree()` of a deferred request leaks the context (for
  UDP, the skb).
- `xpo_release_ctxt`: is called with a NULL context, by `svc_xprt_release()`
  for a request that has none and by `free_deferred()` after
  `svc_deferred_recv()` took the context back; every implementation must
  accept NULL.
- Service shutdown: `svc_destroy()` calls `cache_clean_deferred()`, which
  calls `svc_revisit()` with `too_many` set, so requests still waiting in
  the cache are freed there.
