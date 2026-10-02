# Networking Drivers

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

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

## Locks and callback context

**Per-device lock**

- `up`, `moving_ns`, `nd_net`, `xdp_features`: "double protected", not protected
  by `lock` alone; writers hold `rtnl_lock` and `lock`, readers hold either.
  `netif_set_up()` in `net/core/dev.h` takes `netdev_lock()` itself when the
  device is not ops-locked.
- Field classes: the comment on `lock` in `include/linux/netdevice.h` names
  four (simply, double, ops, double ops protected); a patch that touches a
  listed field is checked against its class.
- "Ops protected" fields (`cfg`, `cfg_pending`, `ethtool`, `hwprov`): under the
  instance lock on ops-locked devices, under `rtnl_lock` on all others;
  `netdev_assert_locked_ops_compat()` is the matching assertion.
- Several instance locks at once: `netdev_lock_cmp_fn()` in
  `include/net/netdev_lock.h`, installed per lock class by
  `netdev_lockdep_set_classes()`, permits it for two locks of that class only
  while `rtnl_lock` is held, in any order; there is no upper-before-lower rule.
- Queue leasing nests two instance locks in a fixed order: the virtual
  device's lock before the physical device's; see
  `netdev_nl_queue_create_doit()`.
- `Documentation/networking/netdevices.rst` per-callback entries say "if the
  driver implements queue management or shaper API"; the code tests
  `netdev_need_ops_lock()`, so `request_ops_lock` drivers are covered too.
- Ethtool callbacks are the exception to "instance lock in addition to
  `rtnl_lock`"; see "Ethtool callback locking".

**Lock helper families**

- There is no netdev_ops_assert_locked() or
  netdev_ops_assert_locked_or_invisible() here;
  `netdev_assert_locked_ops_compat()` and
  `netdev_assert_locked_ops_compat_or_invisible()` do that job.

| Assertion | Ops-locked device | Other device |
|---|---|---|
| `netdev_assert_locked()` | instance lock | instance lock |
| `netdev_assert_locked_or_invisible()` | instance lock, while `NETREG_REGISTERED` or `NETREG_UNREGISTERING` | same |
| `netdev_assert_locked_ops()` | instance lock | nothing |
| `netdev_assert_locked_ops_compat()` | instance lock | `ASSERT_RTNL()` |
| `netdev_assert_locked_ops_compat_or_invisible()` | instance lock, while `NETREG_REGISTERED` or `NETREG_UNREGISTERING` | `ASSERT_RTNL()`, in the same two states |

- `netdev_assert_locked_or_invisible()`: never falls back to `rtnl_lock`.
- `netdev_is_locked_ops_compat()` and `netdev_ops_lock_dereference()`: the
  lockdep predicate and RCU dereference for "ops protected" pointers.
- `netdev_get_by_index_lock_ops_compat()` and
  `for_each_netdev_lock_ops_compat_scoped()` in `net/core/dev.h`: look up and
  take the compat lock (instance lock or `rtnl_lock`) in one step.
- `dev_set_threaded()`: takes `netdev_lock()` unconditionally, unlike wrappers
  such as `dev_open()` in `net/core/dev_api.c`, which take
  `netdev_lock_ops()`.
- `netif_open()` and `netif_close()`: need `rtnl_lock` as well as the ops lock;
  `__dev_open()` and `__dev_close_many()` contain `ASSERT_RTNL()`.
- `netif_set_real_num_tx_queues()` and `netif_set_real_num_rx_queues()`: the
  only assertion in either is `netdev_assert_locked_ops_compat()`; neither
  contains `ASSERT_RTNL()`.
- `netif_set_real_num_tx_queues()` on a registered device also needs
  `rtnl_lock`: it calls `dev_qdisc_change_real_num_tx()`, which uses
  `rtnl_dereference()`.
- The assertion in `netif_set_real_num_tx_queues()` and
  `netif_set_real_num_rx_queues()` depends on `reg_state`, not on the device
  being up: tx asserts for `NETREG_REGISTERED` and `NETREG_UNREGISTERING`, rx
  for `NETREG_REGISTERED` only.

**Callback contexts**

| Callback | Normal driver | Ops-locked driver | Sleep |
|---|---|---|---|
| `ndo_set_rx_mode` | `netif_addr_lock_bh()` of the caller; `rtnl_lock` not guaranteed | from core work: `rtnl_lock`, instance lock, then `netif_addr_lock_bh()` | no |
| `ndo_setup_tc`, `TC_SETUP_BLOCK` or `TC_SETUP_FT` | neither lock guaranteed | instance lock held on some paths, not on others | yes |
| `ndo_tx_timeout` | `tx_global_lock`, queues frozen, timer | same, no instance lock | no |

- `ndo_set_rx_mode` of a normal driver that also has `ndo_change_rx_flags`:
  runs from the core work under `rtnl_lock` and `netif_addr_lock_bh()`, with
  no instance lock; see `__dev_set_rx_mode()` in
  `net/core/dev_addr_lists.c`.
- `TC_SETUP_BLOCK` with the instance lock held: `tc_modify_qdisc()` takes
  `netdev_lock_ops()` and reaches `tcf_block_offload_cmd()` through
  `ingress_init()`.
- `TC_SETUP_BLOCK` without it: `nft_block_offload_cmd()` in
  `net/netfilter/nf_tables_offload.c` takes no netdev lock.
- `TC_SETUP_FT`: `nf_flow_table_offload_cmd()` takes
  `flowtable->flow_block_lock` and no netdev lock.
- An ops-locked driver's `TC_SETUP_BLOCK` handler therefore can neither assert
  the instance lock nor take it.

**Ethtool callback locking**

- Ops-locked driver, in `__dev_ethtool()` in `net/ethtool/ioctl.c` and in
  `ethnl_default_doit()`, `ethnl_default_dump_one()` and
  `ethnl_default_set_doit()` in `net/ethtool/netlink.c`: the core holds the
  instance lock and, by default, not `rtnl_lock`; see `need_rtnl` there.
- Other driver, in the same four functions: `rtnl_lock` only; `op_needs_rtnl`
  is ignored.
- `module_flash_fw_work()` in `net/ethtool/module.c`: calls
  `get_module_eeprom_by_page` and `set_module_eeprom_by_page` under
  `netdev_lock_ops()` without `rtnl_lock`, so with no lock at all on a driver
  that is not ops-locked.
- `op_needs_rtnl` in `struct ethtool_ops`: a mask of `ETHTOOL_OP_NEEDS_RTNL_*`
  bits from `include/linux/ethtool.h`; the core then takes `rtnl_lock` before
  the instance lock for the matching commands.
- Only commands with a case in `ethtool_nl_msg_needs_rtnl()` or
  `ethtool_ioctl_needs_rtnl()` in `net/ethtool/common.h` can opt in; a patch
  that needs another command adds a bit and a case in each of the two that
  has the command (`ETHTOOL_TEST` has an ioctl case only).
- Always under `rtnl_lock`, whatever the driver sets: the feature commands
  (`ethtool_cmd_changes_features()`, `ethnl_set_features()`) and
  `ETHTOOL_MSG_TSCONFIG_GET` / `ETHTOOL_MSG_TSCONFIG_SET`.
- A callback cannot assume `rtnl_lock` is absent either:
  `__ethtool_get_link_ksettings()` asserts `rtnl_lock`, takes
  `netdev_lock_ops()` and calls `get_link_ksettings`.
- `ethtool_op_get_link()` needs `rtnl_lock`; ops-locked drivers that use it set
  `ETHTOOL_OP_NEEDS_RTNL_GLINK`.
- **Potentially unsafe usage**: an ethtool callback that calls a core helper
  which needs `rtnl_lock`, such as `netdev_update_features()`,
  `netif_set_real_num_tx_queues()`, `netif_open()` or `netif_close()`.
  - Unsafe: on an ops-locked driver whose `op_needs_rtnl` lacks the bit for
    that command; `ASSERT_RTNL()` in `__netdev_update_features()`,
    `__dev_open()` or `__dev_close_many()` fires, or `rtnl_dereference()` in
    `dev_qdisc_change_real_num_tx()`.
  - Safe: the bit is set, as `nsim_set_channels()` with
    `ETHTOOL_OP_NEEDS_RTNL_SCHANNELS` in `drivers/net/netdevsim/ethtool.c`.
  - Safe: the driver is not ops-locked and the callback runs from the ioctl
    or a netlink request; `need_rtnl` is then always true.

**Address filter callback**

- `ndo_set_rx_mode_async` in `struct net_device_ops`: the sleeping variant;
  called from `netif_rx_mode_run()` in `net/core/dev_addr_lists.c` in process
  context, under `rtnl_lock` and `netdev_lock_ops()`, without
  `netif_addr_lock_bh()`.
- Its `uc` and `mc` arguments are snapshots of `dev->uc` and `dev->mc`.
- `__hw_addr_sync_dev()` may be run on the snapshots; the core copies the
  `sync_cnt` changes back with `__hw_addr_list_reconcile()`.
- Non-zero return: `netif_rx_mode_schedule_retry()` re-queues the update from a
  timer with doubling delay, at most `NETIF_RX_MODE_RETRY_MAX` times.
- Both callbacks set: only `ndo_set_rx_mode_async` is called.
- `__dev_set_rx_mode()` calls `ndo_set_rx_mode` inline only when the driver is
  not ops-locked and has neither `ndo_set_rx_mode_async` nor
  `ndo_change_rx_flags`; otherwise it only queues core work.
