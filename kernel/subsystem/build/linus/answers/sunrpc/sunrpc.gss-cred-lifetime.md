- `gss_get_ctx()`: plain `refcount_inc()`, not an inc-not-zero; it cannot
  fail and cannot detect a dying context.
- **Unsafe usage**: calling `gss_cred_get_ctx()` on a cred the caller holds
  no reference to.
  - Unsafe: the cred's own context reference may already be gone, and
    `refcount_inc()` on a zero count does not refuse.
  - Safe: with a counted cred, as `gss_marshal()` has in `rq_cred`;
    `gss_destroy_nullcred()` drops the cred's context reference only after
    `cr_count` reached zero.
  - Safe: reading `gc_ctx` fields inside `rcu_read_lock()` without taking a
    reference, as `gss_match()`, `gss_key_timeout()` and
    `gss_stringify_acceptor()` do; `gss_free_ctx()` frees through
    `call_rcu()`.
- `gc_ctx`: installed at most once, because `gss_cred_set_ctx()` returns
  early unless `RPCAUTH_CRED_NEW` is set; it is never swapped, and
  `gss_update_rslack()` does not touch it.
- Clearing `gc_ctx`: done in `gss_destroy_nullcred()` with
  `RCU_INIT_POINTER()`, followed by `gss_put_ctx()`; `gss_destroy_cred()`
  only adds `gss_send_destroy_context()` in front, when
  `RPCAUTH_CRED_UPTODATE` was set.
- `gss_nullops`: its `crdestroy` is `gss_destroy_nullcred()`, so the
  duplicate cred from `gss_dup_cred()` sends no second destroy call.
- `gss_delete_sec_context()`: runs inside the RCU callback, in
  `gss_do_free_ctx()`, not before `call_rcu()`.
- `gss_free_callback()`: the `kref` release of `struct gss_auth`; the cred is
  freed by `gss_free_cred_callback()`.
- `rpcauth_lookup_credcache()`: only the first walk is under
  `rcu_read_lock()`; after a miss it creates a cred and walks the chain again
  under the cache's `lock` before inserting.
- Lookup flags: `RPCAUTH_LOOKUP_NEW` and `RPCAUTH_LOOKUP_ASYNC` only; there
  is no RPCAUTH_LOOKUP_RCU.
