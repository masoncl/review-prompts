- First call, `nfsd_set_fh_dentry()`, in order:
  1. `fh_size == 0` gives `nfserr_nofilehandle`; bad version, auth type,
     fsid type or length gives `nfserr_badhandle`.
  2. `rqst_exp_find()`: `-ENOENT` gives `nfserr_stale`, other errors go
     through `nfserrno()`.
  3. Credentials: with `NFSEXP_NOSUBTREECHECK` it only raises the nfsd
     capabilities on a copy of the current credentials; otherwise it calls
     `nfsd_setuser_and_check_port()`.
  4. `FILEID_ROOT` takes the export root; otherwise the MAC check (see
     "Signed file handles") and then `exportfs_decode_fh_raw()`.
  5. An NFSv2 or NFSv3 handle on an `NFSEXP_V4ROOT` export:
     `nfserr_badhandle`.
- Every call then runs, in `__fh_verify()`: `check_pseudo_root()`,
  `nfsd_setuser_and_check_port()`, `nfsd_mode_check()`,
  `check_xprtsec_policy()`, `check_security_flavor()`, `nfsd_permission()`.
- Later calls skip only `nfsd_set_fh_dentry()`.
- `__fh_verify()` does not call `check_nfsd_access()`; it calls the two
  helpers so that each can be skipped separately.
- `nfsd_mode_check()` on a mismatch, first match wins:

| Object | Requested | Status |
|---|---|---|
| symlink | `S_IFDIR` | `nfserr_symlink_not_dir` |
| symlink | other | `nfserr_symlink` |
| any other | `S_IFDIR` | `nfserr_notdir` |
| directory | other | `nfserr_isdir` |
| any other | other | `nfserr_wrong_type` |

- `nfsd_mode_check()` with a matching `S_IFDIR`: still `nfserr_notdir` when
  `d_can_lookup()` fails.
- `nfserr_inval` is not returned by `nfsd_mode_check()`; it is what
  `nfsd3_map_status()` makes of `nfserr_wrong_type` and `nfserr_symlink`.
- The type argument is `umode_t`; no negative value is handled, whatever the
  comment above `fh_verify()` says.
- `NFSD_MAY_NLM`: always skips `check_xprtsec_policy()`; the flavor check
  still runs.
- `NFSD_MAY_NLM` on an export with `NFSEXP_NOAUTHNLM`: also skips
  `check_security_flavor()` and `nfsd_permission()`.
- `fh_verify_local()` (`rqstp` is NULL): skips the port check, both security
  checks and `svc_xprt_set_valid()`; `nfsd_setuser()`, the type check and
  `nfsd_permission()` still run.