- Deferred `ndo_set_rx_mode`: `netif_rx_mode_run()` still takes
  `netif_addr_lock_bh()` around it, so it cannot sleep on any path.
- `rtnl_lock` around `ndo_set_rx_mode`: held when it runs from
  `netdev_work_proc()`; not guaranteed on the inline path.
- `netif_rx_mode_sync()`: runs a queued update inline, so the filter is
  programmed before the syscall returns; `dev_change_flags()`,
  `dev_set_promiscuity()` and `dev_set_allmulti()` call it, for example.
- `register_netdevice()`: issues `netdev_WARN()` when the driver is ops-locked
  and has `ndo_set_rx_mode` without `ndo_set_rx_mode_async`; registration
  still succeeds, and there is no other check on these callbacks.
- **Potentially unsafe usage**: walking `dev->uc` or `dev->mc`.
  - Unsafe: inside `ndo_set_rx_mode_async` without `netif_addr_lock_bh()`;
    `netif_rx_mode_run()` has dropped that lock and `dev_mc_add()` can change
    the list.
  - Safe: walking the `uc` and `mc` arguments, as `bnxt_set_rx_mode()` does;
    they are private copies made by `netif_addr_lists_snapshot()`.
  - Safe: under `netif_addr_lock_bh()`, as `fbnic_set_mac()` does; the list
    writers, for example `dev_mc_add()`, take the same lock.

**Deferred work for drivers**

- `netdev_work_sched(dev, events)` in `net/core/netdev_work.c`: ORs
  driver-defined bits into `dev->work_pending` and schedules one global work
  item; it does not sleep.
- `ndo_work(dev, events)`: called by `netdev_work_proc()` under `rtnl_lock`,
  plus the instance lock on ops-locked devices (`netdev_lock_ops()`); may
  sleep.
- Inside `ndo_work` the `netif_*` forms apply, as in `vlan_dev_work()` in
  `net/8021q/vlan_dev.c`.
- Events coalesce: bits scheduled several times before the work runs arrive
  in one call.
- Events are dropped, not retried, when `netif_device_present()` is false at
  run time; see `netdev_work_run()`.
- Events are ignored when the device is past `NETREG_REGISTERED`
  (`dev_isalive()`), and `unregister_netdevice_many_notify()` clears what is
  pending with `netdev_work_cancel_all()`.
- The core holds a reference on the device while work is queued
  (`work_tracker`).
- `netdev_work_cancel(dev, mask)`: clears pending bits and returns those that
  were pending, so the caller can run them inline; it gives no guarantee about
  a run already in progress, except that a caller that holds `rtnl_lock`, or
  the instance lock on an ops-locked device, cannot race with one.
  `vlan_dev_open()` and `vlan_dev_stop()` use it.
- The same work item runs the core's deferred rx-mode update; see "Address
  filter callback".

**Statistics callback context**

- Models have this right; see `dev_get_stats()` in `net/core/dev.c`, which
  takes no lock and makes no test of `netif_running()`.

**Sleeping counter reads**

- Models have this right; see "Notes for driver authors" in
  `Documentation/networking/statistics.rst`.
- The document names no mechanism for the periodic refresh, only that the
  ethtool interrupt coalescing interface can set its frequency; it says
  nothing about how the cached copy is protected or about ethtool statistics
  reads being allowed to sleep.

## Device lifetime and teardown

**Allocation and registration**

- `register_netdev()`: takes the lock with `rtnl_net_lock_killable()` and
  returns `-EINTR` without registering if the task is killed while waiting.
- `netdev->lock`: `register_netdevice()` and
  `unregister_netdevice_many_notify()` call `netdev_lock(dev)` for every
  device, ops-locked or not, to write `reg_state`; a caller that holds the
  instance lock deadlocks.
- `unregister_netdevice_queue_net()`: a form some `dellink` implementations
  use (for example `__geneve_dellink()`, and `veth_dellink()` for the peer);
  caller holds rtnl. It is an inline wrapper of
  `unregister_netdevice_queue()` unless `CONFIG_DEBUG_NET_SMALL_RTNL` is set.
- NAPI instances need not exist before registration; `__bnxt_open_nic()` adds
  them and `__bnxt_close_nic()` deletes them.
- `register_netdevice()`: `BUG_ON()` unless `reg_state` is
  `NETREG_UNINITIALIZED`, so an unregistered device cannot be registered
  again.
- `unregister_netdevice_many_notify()`: `WARN_ON(1)` and skips a device that
  is `NETREG_UNINITIALIZED`, `BUG_ON()` for any state but
  `NETREG_REGISTERED`; do not unregister after a failed registration.
- `register_netdevice()` fails or warns on incomplete ops; see its first
  checks. Easy to miss: an ops-locked device with `ndo_set_rx_mode` and no
  `ndo_set_rx_mode_async` gets a `netdev_WARN()`.
- `devm_register_netdev()`: attaches the unregister action to
  `ndev->dev.parent`, so `SET_NETDEV_DEV()` must come first.

**Freeing a net_device**

- `priv_destructor`: the core calls it from two places only,
  `netdev_run_todo()` (rtnl not held, references gone, before the optional
  `free_netdev()`) and the error path of `register_netdevice()` (rtnl held).
  `free_netdev()` never calls it.
- Failed `register_netdevice()`, by where it failed:

| Failure point | `ndo_uninit` | `priv_destructor` |
|---|---|---|
| `ethtool_check_ops()`, name, `ndo_init` | not called | not called |
| after `ndo_init`, up to `netdev_register_kobject()` | called before return | called before return |
| `NETDEV_REGISTER` notifier | called before return, from `unregister_netdevice_many_notify()` | called later, from `netdev_run_todo()` |

- `needs_free_netdev` after a failed registration: the caller frees in every
  case; only the notifier-failure path clears the flag.
- `needs_free_netdev` after `unregister_netdev()`: `netdev_run_todo()` runs
  inside `rtnl_unlock()`, so the device is already freed when
  `unregister_netdev()` returns.
- `free_netdev()` under rtnl right after `unregister_netdevice()`, as in
  `qmimux_register_device()`: `reg_state` is `NETREG_UNREGISTERING`, so it
  only sets `needs_free_netdev`; `netdev_run_todo()` frees the device at
  `rtnl_unlock()`. The same holds for the caller's `free_netdev()` after a
  `register_netdevice()` that failed in the `NETDEV_REGISTER` notifier:
  that path has called `unregister_netdevice_queue()`, so the device is
  `NETREG_UNREGISTERING` and `priv_destructor` has not run yet.
- `rtnl_newlink_create()`: calls `free_netdev()` itself when `newlink` or
  `register_netdevice()` fails; a `newlink` implementation must not free the
  device it was passed.
- `devm_alloc_etherdev_mqs()`: `devm_free_netdev()` frees at devres release;
  the driver does not call `free_netdev()`.
- **Unsafe usage**: reading anything through `netdev_priv()` after
  `free_netdev()`, or after `unregister_netdev()` when `needs_free_netdev` is
  set.
  - Safe: release what hangs off priv first and call `free_netdev()` last, as
    `igb_remove()` does; `netdev_release()` frees priv with the device.
- **Unsafe usage**: freeing memory that holds a `struct napi_struct` still on
  `dev->napi_list` before `free_netdev()`; `netdev_napi_exit()` dereferences
  each one.
  - Safe: `netif_napi_del()` before freeing that memory, or
    `__netif_napi_del()` and an RCU grace period, as `ixgbe_free_q_vector()`
    does with `kfree_rcu()`.
  - Safe: the NAPI struct lives inside the `netdev_priv()` area, as `napi` in
    `struct rtl8169_private`; `free_netdev()` runs `netdev_napi_exit()`
    before the device memory is freed.

**Stopping timers and work**

- There is no del_timer_sync() or del_timer() in this tree; the names are
  `timer_delete_sync()` and `timer_delete()`.
- `timer_delete_sync_try()`: exists; returns -1 if the handler is running and
  does not wait.
- `cancel_work_sync()` and `cancel_delayed_work_sync()`: reject queueing from
  any source while they wait, then re-enable before returning; nothing blocks
  queueing afterwards.
- `disable_work_sync()` family: a depth count; each call needs its own
  `enable_work()`.
- Queueing a disabled item: returns `false` and the request is dropped.
- `timer_shutdown_sync()` in `ndo_stop`: the timer stays dead in the next
  `ndo_open`; `__mod_timer()` returns without arming until `timer_setup()`
  runs again.
- Stop/open pairing: `rtl8169_down()` calls `disable_work_sync()` and
  `rtl8169_up()` calls `enable_work()`.
- **Unsafe usage**: `cancel_work_sync()` or `timer_delete_sync()` in remove
  while the device is still registered and a callback can queue the item
  again; the handler then runs after `free_netdev()`.
  - Safe: after `unregister_netdev()` has closed the device and before
    `free_netdev()`, as `bnxt_remove_one()` does.

**Watchdog and netpoll against teardown**

- There is no dev_watchdog_down() here; `netdev_watchdog_down()` in
  `net/sched/sch_generic.c` does that, called from `dev_deactivate_many()`
  before `ndo_stop`.
- `dev_watchdog()`: holds `dev->tx_global_lock` for the whole scan and skips
  the device if `qdisc_tx_is_noop()`.
- `ndo_tx_timeout`: runs with `tx_global_lock` held and queues frozen by
  `netif_freeze_queues()`; no `_xmit_lock` is held during the call.
- `netdev_watchdog_down()`: uses `timer_delete()`, not a sync variant, under
  `netif_tx_lock_bh()`. A late `dev_watchdog()` can still run but finds noop
  qdiscs (and, on the close path, `netif_running()` false), so it does not
  call `ndo_tx_timeout`.
