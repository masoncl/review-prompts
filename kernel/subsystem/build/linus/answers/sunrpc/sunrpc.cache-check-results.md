- No request (`rqstp` NULL): `cache_check_rcu()` calls no `cache_upcall`, not
  even for early refresh, defers nothing, and turns `-EAGAIN` into `-ENOENT`.
- No request: the only results are 0 and `-ENOENT`; `-EAGAIN` and
  `-ETIMEDOUT` cannot occur. `gss_svc_searchbyctx()` passes NULL.
- `cache_check_rcu()`: never puts the caller's reference, on any return, so
  a caller that holds a reference still has to put it.
- 0 means `CACHE_VALID` set and `CACHE_NEGATIVE` clear; neither function
  calls `cache_is_expired()`. Lookup filters expired entries
  (`sunrpc_cache_find_rcu()`); a holder of a saved pointer tests expiry
  itself, as `ip_map_cached_get()` and `c_show()` do.
- Entry filled during the in-thread wait: `cache_defer_req()` returns false,
  `cache_is_valid()` runs again, and the result is 0 or `-ENOENT`, not
  `-ETIMEDOUT`.
- `cache_upcall` returning `-EAGAIN`: `cache_fresh_unlocked()` clears
  `CACHE_PENDING`; a not-yet-valid entry then ends as `-ETIMEDOUT`.
- `ip_map_cached_get()` does not call `cache_check()`; its caller
  `svcauth_unix_set_client()` does, and touches the entry only in `case 0`.
- **Unsafe usage**: calling `cache_check_rcu()` with a request inside
  `rcu_read_lock()`.
  - Unsafe: `cache_do_upcall()` allocates with `GFP_KERNEL` and
    `cache_wait_req()` sleeps for up to `req->thread_wait`.
  - Safe: pass NULL, as `c_show()` in `net/sunrpc/cache.c` and `e_show()` in
    `fs/nfsd/export.c` do between `cache_seq_start_rcu()` and
    `cache_seq_stop_rcu()`.
- **Unsafe usage**: calling `cache_check()` on an entry the caller holds no
  reference on.
  - Unsafe: `cache_check()` calls `cache_put()` on every non-zero return.
  - Safe: take the entry from `sunrpc_cache_lookup_rcu()`, which returns it
    with a reference, as `unix_gid_find()` does through `unix_gid_lookup()`.
  - Safe: with no reference, call `cache_check_rcu()` with NULL inside
    `rcu_read_lock()` instead, as `c_show()` does.
