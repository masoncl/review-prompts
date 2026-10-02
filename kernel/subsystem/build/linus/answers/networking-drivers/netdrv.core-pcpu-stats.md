- Allocation: `netdev_do_alloc_pcpu_stats()` runs in `register_netdevice()`
  after `ndo_init` has returned, so `ndo_init` sees no per-CPU area.
- Free: `netdev_do_free_pcpu_stats()` runs in `netdev_run_todo()` before
  `priv_destructor` and `free_netdev()`.
- Free on a `register_netdevice()` failure after the allocation and before
  the `NETDEV_REGISTER` notifier: runs before `ndo_uninit` and
  `priv_destructor`; the pointer is not cleared.
- `ndo_get_peer_dev` set with any type other than `NETDEV_PCPU_STAT_TSTATS`:
  `register_netdevice()` fails with `-EOPNOTSUPP`.
- `NETDEV_PCPU_STAT_LSTATS`: allocated and freed by the core but never read by
  `dev_get_stats()`; without a driver callback only `dev->stats` is
  reported. `dev_lstats_read()` in `drivers/net/loopback.c` reads it.
- `NETDEV_PCPU_STAT_TSTATS` and `NETDEV_PCPU_STAT_DSTATS` without driver
  callbacks: the result is `dev->stats` plus the per-CPU sums, not the
  per-CPU sums alone.
- Driver with `ndo_get_stats64` or `ndo_get_stats`: the core reads neither
  the per-CPU area nor (for `ndo_get_stats64`) `dev->stats`; the callback
  folds them in itself. `dev_get_tstats64()` is exported for use as that
  callback.
- `ndo_get_stats64`: the storage is zeroed by `dev_get_stats()` before the
  call.
- `dev->core_stats`: per-CPU, not atomic; added after the chosen source on
  every path.
