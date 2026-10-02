- `nfsd_breaker_owns_lease()`: tests
  `fl->fl_lmops != &nfsd_lease_mng_ops` itself, before it dereferences
  `flc_owner`.
- Why it tests: `should_notify_deleg()` calls it directly for each lease on
  a directory, not through `fl_lmops`.
- NULL breaker: `nfsd_breaker_owns_lease()` has no test for a NULL
  `ntli_lease_breaker`; its only other test is `nfsd_v4client()` on
  `nfsd_current_rqst()`.
- `nfsd4_deleg_getattr_conflict()`: compares `dp->dl_recall.cb_clp` with
  `*(ntli->ntli_lease_breaker)`.
- Other clients: `nfsd_open_break_lease()` adds `O_NONBLOCK`; the
  `-EWOULDBLOCK` becomes `nfserr_jukebox` through `nfserrno()`.
- Directory events: `should_notify_deleg()` uses the same test, so a client
  gets no CB_NOTIFY for its own change.
