- `nfserr_stale`, from `nfsd_set_fh_dentry()`, also when the key is not set.
- `trace_nfsd_set_fh_dentry_badmac()` records it; `__fh_verify()` counts it
  with `nfsd_stats_fh_stale_inc()`.
- `nfsd4_putfh()` with `no_verify` set (`CONFIG_NFSD_V4_2_INTER_SSC`): turns
  any `nfserr_stale`, a bad signature included, into success with
  `NFSD4_FH_FOREIGN`.
