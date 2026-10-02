- `fh_copy()` in `fs/nfsd/nfsfh.h`: plain structure assignment; takes no
  reference and does not put the destination.
- `fh_copy()`: its `WARN_ON()` tests `src->fh_dentry`, not the destination.
- `fh_dup2()`: `static inline` in `fs/nfsd/nfs4proc.c`; code in other files
  cannot call it.
- `fh_dup2()` with a source whose `fh_dentry` is NULL: allowed; `dget(NULL)`
  does nothing and `exp_get()` is guarded.
- `fh_dup2()` copies the whole structure after taking the references,
  including `fh_want_write`, `fh_pre_saved`, `fh_post_saved` and `fh_flags`.
- Saved pre/post attributes on the source are harmless for `current_fh`:
  `nfsd4_proc_compound()` calls `fh_clear_pre_post_attrs()` before each
  handler it runs.
- **Unsafe usage**: `fh_copy()` from a source whose `fh_dentry` is set; both
  structures then share one dentry and one export reference, and two
  `fh_put()` calls drop them twice.
  - Safe: copy the decoded handle first, then `fh_verify()` the destination,
    as `nfsd3_proc_getattr()` does.
- **Unsafe usage**: `fh_copy()` into a destination that holds references;
  they leak.
  - Safe: a destination in `rq_resp`, which `svc_generic_init_request()`
    zeroes before the procedure runs, as in `nfsd3_proc_getattr()`.
- **Unsafe usage**: `fh_dup2()` from a source with `fh_want_write` set; both
  handles then call `mnt_drop_write()` in `fh_drop_write()`.
  - Safe: `nfsd4_create()`; `nfsd_create()` takes write access on
    `current_fh`, the destination, which `fh_put()` inside `fh_dup2()`
    drops, and `resfh`, from `fh_init()` and `fh_compose()`, has
    `fh_want_write` clear.
