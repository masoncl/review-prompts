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
