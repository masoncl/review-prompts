- Decode failure: `nfsd_dispatch()` writes `rpc_garbage_args` through
  `rq_accept_statp` and returns 1; it does not write `rq_auth_stat`.
- Cache type: `ntli->ntli_cachetype`, set from `pc_cachetype` before
  `pc_decode`; `nfsd_cache_lookup()` reads it from `rq_private` itself, so a
  value the decoder stored is the one the lookup uses.
- Encode failure and `RQ_DROPME`: both call
  `nfsd_cache_update(rqstp, rp, RC_NOCACHE, NULL)`; the NULL status pointer
  makes `nfsd_cache_update()` free the entry.
- `rp` stays NULL after `RC_DOIT` unless `nfsd_cache_lookup()` inserted a new
  entry, for example when the type is `RC_NOCACHE` or the entry allocation
  failed; `nfsd_cache_update()` then returns at once.
- Return 1 with an accept status other than `rpc_success`:
  `svc_process_common()` truncates away everything encoded after
  authentication and sends the reply.
- `nfsd_status_counter_set_idle()`: called on every return path after the
  store that makes `rq_status_counter` odd, including both drop paths; the
  decode-failure path returns before that store.
