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
