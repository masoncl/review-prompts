| Job | File | Easy to look in the wrong place |
|---|---|---|
| `struct net_device_ops` | `include/linux/netdevice.h` | |
| `struct ethtool_ops` | `include/linux/ethtool.h` | |
| NAPI | `include/linux/netdevice.h`, `net/core/dev.c` | `struct napi_config` code is in `net/core/dev.c`, not `net/core/netdev_config.c` |
| Per-queue statistics callbacks (`struct netdev_stat_ops`) | `include/net/netdev_queues.h`; core in `net/core/netdev-genl.c` | |
| Queue management callbacks (`struct netdev_queue_mgmt_ops`) | `include/net/netdev_queues.h`; core in `net/core/netdev_rx_queue.c`, `net/core/netdev_queues.c`, `net/core/netdev_config.c` | `net/core/netdev_config.c` holds `netdev_queue_config()`, the per-queue configuration |
| Per-device lock helpers | `include/net/netdev_lock.h`: `netdev_lock_ops()`, `netdev_need_ops_lock()`, `netdev_trylock()`, the assert helpers | `include/linux/netdevice.h` defines only `netdev_lock()` and `netdev_unlock()`, and does not include `include/net/netdev_lock.h` |
| Lockless transmit queue stop and wake macros | `include/net/netdev_queues.h` | |
| Page pool | `include/net/page_pool/types.h`, `include/net/page_pool/helpers.h`, `net/core/page_pool.c` | |
| XDP driver helpers | `include/net/xdp.h`, `net/core/xdp.c` | `bpf_prog_run_xdp()` is in `include/net/xdp.h`; `xdp_do_redirect()` and `xdp_do_flush()` are declared in `include/linux/filter.h` and defined in `net/core/filter.c` |
| 64-bit statistics helpers | `include/linux/u64_stats_sync.h` | |
| Core's deferred work for drivers | `net/core/netdev_work.c`: `netdev_work_sched()`, `netdev_work_cancel()`; callback is `ndo_work` in `struct net_device_ops`, called under `rtnl_lock()` and `netdev_lock_ops()` | not `net/core/link_watch.c`, not `netdev_run_todo()`; declarations are in `include/linux/netdevice.h`, core-only events (`enum netdev_work_core`) in `net/core/dev.h` |
| Software driver used for testing | `drivers/net/netdevsim/` | |