- `netif_tx_disable()`: takes `tx_global_lock` as well as each `_xmit_lock`,
  so it waits for a running `ndo_tx_timeout`.
- `netif_tx_stop_queue()`: stamps `trans_start`; a driver path that keeps
  queues stopped longer than `watchdog_timeo` while running, present and
  carrier-on gets `ndo_tx_timeout`.
- Netpoll transmit in `__netpoll_send_skb()`: `HARD_TX_TRYLOCK()` on one
  queue's `_xmit_lock`, then `netif_xmit_stopped()`; it does not take
  `tx_global_lock`.
- `netpoll_poll_disable()`: not exported, called only from `net/core/dev.c`;
  it blocks `netpoll_poll_dev()` and not netpoll transmit.
- On a driver's own reset or resize path `napi_disable()` is what keeps
  netpoll's poll out; `ndo_poll_controller` is not gated by NAPI state,
  `netpoll_poll_dev()` tests only `dev_lock`, `netif_running()` and
  `netif_local_xmit_active()` before it.
- **Unsafe usage**: calling `netif_tx_disable()` or `netif_tx_lock()` from
  `ndo_tx_timeout`; `dev_watchdog()` already holds `tx_global_lock`.
  - Safe: only schedule work from the callback, as `igb_tx_timeout()` does.

**Callbacks on a closed device**

- `netif_running()` inside `ndo_stop` called by the core: false;
  `__dev_close_many()` clears `__LINK_STATE_START` first.
- `netif_running()` inside `ndo_open`: true; `__dev_open()` sets the bit
  before the call and clears it if `ndo_open` fails.
- A driver that calls its own stop function sees `netif_running()` true;
  `__igb_shutdown()` calls `__igb_close()` only when it is true.
- `ndo_open` and `ndo_stop` run under the lock that
  `netdev_assert_locked_ops_compat()` asserts, which the ethtool ioctl and
  netlink handlers also hold (see "Ethtool callback locking"), so a
  `netif_running()` test in an ethtool op called from them is still
  serialised against open and close.
- Ethtool ops are gated on `netif_device_present()`, not on up: `-ENODEV` in
  `ethnl_ops_begin()` and `dev_ethtool_locked()`.
- `ndo_get_stats64`: called under `rcu_read_lock()` without rtnl, for example
  from `dev_seq_printf_stats()`; it cannot sleep or take a mutex.
- `ndo_set_rx_mode` on the inline path of `__dev_set_rx_mode()` (driver not
  ops-locked, no `ndo_set_rx_mode_async`, no `ndo_change_rx_flags`): gated on
  `IFF_UP`, which is still set while `ndo_stop` runs, and reachable without
  rtnl through `dev_mc_add()`; it can run concurrently with `ndo_stop`.
- `struct netdev_stat_ops`: `netdev_nl_stats_by_netdev()` calls
  `get_base_stats` and, through `netdev_stat_queue_sum()`, the per-queue
  callbacks with no `IFF_UP` test; only `netdev_nl_stats_by_queue()` tests it.
- `ndo_work`: `netdev_work_run()` tests `netif_device_present()` only.
- **Potentially unsafe usage**: `ndo_get_stats64` reading per-ring memory.
  - Unsafe: when `ndo_stop` frees the rings with nothing that makes the
    reader finish first; a `netif_running()` test alone does not.
  - Safe: ring pointers read with `READ_ONCE()` under `rcu_read_lock()` and
    freed with `kfree_rcu()`, as `ixgbe_get_stats64()` and
    `ixgbe_free_q_vector()` do.
  - Safe: a reader bit the close path waits on; `bnxt_get_stats64()` sets
    `BNXT_STATE_READ_STATS` before it tests `BNXT_STATE_OPEN`, and
    `__bnxt_close_nic()` clears `BNXT_STATE_OPEN` and then polls
    `bnxt_drv_busy()`.

**Reset work against close**

- Ops-locked drivers: `ndo_stop` also runs with `netdev->lock` held, so
  waiting in `ndo_stop` for work that takes `netdev_lock()` deadlocks the
  same way as for work that takes `rtnl_lock()`.
- bnxt: `bnxt_rtnl_lock_sp()` clears `BNXT_STATE_IN_SP_TASK`, then takes
  `rtnl_lock()` and `netdev_lock()`; `cancel_work_sync()` on `sp_task` is only
  in `bnxt_remove_one()`, after `unregister_netdev()`.
- **Unsafe usage**: `cancel_work_sync()`, `disable_work_sync()` or
  `flush_work()` from `ndo_stop` on work that calls `rtnl_lock()`.
  - Safe: close sets a down bit and does not wait; the work tests the bit
    after `rtnl_lock()`, as `igb_down()` and `igb_reset_task()` do with
    `__IGB_DOWN`. `e1000e_down()` and `e1000_reset_task()` in
    `drivers/net/ethernet/intel/e1000e/netdev.c` do the same with
    `__E1000_DOWN`.
  - Safe: the work drops its busy bit before `rtnl_lock()` and close waits on
    the bit, as `bnxt_rtnl_lock_sp()` and `__bnxt_close_nic()` do.
  - Safe: the work takes no rtnl; `rtl_task()` does not, so `rtl8169_down()`
    calls `disable_work_sync()` under rtnl.

## NAPI

**NAPI control calls**

- `netif_napi_add()`, `napi_enable()`, `napi_disable()`, `netif_napi_del()`: each
  takes `netdev_lock()` (the mutex `dev->lock`) itself, so each can sleep and
  each deadlocks if the caller already holds that lock.
- `napi_enable_locked()`: can sleep only when `n->config` is set;
  `napi_restore_config()` calls `napi_set_threaded()`, which can create or
  stop the kthread.
- NAPI id and `napi_hash`: `napi_enable_locked()` assigns the id and hashes
  the instance, `napi_disable_locked()` unhashes it and leaves `napi_id` set;
  `netif_napi_add()` and `netif_napi_del()` do not touch the hash, so a new
  instance is assigned no NAPI id until it is enabled.
- `napi_hash_add()`: does nothing for an instance with
  `NAPI_STATE_NO_BUSY_POLL`, which `netif_napi_add_tx()` sets, so such an
  instance gets no id from it.
- `napi_disable_locked()`: waits in `usleep_range()`, not `msleep()`, with the
  instance lock held for the whole wait.
- `napi_enable_locked()`: has no `netdev_assert_locked()`, so lockdep does not
  catch a caller without the lock; `napi_disable_locked()`,
  `netif_napi_add_weight_locked()` and `__netif_napi_del_locked()` do assert.
- `netdev_assert_locked()`: is `lockdep_assert_held()`, see
  `include/net/netdev_lock.h`.
- `netif_napi_del()` on an enabled instance: `__netif_napi_del_locked()` hits
  `WARN_ON()` if `NAPI_STATE_SCHED` is clear, then deletes anyway.
- **Potentially unsafe usage**: `napi_enable_locked()` under a spinlock.
  - Unsafe: when the instance was added with `netif_napi_add_config()`, so
    `n->config` is set and `napi_restore_config()` may sleep.
  - Safe: when `n->config` is NULL and `netdev_lock()` was taken before the
    spinlock, as `nv_open()` in `drivers/net/ethernet/nvidia/forcedeth.c` does;
    `napi_enable_locked()` calls `napi_restore_config()` only if `n->config`.

**Repeated enable or disable**

- Second `napi_enable()`: `napi_enable_locked()` runs `napi_restore_config()`
  or `napi_hash_add()` again before it reaches the `BUG_ON()`.
- Second `napi_enable()` while a poll is scheduled: `NAPI_STATE_SCHED` is set,
  so the `BUG_ON()` passes and the bit is cleared under the poll that owns it.
- Second `napi_disable()`: the wait is `TASK_UNINTERRUPTIBLE` and holds
  `netdev_lock()`, so a `napi_enable()` from another task blocks on the lock
  and cannot end the wait.
- `napi_disable()` on an instance that was added and never enabled: hangs the
  same way; `netif_napi_add_weight_locked()` sets the two bits the loop in
  `napi_disable_locked()` waits on.
- **Unsafe usage**: `napi_disable()` on an instance that is not enabled.
  - Safe: test a driver flag first, as `ibmvnic_napi_disable()` in
    `drivers/net/ethernet/ibm/ibmvnic.c` tests `adapter->napi_enabled`; the
    wait loop in `napi_disable_locked()` defines the requirement.
- **Unsafe usage**: `napi_enable()` on an instance that is already enabled.
  - Safe: test a driver flag first, as `ibmvnic_napi_enable()` does; the
    `BUG_ON()` in `napi_enable_locked()` defines the requirement.

**Poll return value**

- Return above budget: `__napi_poll()` prints `netdev_err_once()`, there is no
  WARN; the value is then handled like `work == weight`.
- Exactly budget with nothing left: two forms are valid, see the warning in
  `Documentation/networking/napi.rst`.
  - Return `budget` and do not call `napi_complete_done()`.
  - Call `napi_complete_done()` and return `budget - 1`, as `ixgbe_poll()` does
    with `min(work_done, budget - 1)`.
- Returning `budget` after `napi_complete_done()`: `__napi_poll()` sets
  `*repoll` and `napi_poll()` queues an instance the core no longer owns.
- Diagnostics for that case: `pr_warn_once()` only if `n->poll_list` is already
  non-empty; `pr_crit()` in `napi_poll()` only under `CONFIG_DEBUG_NET`.
