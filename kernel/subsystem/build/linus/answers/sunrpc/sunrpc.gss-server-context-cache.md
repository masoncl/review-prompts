- Lookup reference: dropped at `out:` in `svcauth_gss_accept()` on every path
  that found a context, `SVC_OK` included; it never outlives the function.
- Second reference: `cache_get()` stored in the `rsci` field of
  `struct gss_svc_data`, taken only on the successful `RPC_GSS_PROC_DATA`
  path; `svcauth_gss_release()` drops it after wrapping.
- `rq_cred`: a plain struct assignment from `rsci->cred`; only
  `cr_group_info` gets its own reference (`get_group_info()`).
- `cr_principal`, `cr_raw_principal`, `cr_targ_princ`, `cr_gss_mech` in
  `rq_cred`: borrowed from the `struct rsc`; nothing is `kstrdup()`ed and
  `gss_mech_get()` is not called; the reference in `gsd->rsci` keeps them
  alive until `svcauth_gss_release()`.
- `svcauth_gss_release()`: for the cred it only does `put_group_info()` and
  clears `cr_group_info`; no caller in this tree passes `rq_cred` to
  `free_svc_cred()`.
- `free_svc_cred()`: besides the three strings and the group info it does
  `gss_mech_put()` on `cr_gss_mech`, then `init_svc_cred()`.
- `rsc_put()`: on the last `cache_put()` it calls `gss_delete_sec_context()`
  and `free_svc_cred()` at once; only `rsc_free_rcu()`, which frees the handle
  and the `struct rsc`, waits for `call_rcu()`.
- `rsc_free()`: used only on on-stack temporaries, in `rsc_parse()`,
  `gss_proxy_save_rsc()` and `gss_svc_searchbyctx()`; it is not the cache's
  release function.
- **Unsafe usage**: calling `free_svc_cred()` on `rqstp->rq_cred`.
  - Unsafe: it frees strings and puts a mech reference that the `struct rsc`
    still owns; `rsc_put()` then frees them again.
  - Safe: `svcauth_gss_release()` puts only `cr_group_info`, the one
    reference `svcauth_gss_accept()` took.
  - Safe: `free_svc_cred()` on a cred filled by `copy_cred()` in
    `fs/nfsd/nfs4state.c`, which duplicates each string and takes
    `gss_mech_get()`.
- **Potentially unsafe usage**: reading string or mech pointers from
  `rq_cred`.
  - Unsafe: after `svcauth_gss_release()` has dropped `gsd->rsci`, for example
    from an object that outlives the request; `rsc_put()` may already have
    freed them.
  - Safe: before `svc_authorise()` runs, in `pg_authenticate` or the
    procedure, as `check_gss_callback_principal()` in `fs/nfs/callback.c`
    does; `svcauth_gss_accept()` holds the `cache_get()` reference in
    `gsd->rsci` until then. `svc_process_common()` calls `svc_authorise()`
    before the reply is sent.
  - Safe: after a deep copy with `copy_cred()`.
