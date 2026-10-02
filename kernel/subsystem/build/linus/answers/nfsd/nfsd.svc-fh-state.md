- `fh_no_wcc`, `fh_no_atomic_attr`, `fh_use_wgather`, `fh_64bit_cookies`: set
  in `nfsd_set_fh_dentry()`, by a switch on `fh_maxsize`; the last three are
  set nowhere else, so only on the first `fh_verify()` of a wire handle.
- `fh_compose()`: of those four it sets only `fh_no_wcc`, copied from `ref_fh`
  or false; the others keep what the structure held before.
- `fh_put()` does not reset `fh_handle`, `fh_maxsize`, `fh_flags`,
  `fh_no_atomic_attr`, `fh_use_wgather` or `fh_64bit_cookies`.
- `fh_put()` calls `fh_clear_pre_post_attrs()` only when `fh_dentry` was set.
- NFSv2/v3 `pc_release` callbacks put only the handles in `rq_resp`; there is
  no nfsd_release_fhandle here.
- Handlers that verify the argument handle in place put it themselves before
  returning, for example `nfsd3_proc_fsstat()`, `nfsd3_proc_fsinfo()`,
  `nfsd3_proc_pathconf()` and `nfsd_proc_statfs()`.
- FSSTAT, FSINFO and PATHCONF in `nfsd_procedures3` have no `pc_release`; a
  handle left referenced by their handler is never put.
- `nfsd4_proc_compound()`: calls `fh_put()` on `current_fh` and `save_fh`
  directly after the operation loop, not through
  `nfsd4_cstate_clear_replay()`.
- `nfsd4_release_compoundargs()`, the COMPOUND `pc_release`: frees decode
  buffers only, puts no handle.
