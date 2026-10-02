| Job | File in this tree |
|---|---|
| Software segmentation | `net/core/gso.c` holds `__skb_gso_segment()` and `skb_mac_gso_segment()`; `skb_segment()` and `skb_segment_list()` are in `net/core/skbuff.c` |
| Helpers that take the device instance lock | `netdev_lock()` and `netdev_unlock()`: `include/linux/netdevice.h`. Conditional and assert forms such as `netdev_lock_ops()`: `include/net/netdev_lock.h`. `dev_` wrappers around `netif_` functions: `net/core/dev_api.c`. There is no net/core/netdev_lock.c |
| What the `net/core/dev_api.c` wrappers lock | Each wrapper around a `netif_` function except `dev_set_threaded()` calls `netdev_lock_ops()`, which takes the lock only when `netdev_need_ops_lock()` is true; `dev_set_threaded()` calls `netdev_lock()` unconditionally |
| Socket system calls | `net/socket.c`; the compat entry points are in `net/compat.c` |
| Datagram helpers | `net/core/datagram.c`; there is no include/net/datagram.h, the prototypes are in `include/linux/skbuff.h`, except `__sk_queue_drop_skb()` in `include/net/sock.h` |
| Drop reason strings | `drop_reasons[]` in `net/core/skbuff.c`, expanded by the preprocessor from `DEFINE_DROP_REASON()` in `include/net/dropreason-core.h`; no file is generated at build time |
| Qdisc drop reasons | separate `enum qdisc_drop_reason` in `include/net/dropreason-qdisc.h`, not part of `enum skb_drop_reason` |
