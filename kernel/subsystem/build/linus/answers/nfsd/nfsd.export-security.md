- Both transport security and flavor are checked on both paths.
- `__fh_verify()`: calls `check_xprtsec_policy()` then
  `check_security_flavor()` on every call that has an `rqstp`, except where
  `NFSD_MAY_NLM` skips them (see "File handle verification steps").
- `check_nfsd_access()` has exactly three callers, all passing
  `may_bypass_gss` false: `nfsd_lookup()`, `nfsd4_encode_entry4_fattr()` and
  `nfsd4_proc_compound()`.
- `nfsd_cross_mnt()`, `nfsd4_lookup()` and `nfsd4_do_lookupp()` do not call it
  themselves; there is no nfsd4_encode_dirent here.
- `nfsd4_proc_compound()` calls it only after a successful operation flagged
  `OP_IS_PUTFH_LIKE`, when another operation follows and that one lacks
  `OP_HANDLES_WRONGSEC`; see `need_wrongsec_check()`.
- `compose_entry_fh()` (NFSv3 READDIRPLUS) needs no check: it returns no
  handle for a `d_mountpoint()` entry.
- `check_xprtsec_policy()` failure: `nfserr_wrongsec`, the same as the flavor
  check.
- Transport policy: `may_bypass_gss` and `nfsd4_spo_must_allow()` do not
  relax it; only `NFSD_MAY_NLM` and a NULL `rqstp` skip it.
- Flavor check: passes early for `exp->ex_client == rqstp->rq_gssclient` and
  for `nfsd4_spo_must_allow()`; the bypass flags are in "NFSD_MAY access
  flags".
