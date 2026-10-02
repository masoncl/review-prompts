- State: bits in `nn->flags`, an `unsigned long` in `struct nfsd_net`, named by
  `enum nfsd_net_flag` in `fs/nfsd/netns.h`.
- There are no fields grace_ended, grace_end_forced, in_grace,
  somebody_reclaimed, track_reclaim_completes or client_tracking_active, and no
  nfsd4_net_flags word.

| Bit | Meaning |
|---|---|
| `NFSD_NET_GRACE_ENDED` | end-of-grace work has been claimed; reads of `v4_end_grace` report it |
| `NFSD_NET_GRACE_END_FORCED` | an administrator asked for the end; first test in `clients_still_reclaiming()` |
| `NFSD_NET_SOMEBODY_RECLAIMED` | a reclaim succeeded in `nfsd4_open()` or `nfsd4_lock()` since the last `clients_still_reclaiming()` that reached it |
| `NFSD_NET_TRACK_RECLAIM_COMPLETES` | RECLAIM_COMPLETE counting is on; set only by `nfs4_cld_state_init()` |
| `NFSD_NET_IN_GRACE` | legacy recovery-directory tracker only, under `CONFIG_NFSD_LEGACY_CLIENT_TRACKING`; set in `nfsd4_init_recdir()`, cleared in `nfsd4_recdir_purge_old()`; read only by `nfsd4_create_clid_dir()` and `nfsd4_remove_clid_dir()` |

- `nfsd4_end_grace()` has three callers: `nfs4_laundromat()` on the
  workqueue, `inc_reclaim_complete()` in the nfsd thread handling
  RECLAIM_COMPLETE, and `nfs4_state_start_net()` on its `skip_grace` path;
  the laundromat can run concurrently with either of the others.
- `inc_reclaim_complete()`: calls `nfsd4_end_grace()` directly; it does not
  call `mod_delayed_work()`.
- `inc_reclaim_complete()`: counts a client only if
  `NFSD_NET_TRACK_RECLAIM_COMPLETES` is set and
  `nfsd4_find_reclaim_client()` finds its name.
- Trackers whose init does not call `nfs4_cld_state_init()`: neither the
  RECLAIM_COMPLETE early end nor the `skip_grace` path can happen.
- Once-only guarantee: `test_and_set_bit(NFSD_NET_GRACE_ENDED, &nn->flags)` at
  the top of `nfsd4_end_grace()`; no lock serialises the callers.
- "Once" is per server start: `nfs4_state_create_net()` clears
  `NFSD_NET_GRACE_ENDED` and `NFSD_NET_GRACE_END_FORCED`.
- **Potentially unsafe usage**: acting on a plain `test_bit()` of
  `NFSD_NET_GRACE_ENDED`.
  - Unsafe: when the code that follows does end-of-grace work; two callers can
    both see the bit clear and both run `->grace_done`, which in
    `nfsd4_cld_grace_done()` sends `Cld_GraceDone` and empties the reclaim
    table through `nfs4_release_reclaim()`.
  - Safe: when the test only decides whether to ask for the end, as in
    `nfsd4_force_end_grace()`; the work still goes through the
    `test_and_set_bit()` in `nfsd4_end_grace()`.
- `nfsd4_end_grace()`: does not call `nfsd4_client_tracking_exit()`; that is
  in `nfs4_state_shutdown_net()`.
- `nfsd4_record_grace_done()`: does nothing when `nn->client_tracking_ops` is
  `NULL`.
- First laundromat run: queued by `nfs4_state_start_net()` after
  `nn->nfsd4_grace` seconds, not `nn->nfsd4_lease`; only the `skip_grace`
  path queues it after `nn->nfsd4_lease`.
- `nfs4_laundromat()`: has no elapsed-time test; it calls `nfsd4_end_grace()`
  on every run where `clients_still_reclaiming()` is false, and later calls
  return at the `test_and_set_bit()`.
- `clients_still_reclaiming()` returns false at the first of these that holds,
  true otherwise:
  1. `NFSD_NET_GRACE_END_FORCED` is set.
  2. `NFSD_NET_TRACK_RECLAIM_COMPLETES` is set and `nn->nr_reclaim_complete`
     equals `nn->reclaim_str_hashtbl_size`.
  3. `NFSD_NET_SOMEBODY_RECLAIMED` was clear (the test clears it).
  4. `ktime_get_boottime_seconds()` is past `nn->boot_time_bt` plus twice
     `nn->nfsd4_lease`.
- `clients_still_reclaiming()`: does not look at `nn->client_lru` or
  `nn->boot_time`.
- While `clients_still_reclaiming()` is true: `nfs4_laundromat()` skips all its
  other work and reruns after `NFSD_LAUNDROMAT_MINTIMEOUT` seconds.
- Length of the delay: it lasts only while a reclaim succeeds between
  consecutive laundromat runs, and ends at the first run later than two
  leases after `nn->boot_time_bt`.
- Forced end: `write_v4_end_grace()` in `fs/nfsd/nfsctl.c` calls
  `nfsd4_force_end_grace()` in `fs/nfsd/nfs4state.c`, not
  `nfsd4_end_grace()`.
- `nfsd4_force_end_grace()`: sets `NFSD_NET_GRACE_END_FORCED` and calls
  `mod_delayed_work()` on `nn->laundromat_work` with delay 0; the work runs in
  the laundromat, and the write does not wait for it.
- `nfsd4_force_end_grace()`: takes no NFSD lock, `nn->client_lock` included.
- `nfsd4_force_end_grace()` returns `false` when `nn->client_tracking_ops` is
  `NULL` or `NFSD_NET_GRACE_ENDED` is already set; the write then fails with
  `-EBUSY`.
