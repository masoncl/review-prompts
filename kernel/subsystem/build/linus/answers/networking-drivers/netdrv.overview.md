- "Ops-locked" device: one for which `netdev_need_ops_lock()` in
  `include/net/netdev_lock.h` is true: the driver set `request_ops_lock`, or
  set `queue_mgmt_ops`, or (with `CONFIG_NET_SHAPER`) has
  `netdev_ops->net_shaper_ops`.
- `lock` in `struct net_device` (the instance lock): a plain mutex, taken
  after `rtnl_lock()`; on an ops-locked device `ndo_open` and `ndo_stop` run
  with both held (see `__dev_open()` in `net/core/dev.c`).
- `struct netdev_queue_mgmt_ops`: called with the instance lock;
  `rtnl_lock()` need not be held.
- `struct net_shaper_ops`: `set`, `delete` and `group` are called with the
  instance lock, and `rtnl_lock()` need not be held; `capabilities` is also
  called with no lock, from `net_shaper_nl_cap_get_doit()`.
- `struct netdev_stat_ops`: called under the instance lock on an ops-locked
  device, under `rtnl_lock()` otherwise.
- `struct napi_struct` and the instance lock: `netif_napi_add()`,
  `netif_napi_del()`, `napi_enable()`, `napi_disable()` and
  `netif_napi_set_irq()` take `netdev_lock()` themselves on every device, not
  only ops-locked ones; the `_locked` variants expect it held instead, and
  `napi_enable_locked()` has no assertion.
- **Unsafe usage**: calling a NAPI helper that takes `netdev_lock()` from a
  callback that already runs under the instance lock.
  - Safe: use the `_locked` variant, for example `napi_disable_locked()` as
    `bnxt_disable_napi()` does; `netdev_assert_locked()` in it defines the
    requirement.
- `struct napi_config`: per-index NAPI settings that outlive the
  `struct napi_struct`; the array is `dev->napi_config`, sized
  max(txqs, rxqs) in `alloc_netdev_mqs()`, attached by
  `netif_napi_add_config()`.
- With `n->config` set, `napi_disable()` saves the settings into
  `struct napi_config` and `napi_enable()` restores from it; the NAPI id is
  stored there by the first `napi_enable()` and reused by later ones, so the
  id survives a ring rebuild.
- Queue to NAPI link: explicit, set by `netif_queue_set_napi()` into
  `struct netdev_queue` and `struct netdev_rx_queue`; the core does not infer
  it.
- `xdp_rxq` embedded in `struct netdev_rx_queue`: the core's own, registered
  in `netif_alloc_rx_queues()` and used by generic XDP
  (`bpf_prog_run_generic_xdp()`); a driver's native XDP path registers a
  separate `struct xdp_rxq_info` in its ring.
- `struct netdev_rx_queue` also records what has claimed the queue: `pool`
  (AF_XDP, under `CONFIG_XDP_SOCKETS`), `mp_params` (memory provider),
  `lease`; `netdev_queue_busy()` in `net/core/netdev_queues.c` is the test the
  core runs before it shrinks channels or leases a queue.
- Queue lease: a virtual device (no `dev->dev.parent`) creates an RX queue
  with `ndo_queue_create` and pairs it with a physical device's RX queue;
  `lease` points each queue at the other. See `netdev_nl_queue_create_doit()`
  in `net/core/netdev-genl.c`; `drivers/net/netkit.c` is the implementor.
- Memory provider on a leased queue: `netif_mp_open_rxq()` installs it on the
  physical queue, so a physical driver's `ndo_queue_mem_alloc` and
  `ndo_queue_start` can run on behalf of another netdev.
- `netmem_ref`: what a `struct page_pool` hands out; it is a `struct page` or
  a `struct net_iov` (memory with no kernel mapping), told apart by
  `netmem_is_net_iov()`.
- `struct page_pool` with `PP_FLAG_ALLOW_UNREADABLE_NETMEM`: takes its memory
  provider from the `struct netdev_rx_queue` at `slow.queue_idx` in
  `page_pool_init()`, which asserts the instance lock.
- Page pools per RX queue: can be more than one; for example
  `bnxt_alloc_rx_page_pool()` creates a separate `head_pool` for headers when
  `bnxt_separate_head_pool()` is true, such as when `page_pool` is
  unreadable; otherwise `head_pool` is the same pool.
- `struct page_pool` lifetime: can outlive the ring, the NAPI and the netdev;
  `page_pool_destroy()` defers the free while pages are in flight, and
  `page_pool_unreg_netdev()` moves the pool to the loopback device on
  `NETDEV_UNREGISTER`.
- `struct xdp_buff`: not always on the poll function's stack; for example
  `struct i40e_ring` embeds one to carry a partly built multi-buffer packet
  into the next poll.
- `struct devlink`: exists only where one is allocated, for example with
  `devlink_alloc()` or `devlink_alloc_ns()`; the netdev side of the link is
  `dev->devlink_port`, set with `SET_NETDEV_DEVLINK_PORT()` before
  registration.
- NAPI with no interface behind it: still needs a `struct net_device`; such
  drivers allocate one with `alloc_netdev_dummy()` (`NETREG_DUMMY`), which is
  never registered.