- Returning `budget` does not guarantee another poll: `__napi_poll()` calls
  `napi_complete()` itself when `napi_disable_pending()`, and
  `napi_complete_done()` when `napi_prefer_busy_poll()`.
- `napi_complete_done()`: never sees the budget; `work_done` is only tested
  for non-zero.
- `napi_complete_done()`: does not test `NAPI_STATE_DISABLE` or
  `NAPI_STATE_PREFER_BUSY_POLL`; it clears the latter.
- `napi_complete_done()` returns false in exactly three cases:

| Case | `NAPI_STATE_SCHED` afterwards |
|---|---|
| `NAPIF_STATE_NPSVC` or `NAPIF_STATE_IN_BUSY_POLL` set | unchanged, nothing done |
| `n->defer_hard_irqs_count > 0` and the gro flush timeout is non-zero | cleared, `n->timer` armed |
| `NAPIF_STATE_MISSED` was set | left set, `__napi_schedule()` called |

- A false return means "do not unmask", not "still owned": in the deferral
  case the instance has been released.

**Zero budget polls**

- Context of the zero-budget call: `__netpoll_send_skb()` in
  `net/core/netpoll.c` asserts IRQs disabled, then reaches `poll_one_napi()`
  through `netpoll_poll_dev()`.
- Non-zero return from a zero-budget call: `WARN_ONCE()` in `poll_one_napi()`.
- `napi_complete_done()` in a zero-budget call from `poll_one_napi()`: returns
  false at its first test, because `poll_one_napi()` holds `NAPI_STATE_NPSVC`.
- `Documentation/networking/napi.rst`: says never to call
  `napi_complete_done()` with budget 0; its example tests `budget &&` first.
- `napi_consume_skb()` with non-zero budget, skb allocated on another CPU:
  goes to `skb_attempt_defer_free()` instead of straight to the local cache,
  unless the skb is shared or `skb_defer_disable_key` is on.
- `napi_consume_skb()` with non-zero budget, fclone skb: freed with
  `__kfree_skb()`, not cached.
- Page pool direct recycling: not controlled by the budget;
  `napi_consume_skb()` does not pass it on, `page_pool_napi_local()` in
  `net/core/page_pool.c` decides.
- **Potentially unsafe usage**: `napi_consume_skb()` with a constant non-zero
  budget.
  - Unsafe: when the caller can run outside softirq or BH-disabled context,
    such as a Tx-clean routine reached from the zero-budget netpoll call;
    `napi_skb_cache_put()` guards the per-CPU cache only with
    `local_lock_nested_bh()`.
  - Safe: when every caller has BH disabled, as `skb_defer_free_flush()` in
    `net/core/dev.c`, which passes 1; `napi_consume_skb()` checks this with
    `DEBUG_NET_WARN_ON_ONCE(!in_softirq())`.
  - Safe: pass the poll function's own `budget` down, as `ixgbe_poll()` does
    to `ixgbe_clean_tx_irq()`; the `!budget` test in `napi_consume_skb()` then
    covers the netpoll call.

## Transmit

**Transmit context and locking**

- `HARD_TX_LOCK()`: defined in `include/linux/netdevice.h`; it takes
  `txq->_xmit_lock` only when `dev->lltx` is clear.
- Callers of the transmit routine: search for `HARD_TX_LOCK` and
  `netdev_start_xmit`; besides the qdisc path, `__dev_queue_xmit()` and
  netpoll there are, for example, `__dev_direct_xmit()`, `generic_xdp_tx()`,
  `xfrm_dev_resume()` and pktgen.
- netpoll, direct path: `__netpoll_send_skb()` retries `HARD_TX_TRYLOCK()` for
  up to one tick, polling the device between tries.
- netpoll, deferred path: on failure the skb goes to `npinfo->txq`, and
  `queue_process()` (a work item) sends it with `HARD_TX_LOCK()` inside
  `local_irq_save()`.
- Qdisc exclusion: there is no __QDISC_STATE_RUNNING here; `qdisc_run_begin()`
  in `include/net/sch_generic.h` uses the `running` field of `struct Qdisc`,
  or `spin_trylock()` on `seqlock` for a `TCQ_F_NOLOCK` qdisc.
- Same-CPU recursion check: `netif_tx_owned()`; on the transmit path it is
  called only in the branch of `__dev_queue_xmit()` for a qdisc with no
  `enqueue`.
- `netif_tx_owned()` under `CONFIG_PREEMPT_RT`: compares `rt_mutex_owner()` of
  `_xmit_lock` with `current`, not `xmit_lock_owner` with the CPU.
- `netif_tx_lock()` in `net/sched/sch_generic.c`: holds only
  `dev->tx_global_lock` on return; `netif_freeze_queues()` takes and drops
  each `_xmit_lock` just to set `__QUEUE_STATE_FROZEN`.

**Lockless transmit opt-out**

- Flag: `lltx`, a one-bit field of `struct net_device` beside `priv_flags`;
  there is no NETIF_F_LLTX feature bit in this tree.
