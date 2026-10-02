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
