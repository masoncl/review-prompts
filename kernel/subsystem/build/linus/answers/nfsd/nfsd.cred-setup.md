- `nfsd_setuser()` installs the credentials itself with `override_creds()`;
  callers do nothing more.
- `nfsd_setuser()` has one caller, `nfsd_setuser_and_check_port()`; it runs
  on every `__fh_verify()` that gets past `check_pseudo_root()` and the port
  check, and once more inside `nfsd_set_fh_dentry()` for an export without
  `NFSEXP_NOSUBTREECHECK`.
- Squash flags come from `nfsexp_flags()`: the flags of the `ex_flavors`
  entry that matches `cr_flavor`, else `ex_flags`.
- `NFSEXP_ROOTSQUASH`: supplementary groups are kept; only entries equal to
  `GLOBAL_ROOT_GID` are replaced by `ex_anon_gid`.
- `NFSEXP_ALLSQUASH`: the only case that replaces the request's group list
  with an empty one.
- Capabilities: `CAP_NFSD_SET` in `include/linux/capability.h` is dropped
  from `cap_effective` for a non-root fsuid, and raised, limited by
  `cap_permitted`, for root.
- Before the first `fh_verify()` of a request: nothing at dispatch sets or
  clears credentials, so the thread carries the override left by an earlier
  request, or its own if there was none.
- `nfsd_set_fh_dentry()` with `NFSEXP_NOSUBTREECHECK`: decodes with the
  credentials the thread carries at that point plus raised nfsd
  capabilities.