- Deprecation wording: in the `struct net_device` kdoc ("Deprecated for real HW
  drivers") and `Documentation/networking/netdevices.rst` ("meant for software
  drivers only"); `Documentation/networking/netdev-features.rst` does not
  mention it.
- Hardware drivers that set `lltx` exist in the tree (search
  `lltx = true` under `drivers/net/ethernet`); for example
  `pasemi_mac_start_tx()` serialises its ring with its own `txring->lock`
  under `spin_lock_irqsave()`.
- Recursion with `lltx`: `dev_xmit_recursion()` in `__dev_queue_xmit()` still
  bounds nesting at `XMIT_RECURSION_LIMIT`; `netif_tx_owned()` does not catch
  it, because `HARD_TX_LOCK()` does not take `_xmit_lock`.
- `netif_tx_lock()` and `netif_tx_disable()` with `lltx`: they still take
  `_xmit_lock`, which the transmit path does not, so they do not wait for a
  transmit routine that is already running.
- `txq_trans_update()` with `lltx`: does nothing, so `netdev_start_xmit()` does
  not update `trans_start`; a driver that needs it calls
  `netif_trans_update()` or `txq_trans_cond_update()` itself.
- `netdev_uses_bql()` in `net/core/net-sysfs.c`: false when `lltx` is set, so
  the queue gets no BQL sysfs group.

**Transmit return codes**

- `enum netdev_tx` in `include/linux/netdevice.h`: the only return values are
  `NETDEV_TX_OK` and `NETDEV_TX_BUSY`; NETDEV_TX_LOCKED is not defined.
- Any other value: `dev_xmit_complete()` treats every `rc < NET_XMIT_MASK` as
  consumed, which covers negative errno, `NET_XMIT_DROP` and `NET_XMIT_CN`.
- A value that fails `dev_xmit_complete()` and is not `NETDEV_TX_BUSY`:
  `sch_direct_xmit()` logs "BUG %s code %d qlen %d" and requeues the skb.
- After a drop: the value must pass `dev_xmit_complete()`; for example
  `ixgbe_xmit_frame_ring()` returns `NETDEV_TX_OK`, and `veth_xmit()` returns
  `NET_XMIT_DROP`.
- `NETDEV_TX_BUSY`: the caller keeps ownership, and what it does with the skb
  depends on the caller:

| Caller | On `NETDEV_TX_BUSY` |
|---|---|
| `sch_direct_xmit()` | requeues with `dev_requeue_skb()` |
| `__dev_queue_xmit()`, qdisc without `enqueue` | logs "Virtual device %s asks to queue packet!", frees the skb |
| `generic_xdp_tx()`, `dev_direct_xmit()` | `kfree_skb()` |
| `__netpoll_send_skb()` | retries, then queues to `npinfo->txq` |

- `veth_xmit()`: tests `qdisc_txq_has_no_queue()` and drops instead of
  returning `NETDEV_TX_BUSY`; when it does return it, it first restores the
  Ethernet header with `__skb_push()`.
- `Documentation/networking/driver.rst`, exception: `NETDEV_TX_BUSY` is "a hard
  error unless there is no way your device can tell ahead of time when its
  transmit function will become busy".
- `Documentation/networking/driver.rst`, example: on a full ring with the queue
  awake the transmit routine calls `netif_tx_stop_queue()`, `netdev_warn()`
  and returns `NETDEV_TX_BUSY`.
- `Documentation/networking/netdevices.rst` adds that on `NETDEV_TX_BUSY` the
  driver must not have put the skb in its DMA ring.

**Freeing skbs in a driver**

- `dev_kfree_skb()`: `#define dev_kfree_skb(a) consume_skb(a)` in
  `include/linux/skbuff.h`; it means consumed, and it frees directly whatever
  the IRQ state.
- `napi_consume_skb()` with `budget == 0` or a NULL skb: calls
  `dev_consume_skb_any()`.
- Drop in NAPI Tx completion: `dev_kfree_skb_any()`, because of the budget-0
  call from `poll_one_napi()`; see "Zero budget polls".
- **Potentially unsafe usage**: `kfree_skb()`, `consume_skb()` or
  `dev_kfree_skb()` in code reached from `ndo_start_xmit` or from the Tx
  completion part of a NAPI poll.
  - Unsafe: when netpoll can attach to the device; `__netpoll_send_skb()`
    calls both with hard IRQs disabled, the state in which
    `dev_kfree_skb_any_reason()` defers the free to `net_tx_action()`.
  - Safe: the device sets `IFF_DISABLE_NETPOLL`, which `__netpoll_setup()`
    rejects; `veth_xmit()` calls `kfree_skb()` and `veth_setup()` sets the
    flag.
  - Safe: `dev_kfree_skb_any()` or `dev_consume_skb_any()`, which test
    `in_hardirq() || irqs_disabled()` in `dev_kfree_skb_any_reason()`.

**Byte queue limits**

- `netdev_tx_completed_queue()`: ignores `pkts`; only `bytes` has to balance.
- `netdev_tx_completed_queue()` with `bytes == 0`: returns before
  `dql_completed()` and before its `smp_mb()`.
- Balance at every instant: `dql_completed()` in
  `lib/dynamic_queue_limits.c` has `BUG_ON(count > num_queued -
  dql->num_completed)` on each call, so bytes must be reported sent before
  the completion handler can report them.
- `dql_queued()` with `count > DQL_MAX_OBJECT`: `WARN_ON_ONCE()` and the bytes
  are not counted, so completing them later breaks the balance.
- `netdev_tx_sent_queue()`: returns void; the doorbell decision comes from
  `__netdev_tx_sent_queue()`.
- `__netdev_tx_sent_queue()` with `xmit_more` true: only counts the bytes,
  does not set `__QUEUE_STATE_STACK_XOFF`, and returns
  `netif_tx_queue_stopped()`.
- `__netdev_tx_sent_queue()` without `CONFIG_BQL`: still returns that value,
  or `true` when `xmit_more` is false.
- Core and reset: nothing under `net/` calls `netdev_tx_reset_queue()`;
  `dql_init()` runs once, in `netdev_init_one_queue()`, so BQL state survives
  `ndo_stop` and `ndo_open` unless the driver resets it.
- **Unsafe usage**: `netdev_tx_reset_queue()` while transmit or completion for
  that queue can still run, or a completion report afterwards for packets
  queued before it; `dql_reset()` zeroes `num_queued` and `num_completed`
  with no lock, so the `BUG_ON()` in `dql_completed()` can fire.
  - Safe: stop transmit and NAPI first, then free the ring without reporting
    completion, then reset; `ixgbe_down()` calls `netif_tx_disable()` and
    `ixgbe_napi_disable_all()` before `ixgbe_clean_all_tx_rings()`.

**Stopping and waking queues**

- Stop helpers: `netif_txq_maybe_stop()` and, under it,
  `netif_txq_try_stop()`; there is no __netif_txq_maybe_stop() in this tree.
- `down_cond`: an argument of `__netif_txq_completed_wake()` only;
  `netif_txq_completed_wake()` takes five arguments and passes `false`.
- Stop-side barrier: `smp_mb__after_atomic()`, which relies on the `set_bit()`
  in `netif_tx_stop_queue()`.
- Wake-side barrier: comes from `netdev_txq_completed_mb()`, which issues
  none when `bytes` is 0, with or without `CONFIG_BQL`.
- `__netif_txq_completed_wake()` with `pkts == 0`: never wakes and returns -1,
  whatever `get_desc` says.
- Ring indexes: the macros require no particular representation; `get_desc`
  is any expression, and the example in
  `Documentation/networking/driver.rst` masks the index difference.
- Stop side, context: it re-enables with `netif_tx_start_queue()`, which does
  not reschedule the qdisc, so outside the transmit routine the queue can end
  up enabled but not run.
- Wake side, context: no context restriction; the DOC comment in
  `include/net/netdev_queues.h` assumes that no two wake attempts for one
  queue run concurrently.
- False wake-ups: not prevented, says the same DOC comment; the transmit
  routine must still test for a full ring at its start.
- Return values: 0 means the stop or wake happened; 1 means nothing was
  done (the queue was left enabled, was already enabled, or `down_cond` held);
  -1 means the stop raced and was undone, or the wake threshold was not
  reached.
- BQL: the wake macros report completion through
  `netdev_tx_completed_queue()`, so the driver must not report the same bytes
  again; the stop macros report nothing, and the driver calls
  `netdev_tx_sent_queue()` itself.
- `__ixgbe_maybe_stop_tx()`: calls `netif_subqueue_try_stop()`; it is not
  open-coded here.
- bnxt: the `__netif_txq_completed_wake()` call is in `__bnxt_tx_int()`.

## Receive buffers and XDP

**Page pool usage**

- `allow_direct == false` does not mean "ring only":
  `page_pool_put_unrefed_netmem()` in `net/core/page_pool.c` recycles into
  the lockless cache anyway when `page_pool_napi_local()` is true.
- That upgrade applies to every return path, for example
  `napi_pp_put_page()` (which itself passes `false`), `xdp_return_frame()`
  and a driver's `page_pool_put_full_page(pool, page, false)`;
  `page_pool_put_netmem_bulk()` makes the same test.
- `page_pool_napi_local()`: true only when not `CONFIG_PREEMPT_RT`,
  `in_softirq()`, and this CPU equals the pool's `cpuid` or
  `napi->list_owner`. It has no busy-poll test.
- `cpuid` of `struct page_pool`: -1 from `page_pool_create()`; a real CPU
  only from `page_pool_create_percpu()`.
- `list_owner`: `____napi_schedule()` writes the CPU only when it queues the
  NAPI on the per-CPU poll list; the threaded wake-up path returns before
  that. `napi_complete_done()` resets it to -1.
- Hardirq or IRQs disabled: no page may be returned at all, by either path;
  `__page_pool_put_page()` has `lockdep_assert_no_hardirq()`.
- Ring path from process context: the caller need not disable BH;
  `page_pool_producer_lock()` takes the `_bh` lock itself outside softirq.
- `xdp_return_buff()`, `xdp_return_frag()` and `xdp_return_frame_rx_napi()`
  in `net/core/xdp.c` pass direct = true, so they carry the same context
  rule as `page_pool_recycle_direct()`; `__xdp_return()` drops the direct
  flag only when `xdp_return_frame_no_direct()` is true.
- `page_pool_destroy()` is refcounted by `user_cnt`: only the call that
  drops it to zero tears the pool down; earlier calls just return.
- XDP registration holds one `user_cnt` reference
  (`page_pool_use_xdp_mem()`), and `xdp_unreg_mem_model()` drops it by
  calling `page_pool_destroy()`.
- A pool registered with `xdp_rxq_info_reg_mem_model()` therefore needs both
  `xdp_rxq_info_unreg()` and the driver's own `page_pool_destroy()`, in
  either order.
- The "Driver unload" example in `Documentation/networking/page_pool.rst`
  shows `xdp_rxq_info_unreg()` and no `page_pool_destroy()`; on its own that
  leaves `user_cnt` at 1 and the pool is never torn down.
- `p.napi` is read by `page_pool_napi_local()` on page returns until
  `page_pool_disable_direct_recycling()` clears it; in the core only the
  last `page_pool_destroy()` calls that.
- A driver that frees the `struct napi_struct` before the last
  `page_pool_destroy()` must first call
  `page_pool_disable_direct_recycling()`, after `napi_disable()`;
  `enet_rx_stop()` in `drivers/net/ethernet/alibaba/eea/eea_rx.c` calls it
  between `napi_disable()` and `netif_napi_del()`.
- `page_pool_disable_direct_recycling()` with `p.napi` set: runs
  `napi_assert_will_not_race()` in `net/core/dev.h`, which WARNs unless
  `NAPI_STATE_SCHED` is set and `list_owner` is -1, or the NAPI was never
  added.
- DMA at destroy: the first release pass in `page_pool_scrub()` clears
  `dma_sync` and unmaps every page still recorded in `dma_mapped`,
  in-flight pages included, when `PP_DMA_INDEX_BITS` is non-zero.
- The device must have stopped DMA into pool pages before the last
  `page_pool_destroy()`; a page returned afterwards is only freed.
- `PP_DMA_INDEX_BITS` zero: pages are not tracked; an in-flight page keeps
  its mapping until it comes back to the pool.
- "stalled pool shutdown" warning: `page_pool_release_retry()` prints it
  only when `slow.netdev` is NULL or `NET_PTR_POISON`. A pool created with
  `netdev` set stalls silently; `page_pool_unreg_netdev()` re-points it at
  the loopback device when its netdev unregisters.

**Recycling pages through skbs**

- Frag free path: `skb_release_data()` calls `__skb_frag_unref()` →
  `skb_page_unref()` in `include/linux/skbuff_ref.h`; there is no
  napi_frag_unref() in this tree.
- Per-page test: `netmem_is_pp()` in `net/core/netmem_priv.h`, applied to
  the compound head and masked with `PP_MAGIC_MASK`, which drops the DMA
  index bits and bits 0-1 of `pp_magic`.
- `page_pool_page_is_pp()` in `include/linux/mm.h` is the same test for the
  page allocator, not the one the skb path calls.
- Unmarked skb: `skb_page_unref()` falls to `put_netmem()` and the head to
  `skb_free_frag()`; nothing on that path unmaps DMA, increments
  `pages_state_release_cnt` or clears `pp_magic`. No page-free hook unmaps.
- Unmarked page, DMA, when `PP_DMA_INDEX_BITS` is non-zero: its entry stays
  in the pool's `dma_mapped` xarray, pointing at a page the pool no longer
  owns.
- Unmarked page reaching the allocator with `check_pages_enabled` on
  (default with `CONFIG_DEBUG_VM`): `free_page_is_bad()` reports
  "page_pool leak" from `page_bad_reason()`, and `__free_pages_prepare()`
  returns false, so the page is not freed.
- Unmarked page with `check_pages_enabled` off: it is freed to the
  allocator with no report.
- Detaching a page: there is no page_pool_release_page() here. The only
  detach is the static `page_pool_return_netmem()`, reached for example
  when `page_pool_put_page()` finds the page refcount is not 1.
- `mlx5e_build_linear_skb()` does not call `skb_mark_for_recycle()`; its
  callers do, for example `mlx5e_skb_from_cqe_linear()`.
- `xdp_build_skb_from_buff()` and `__xdp_build_skb_from_frame()` set the
  mark themselves when the memory type is `MEM_TYPE_PAGE_POOL`;
  `xdp_build_skb_from_zc()` always sets it. A driver using them needs no
  call of its own.

**XDP in a receive path**

- `napi_id` argument of `__xdp_rxq_info_reg()`: not stored or used;
  `struct xdp_rxq_info` has no field for it, so the value passed does not
  matter.
- Second way to bind a pool: `xdp_reg_page_pool()` once per pool, then
  `xdp_rxq_info_attach_page_pool()` per queue in place of
  `xdp_rxq_info_reg_mem_model()`; `libeth_rx_fq_create()` does the first
  step.
- **Unsafe usage**: `xdp_rxq_info_unreg()` on a queue whose pool was bound
  with `xdp_rxq_info_attach_page_pool()` and not detached; it calls
  `page_pool_destroy()` and drops a `user_cnt` reference the queue never
  took.
  - Safe: `xdp_rxq_info_detach_mem_model()` first, as
    `__idpf_xdp_rxq_info_deinit()` does; the reference taken by
    `xdp_reg_page_pool()` is dropped by `xdp_unreg_page_pool()`.
  - Safe: no detach when the pool was bound with
    `xdp_rxq_info_reg_mem_model()`, which took the reference that
    `xdp_rxq_info_unreg()` drops, as in `mvneta_create_page_pool()` and
    `mvneta_rxq_drop_pkts()`.
- `xdp_do_check_flushed()`: real only with both `CONFIG_DEBUG_NET` and
  `CONFIG_BPF_SYSCALL`; `__napi_poll()` calls it right after `->poll()`
  returns, and it flushes the leftover lists before it warns.
- `xdp_do_redirect()` failure: the redirect error tracepoint has already
  fired inside it (`_trace_xdp_redirect_map_err()`, called on the error
  paths in `net/core/filter.c`); what the driver still owes is the buffer.
- `trace_xdp_exception()` after a failed redirect: a per-driver addition,
  as in `ixgbe_run_xdp()`; no core code depends on it.
- `bpf_prog_run_xdp()` can hand the driver `XDP_REDIRECT` or `XDP_ABORTED`
  for a program that returned `XDP_TX`: on a bond slave, with
  `bpf_master_redirect_enabled_key` on, it calls `xdp_master_redirect()`.
- The flush duty follows the verdict the driver sees, so a driver that
  handles `XDP_TX` on a bond slave also needs the `XDP_REDIRECT` branch and
  `xdp_do_flush()`.
- `xdp_do_redirect()` and `xdp_do_flush()` dereference
  `current->bpf_net_context`; the NAPI core sets it around `->poll()` with
  `bpf_net_ctx_set()`, but `poll_one_napi()` in `net/core/netpoll.c` does
  not.
- XDP run outside `->poll()` must set the context itself, with BH disabled,
  as `tun_sendmsg()` in `drivers/net/tun.c` does.
- Dropping a multi-buffer frame: every frag must go back as well as the
  head; `xdp_return_buff()` does both, with direct recycling unless
  `xdp_set_return_frame_no_direct()` is in effect, so without that it is
  for the NAPI poll only.

## u64_stats counters

**64-bit counter helpers**

- Variant selection: `include/linux/u64_stats_sync.h` tests `BITS_PER_LONG`
  only; no `CONFIG_` symbol appears in the header.
- `u64_stats_add()` and `u64_stats_inc()` on 64-bit: `local64_add()` and
  `local64_inc()` resolve to the arch `local_add()` and `local_inc()`; x86
  uses an unlocked `add`/`inc` in `arch/x86/include/asm/local.h`, while
  `include/asm-generic/local.h` maps them to `atomic_long_add()` and
  `atomic_long_inc()`.
- `u64_stats_update_begin()` on 32-bit: `preempt_disable_nested()` then
  `write_seqcount_begin()`; `u64_stats_update_end()` is
  `write_seqcount_end()` then `preempt_enable_nested()`.
- `u64_stats_add()`: takes `unsigned long` on both word sizes, so on 32-bit a
  value wider than 32 bits is truncated before the add; `u64_stats_sub()`
  takes `s64` and `u64_stats_set()` takes `u64`.
- `u64_stats_copy()`: defined for both word sizes; a loop of `local64_read()`
  over 64-bit words on 64-bit, `memcpy()` on 32-bit; `BUILD_BUG_ON()` if `len`
  is not a multiple of `sizeof(u64_stats_t)`.
- `u64_stats_copy()` arguments are `void *`; in-tree callers pass structs of
  plain `u64`, for example `struct macsec_rx_sc_stats`.
- Plain `u64` counters under a `struct u64_stats_sync`: present in-tree, for
  example `struct vxlan_vni_stats` in `include/net/vxlan.h`; nothing enforces
  `u64_stats_t`.
- Plain `u64` counters on 64-bit: the begin, end and fetch helpers are empty,
  so those fields get ordinary loads and stores and nothing else.

**Writers and interrupt context**

- `u64_stats_update_begin_irqsave()`: also needed when a reader of the same
  `struct u64_stats_sync` can run in interrupt context on the writer's CPU; on
  32-bit `__read_seqcount_begin()` in `include/linux/seqlock.h` spins while the
  sequence is odd.
- 32-bit, not `CONFIG_PREEMPT_RT`: the irqsave variant satisfies the
  preemption assertion without help, because
  `lockdep_assert_preemption_disabled()` accepts hardirqs disabled; it can be
  called with `preempt_count()` zero.
- 32-bit, `CONFIG_PREEMPT_RT`: `local_irq_save()` followed by
  `preempt_disable()` through `preempt_disable_nested()`.
- 64-bit: `__u64_stats_irqsave()` returns 0 and interrupts stay enabled, so
  the pair excludes nothing; only `u64_stats_t` updates, which go through
  `local64_t` operations such as `local64_add()`, get any help, and a plain
  `u64` `+=` shared with an interrupt handler gets none.
- Reader variants: none are defined; no name beginning u64_stats_fetch_begin_
  or u64_stats_fetch_retry_ exists anywhere in the tree, so readers in every
  context use `u64_stats_fetch_begin()` and `u64_stats_fetch_retry()`.

**Writer exclusion and preemption**

- `u64_stats_update_begin()` on 32-bit, not `CONFIG_PREEMPT_RT`: asserts
  preemption is off, once in `preempt_disable_nested()` and again in
  `__seqprop_assert()` from `write_seqcount_begin()`; it disables nothing.
- `lockdep_assert_preemption_disabled()` in `include/linux/lockdep.h`: an
  empty macro without `CONFIG_PROVE_LOCKING`; with it, warns only when
  `CONFIG_PREEMPT_COUNT` is set, `preempt_count()` is 0 and hardirqs are
  enabled.
- `u64_stats_update_begin()` on 64-bit: empty in every configuration,
  including `CONFIG_PREEMPT_RT`; it neither disables nor asserts.
- Writer exclusion: `seq` is a plain `seqcount_t` with no associated lock, so
  the write path has no `lockdep_assert_held()`; that assertion exists only in
  the `seqcount_LOCKNAME_t` variants in `include/linux/seqlock.h`.
- The per-CPU stats helpers in `include/linux/netdevice.h`, for example
  `dev_sw_netstats_rx_add()`, `dev_lstats_add()` and `dev_dstats_tx_add()`:
  `this_cpu_ptr()` plus plain `u64_stats_update_begin()`; they establish no
  context, the caller must.
- **Potentially unsafe usage**: `u64_stats_update_begin()`, directly or
  through one of the `include/linux/netdevice.h` helpers above.
  - Unsafe: when the caller is preemptible with interrupts enabled; on 32-bit
    without `CONFIG_PREEMPT_RT` a reader that preempts the section spins in
    `__read_seqcount_begin()`, and `preempt_disable_nested()` warns under
    `CONFIG_PROVE_LOCKING`.
  - Safe: per-CPU stats taken with `get_cpu_ptr()` and released with
    `put_cpu_ptr()` after the end call, as `iptunnel_xmit_stats()` in
    `include/net/ip_tunnels.h` does; `get_cpu_ptr()` calls
    `preempt_disable()`, which the assertion in `preempt_disable_nested()`
    accepts.
  - Safe: per-CPU stats inside `local_bh_disable()`, as
    `nft_counter_do_eval()` in `net/netfilter/nft_counter.c` does; without
    `CONFIG_PREEMPT_RT` this raises `preempt_count()`, which the assertion in
    `preempt_disable_nested()` accepts.
  - Safe: shared stats with `preempt_disable()` around the section and an
    outer lock for exclusion, as `mdiobus_stats_acct()` in
    `drivers/net/phy/mdio_bus.c` does; each caller asserts `bus->mdio_lock`
    with `lockdep_assert_held_once()`.
  - Safe: `u64_stats_update_begin_irqsave()`, which meets the assertion in
    `preempt_disable_nested()` by disabling interrupts.

**Reader loops**

- Reader context: `u64_stats_fetch_begin()` and `u64_stats_fetch_retry()` hold
  nothing across the loop; they neither disable nor assert preemption, so the
  body may be preempted or interrupted.
- `seqcount_lockdep_reader_access()`: on 32-bit under
  `CONFIG_DEBUG_LOCK_ALLOC` it saves and restores interrupts inside
  `u64_stats_fetch_begin()` only, not across the body.
- **Potentially unsafe usage**: `+=` inside the fetch loop body.
  - Unsafe: when the code can be built for 32-bit and the left-hand side
    holds a value from before this pass, such as a running total over queues
    or CPUs; a retry adds the same counters again.
  - Safe: when the same pass assigns the variable with `=` first, as
    `bnge_get_ring_stats64()` in
    `drivers/net/ethernet/broadcom/bnge/bnge_netdev.c` does; the totals are
    added after the loop.
  - Safe: when the code is built for 64-bit only, as `hinic3_get_stats64()` in
    `drivers/net/ethernet/huawei/hinic3/hinic3_netdev_ops.c`, whose
    `CONFIG_HINIC3` depends on `CONFIG_64BIT`; `__u64_stats_fetch_retry()`
    returns `false` there, so the loop never retries.
- `u64_stats_copy()`: makes no fetch call itself and belongs inside the loop,
  copying into a local struct; `br_multicast_get_stats()` in
  `net/bridge/br_multicast.c` and `vxlan_vnifilter_stats_get()` in
  `drivers/net/vxlan/vxlan_vnifilter.c` sum per-CPU stats this way.
- There is no ip_tunnel_get_stats64() in this tree; `dev_get_tstats64()` in
  `net/core/dev.c` does that job through `dev_fetch_sw_netstats()`.
- `netdev_stats_to_stats64()`: not a u64_stats reader; it reads the
  `atomic_long_t` fields of `struct net_device_stats` with
  `atomic_long_read()` and uses no `struct u64_stats_sync`.
- `dev_fetch_dstats()` in `net/core/dev.c`: `static`; drivers reach it only
  through `dev_get_stats()` when `dev->pcpu_stat_type` is
  `NETDEV_PCPU_STAT_DSTATS` and the driver sets neither `ndo_get_stats64` nor
  `ndo_get_stats`.

## Reporting statistics

**Statistics interfaces**

- Rows that differ from the usual picture:

| Counters | Fed by | Read through |
|---|---|---|
| Per-queue | `struct netdev_stat_ops` in `dev->stat_ops` | `NETDEV_CMD_QSTATS_GET`, dump only |
| PHY device group, string "phydev" in `stats_std_names` | `get_phy_stats` in `struct phy_driver`; no `struct ethtool_ops` callback | `ETHTOOL_MSG_STATS_GET`, group `ETHTOOL_STATS_PHY` |
| Link down events | `link_down_events` in `struct phy_device`, then `get_link_stats` in `struct phy_driver`, then `get_link_ext_stats` in `struct ethtool_ops` | `ETHTOOL_MSG_LINKSTATE_GET` |
| Timestamping | `get_ts_stats` | `ETHTOOL_MSG_TSINFO_GET` |
| MAC merge | `get_mm_stats` | `ETHTOOL_MSG_MM_GET` |
| Page pool | none; the core reads the pool | `NETDEV_CMD_PAGE_POOL_STATS_GET`, only with `CONFIG_PAGE_POOL_STATS` |

- `ETHTOOL_MSG_STATS_GET` carries five groups only: eth-phy, eth-mac,
  eth-ctrl, rmon, phydev; see `stats_prepare_data()` in
  `net/ethtool/stats.c`.
- `get_phy_stats` of the PHY driver: is passed both the eth-phy and the
  phydev structs, runs before `get_eth_phy_stats`, and runs only when the
  source is `ETHTOOL_MAC_STATS_SRC_AGGREGATE`.
- `get_link_ext_stats` of the MAC driver: runs after the PHY path, so a value
  it writes replaces what `__phy_ethtool_get_link_ext_stats()` stored.
- `get_pause_stats`: never called if the driver lacks `get_pauseparam`;
  `pause_prepare_data()` returns `-EOPNOTSUPP` first.
- `get_fec_stats`: called only after `get_fecparam` exists and returned 0;
  see `fec_prepare_data()`.
- `get_mm_stats`: called only after `get_mm` exists and returned 0; see
  `mm_prepare_data()`.
- `page_pool_ethtool_stats_get_count()`,
  `page_pool_ethtool_stats_get_strings()`, `page_pool_ethtool_stats_get()`
  and `page_pool_get_stats()`: marked deprecated in
  `include/net/page_pool/helpers.h` and `net/core/page_pool.c`.
- `page_pool_get_stats()`: adds into the caller's struct; the caller zeroes
  it first.
- Page pool netlink visibility: only a pool created with a netdev
  (`pool->slow.netdev`) is linked by `page_pool_list()`; any other pool gets
  `-ENOENT` in `netdev_nl_page_pool_get_do()` and is skipped by dumps.

**Core-allocated per-CPU statistics**

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

**Per-queue statistics**

- Queue-count change: drivers are encouraged to reset the per-queue counters
  (comment on `struct netdev_stat_ops` in `include/net/netdev_queues.h`).
- Device-scope totals: count events since the last explicit reset of the
  device; a reconfiguration such as a change of queue count is not a reset
  (`Documentation/netlink/specs/netdev.yaml`).
- Two in-tree patterns satisfy this: `bnxt_get_base_stats()` returns totals
  saved from torn-down rings; `virtnet_get_base_stats()` keeps per-queue
  counters and sums the inactive queues with `netdev_stat_queue_sum()`.
- `get_base_stats()` also selects the device-scope fields: a field it leaves
  unset is not reported even if every queue sets it; see
  `netdev_nl_stats_add()` in `net/core/netdev-genl.c`.
- `get_base_stats()` writing 0: valid, and needed to get a field reported
  when there is no history.
- No `get_base_stats()`: `netdev_nl_stats_by_netdev()` reports nothing for
  the device; device scope is the default scope of the dump.
- A per-queue field left unset by one queue: skipped in the device sum, the
  field is still reported.
- Device scope on a down device: `get_base_stats()` and the per-queue
  callbacks still run for every index below `real_num_rx_queues` and
  `real_num_tx_queues`; `bnxt_get_queue_stats_rx()` guards for this.
- `netdev_stat_queue_sum()` called by a driver: can pass the per-queue
  callbacks an index at or above the real queue count.

**Unsupported counter fields**

- `src` in `struct ethtool_eth_phy_stats`, `struct ethtool_eth_mac_stats`,
  `struct ethtool_eth_ctrl_stats`, `struct ethtool_rmon_stats` and
  `struct ethtool_pause_stats`: an input the core sets after the fill, not a
  counter; it names the MAC to report.
- Per-queue sentinel: `NETDEV_STAT_NOT_SET`, private to
  `net/core/netdev-genl.c`; same value as `ETHTOOL_STAT_NOT_SET`.
- `stats_prepare_data()` in `net/ethtool/stats.c`: fills its five structs
  with `memset()` of 0xff, not `ethtool_stats_init()`; the result is the
  same.
- Per-queue callback that sets no field at all: the core drops the whole
  entry for that queue; see `netdev_nl_stats_queue()`.

**Driver-private ethtool statistics**

- Barred by `Documentation/networking/statistics.rst`: only statistics with a
  matching member in `struct rtnl_link_stats64`; they go "exclusively" through
  `ndo_get_stats64`, and reporting them through ethtool or debugfs "will not
  be accepted".
- Queue statistics, the standard ethtool groups and page pool statistics: the
  notes for driver authors do not bar them from `get_ethtool_stats`.
- Counters reported before a standard interface existed: the document has no
  rule to keep, duplicate or remove them; it only remarks that the ioctl was
  historically used for per-queue and standards-based statistics.
- Number of statistics: drivers "are advised" to keep it constant; this is
  advice, not a requirement.
- Reason given: retrieval takes several system calls, so a changing count
  races with user space. No other reason is given.
- Count mismatch in the kernel: `ethtool_get_stats()` in
  `net/ethtool/ioctl.c` calls `get_sset_count` itself; if user space passed a
  different non-zero `n_stats`, it returns `n_stats` 0 and no values.
- `get_ethtool_stats` kerneldoc in `include/linux/ethtool.h`: "only useful if
  the device maintains statistics not included in" `struct
  rtnl_link_stats64`.

**The stats member of net_device**

- `DEV_CORE_STATS_INC()`: not callable; it generates four inline helpers and
  is `#undef`-ed right after in `include/linux/netdevice.h`.
- The helpers are `dev_core_stats_rx_dropped_inc()`,
  `dev_core_stats_tx_dropped_inc()`, `dev_core_stats_rx_nohandler_inc()` and
  `dev_core_stats_rx_otherhost_dropped_inc()`.
- Driver use of the helpers: present in the tree for the driver's own drops,
  for example `dev_core_stats_tx_dropped_inc()` in
  `drivers/net/ethernet/broadcom/bnxt/bnxt.c`; `netdev_core_stats_inc()` is
  exported.
- `dev->core_stats` itself: the kerneldoc of `struct net_device` says not to
  use the field in drivers; go through the helpers.
- **Potentially unsafe usage**: counting a drop in the driver's own
  `rx_dropped` or `tx_dropped`.
  - Unsafe: when the same drop is also counted in `dev->core_stats`, by the
    core or by a helper call; `dev_get_stats()` adds `dev->core_stats` to
    whatever the driver reports, so the drop shows twice.
  - Safe: when the drop is counted in one place only, as `vrf_xmit()` does
    for a transmit drop with `dev_dstats_tx_dropped()` on a
    `NETDEV_PCPU_STAT_DSTATS` device and no `dev->core_stats` helper call;
    `__dev_queue_xmit()` counts no drop when the transmit routine has
    consumed the skb.

## State bits, atomics and trylock

**Flags and atomics as locks**

- `__LINK_STATE_START` writers: `__dev_open()` and `__dev_close_many()` in
  `net/core/dev.c` both call `ASSERT_RTNL()` unconditionally.
- `init_dummy_netdev()`: also sets `__LINK_STATE_START`, with no open call.
- `__dev_close_many()`: has no `synchronize_net()` of its own; it does
  `clear_bit()`, `smp_mb__after_atomic()`, then `dev_deactivate_many()`.
- `dev_deactivate_many()` in `net/sched/sch_generic.c`: calls
  `synchronize_net()` only if `dev_deactivate_queue()` found a qdisc with an
  `enqueue` op, then sleeps until `some_qdisc_is_busy()` is false.
- Before `ndo_stop`, the close path waits for netpoll (`netpoll_poll_disable()`
  takes `dev_lock`) and for the qdisc layer; it has no unconditional wait for
  a driver path that read `netif_running()` as true.
- **Potentially unsafe usage**: testing `netif_running()` without RTNL, then
  using what `ndo_stop` frees.
  - Unsafe: in a work item, timer or IRQ handler that `ndo_stop` has not
    stopped; the bit can clear and `ndo_stop` can run between test and use.
  - Safe: test and use under `rtnl_lock()`, as `bnx2_reset_task()` in
    `drivers/net/ethernet/broadcom/bnx2.c` does; both writers assert RTNL.
- `napi_schedule_prep()`: takes `NAPIF_STATE_SCHED` with a `try_cmpxchg()`
  loop; `napi_watchdog()` uses `test_and_set_bit()` and `__napi_busy_loop()`
  uses `cmpxchg()`, and neither sets `NAPIF_STATE_MISSED`.
- `napi_disable_locked()`: clears `NAPI_STATE_DISABLE` before it returns; the
  disabled state is `NAPIF_STATE_SCHED | NAPIF_STATE_NPSVC` left set.
- `netif_napi_add_weight_locked()`: sets `NAPI_STATE_SCHED` and
  `NAPI_STATE_NPSVC`, so a new NAPI starts in the disabled state.
- `napi_schedule_prep()` on a disabled NAPI: returns false and sets
  `NAPIF_STATE_MISSED`; the event is dropped, nothing is queued.
- `napi_enable_locked()` on a NAPI whose SCHED bit is clear: `BUG_ON()`.
- `__napi_poll()`: when the driver used its whole budget and
  `napi_disable_pending()`, it calls `napi_complete()` itself, so a poll that
  always uses its whole budget cannot starve `napi_disable_locked()`.
- `->poll()` is not called only by the SCHED owner: `poll_one_napi()` in
  `net/core/netpoll.c` calls `napi->poll(napi, 0)` after
  `test_and_set_bit(NAPI_STATE_NPSVC)`, without SCHED.
- `poll_owner` in `struct napi_struct` is what keeps netpoll and the other
  pollers apart: `poll_napi()` takes it by `cmpxchg()`; `napi_poll()`,
  `napi_threaded_poll_loop()` and `__napi_busy_loop()` take it with
  `netpoll_poll_lock()`.
- `netpoll_poll_lock()` in `include/linux/netpoll.h`: takes `poll_owner` only
  when `dev->npinfo` is set; returns `NULL` without `CONFIG_NETPOLL`.

**Trylock patterns**

- `net/core/net-sysfs.c`: has no `rtnl_trylock()`; its handlers that need
  RTNL call static `sysfs_rtnl_lock()`, which uses
  `sysfs_break_active_protection()` and `rtnl_lock_interruptible()`, and
  returns `-ERESTARTSYS` or `-ENODEV`.
- Sysfs handlers outside that file use `rtnl_trylock()` with
  `restart_syscall()`, for example `store_bridge_parm()` in
  `net/bridge/br_sysfs_br.c` and `bond_opt_tryset_rtnl()` in
  `drivers/net/bonding/bond_options.c`.
- `linkwatch_event()` in `net/core/link_watch.c`: calls `rtnl_lock()`, not
  `rtnl_trylock()`.
- `HARD_TX_TRYLOCK()`: defined in `include/linux/netdevice.h`; its one user is
  `__netpoll_send_skb()` in `net/core/netpoll.c`.
- `HARD_TX_TRYLOCK()` with `dev->lltx` set: evaluates to
  `__netif_tx_acquire()`, which is true and takes no lock.
- `netpoll_poll_dev()`: uses `down_trylock()` on `dev_lock` in
  `struct netpoll_info`, not the xmit lock; 0 means taken.
- `net/core/dev.c`: has no trylock on the xmit lock; search
  `__netif_tx_trylock` for its users.
- **Potentially unsafe usage**: `rtnl_lock()` in a work item.
  - Unsafe: when the work is cancelled or flushed synchronously by a path
    that holds RTNL; the canceller waits for the work, the work for RTNL.
  - Safe: `rtnl_trylock()` and requeue, as
    `udp_tunnel_nic_device_sync_work()` in `net/ipv4/udp_tunnel_nic.c` does;
    `udp_tunnel_nic_unregister()` calls `cancel_delayed_work_sync()` from
    the `NETDEV_UNREGISTER` notifier.
  - Safe: when every synchronous cancel runs outside RTNL, as for
    `bnx2_reset_task()` in `drivers/net/ethernet/broadcom/bnx2.c`:
    `bnx2_remove_one()` cancels it after `unregister_netdev()` has returned,
    and `bnx2_suspend()` cancels it without RTNL.
- **Potentially unsafe usage**: looping on a failed trylock.
  - Unsafe: when the loop has no bound and no other exit, and the holder can
    be waiting for the caller.
  - Safe: a bounded number of tries, then a fallback, as
    `__netpoll_send_skb()` does: it queues the skb on `txq` in
    `struct netpoll_info` and schedules `tx_work`.
  - Safe: `while (!rtnl_trylock())` whose body requeues and returns on the
    first failure, as in `bnxt_fw_reset_task()` in
    `drivers/net/ethernet/broadcom/bnxt/bnxt.c`.
  - Safe: a loop that returns once it sees clear a bit the holder clears
    before it waits, as `mlx5e_tx_reporter_timeout_recover()` tests
    `MLX5E_STATE_CHANNELS_ACTIVE` after each failed `netdev_trylock()`;
    `mlx5e_deactivate_priv_channels()` clears the bit before
    `cancel_work_sync()`.
- **Potentially unsafe usage**: returning on a failed trylock without
  requeueing.
  - Unsafe: when nothing records the skipped event and no other path does
    the same work.
  - Safe: the request flag stays set until the work runs, as
    `FM10K_FLAG_SWPRI_CONFIG` in `fm10k_watchdog_update_host_state()`; only
    `fm10k_configure_swpri_map()` clears it.
  - Safe: the work is opportunistic and another path does it under the
    blocking lock, as `virtnet_poll_cleantx()` in `drivers/net/virtio_net.c`;
    `virtnet_poll_tx()` runs `free_old_xmit()` under `__netif_tx_lock()`.
- `qdisc_run_begin()` in `include/net/sch_generic.h`, for a `TCQ_F_NOLOCK`
  qdisc: after the failed `spin_trylock()` it sets `__QDISC_STATE_MISSED`
  with `test_and_set_bit()` and, if the bit was clear, tries
  `spin_trylock()` a second time.
- `qdisc_run_end()`, for a `TCQ_F_NOLOCK` qdisc: has `smp_mb()` between
  `spin_unlock()` and the `test_bit()` of `__QDISC_STATE_MISSED`; without
  both steps the mark can be set after the holder's last look.
- Lockdep, `validate_chain()` in `kernel/locking/lockdep.c`: skips the
  dependency checks for the trylock acquisition itself.
- Lockdep, `check_prevs_add()`: a lock held through a trylock still gets a
  dependency recorded to a lock taken blocking right after it; a later
  blocking lock is linked through the one before it.

## Model gaps

### Other mistakes models make

- Models take `rtnl_lock` to be the only lock in the reset-work against close
  deadlock. `bnxt_lock_sp()` in `drivers/net/ethernet/broadcom/bnxt/bnxt.c`
  takes only `netdev_lock()` and clears `BNXT_STATE_IN_SP_TASK` before it
  takes the lock.
- Models take netdevice notifiers to run under `rtnl_lock` alone.
  `register_netdevice()` raises `NETDEV_REGISTER` under `netdev_lock_ops()`,
  `unregister_netdevice_many_notify()` raises `NETDEV_UNREGISTER` after
  `netdev_unlock_ops()`; the events with a stated rule are listed under
  "Notifiers and netdev instance lock" in
  `Documentation/networking/netdevices.rst`.
- Models take `dev_open()` and the other `dev_*()` wrappers in
  `net/core/dev_api.c` to be safe in any notifier handler. `dev_open()` and
  `dev_close()`, for example, call `netdev_lock_ops()`, so on an ops-locked
  device a handler for an event raised under the instance lock, such as
  `NETDEV_REGISTER`, that calls one on the device of the event takes
  `dev->lock` twice.
- Models take `xdp_set_features_flag()` to need no lock. It takes
  `netdev_lock()` itself; a caller that holds the instance lock uses
  `xdp_set_features_flag_locked()` in `net/core/xdp.c`, which also raises
  `NETDEV_XDP_FEAT_CHANGE` under that lock.
- Models take the body of a `u64_stats_fetch_begin()` loop to be forbidden
  to sleep. Usage note 5 in `include/linux/u64_stats_sync.h` allows readers
  to sleep or be preempted.
