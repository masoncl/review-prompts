- After a failed `fh_verify()`: `fh_dentry` and `fh_export` may be set, from
  an earlier call or because a check after the lookup failed; test the
  status, not the pointers.
- `fh_compose()` makes no permission, flavor or credential check; a later
  `fh_verify()` on the handle skips only the lookup.
- `nfsd_lookup()` across a mount: runs `check_nfsd_access()` on the new
  export but not `nfsd_setuser()`; credentials stay those of the parent's
  export until the next `fh_verify()`.
- `fh_compose()` failure: returns `nfserr_stale` after its own `fh_put()`, so
  the handle holds no references.
- `nfsd_lookup()` on a negative dentry: composes the result handle, then
  returns `nfserr_noent`; the handle still needs `fh_put()`.
- `fh_verify()` on an empty handle (`fh_size` 0, no dentry): returns
  `nfserr_nofilehandle`; a handler that reaches the handle only through
  `fh_verify()` needs no test of its own.
- `nfsd4_proc_compound()` gates only `current_fh`; `save_fh` may be empty for
  any operation.
- There is no `fh_verify()` in `nfs4_check_fh()`; it only compares
  `fh_handle` with the stateid's `fi_fhandle`.
- **Potentially unsafe usage**: reading `fh_dentry` or `fh_export` of
  `save_fh`.
  - Unsafe: with no test and no `fh_verify()`; no SAVEFH may have run, or it
    saved a foreign handle.
  - Safe: after testing `save_fh.fh_dentry`, as `nfsd4_restorefh()` and
    `nfsd4_verify_copy()` do.
  - Safe: through `fh_verify()`, as `nfsd4_rename()` does by passing it to
    `nfsd_rename()`.
  - Safe: reading only `fh_handle`, as `nfsd4_setup_inter_ssc()` does.
