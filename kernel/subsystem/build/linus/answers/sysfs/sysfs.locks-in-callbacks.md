- **Unsafe usage**: a show or store, while it holds its active reference,
  blocks on a lock that some path holds while it removes that attribute, its
  group, its directory or its device. `kernfs_drain()` waits with a plain
  `wait_event()`, no timeout.
  - Safe: trylock, and `restart_syscall()` on failure, as
    `lock_device_hotplug_sysfs()` in `drivers/base/core.c` and
    `bond_opt_tryset_rtnl()` in `drivers/net/bonding/bond_options.c` (called
    from `bonding_sysfs_store_option()`).
  - Safe: drop the active reference before blocking, as `sysfs_rtnl_lock()` in
    `net/core/net-sysfs.c`: `dev_hold()`, `sysfs_break_active_protection()`,
    `rtnl_lock_interruptible()`, `dev_isalive()` check, then unbreak.
- `ignore_lockdep` (a field of `struct attribute` only under
  `CONFIG_DEBUG_LOCK_ALLOC`): only makes `sysfs_add_file_mode_ns()` and
  `sysfs_add_bin_file_mode_ns()` pass a NULL key, so the node lacks
  `KERNFS_LOCKDEP`; `kernfs_drain()` still waits, so a real cycle still hangs.
- Purpose of `ignore_lockdep`: every node built from one `struct attribute`
  shares one lock class, so a store that removes another object's node of the
  same attribute looks recursive to lockdep.
- Macros that set it: `__ATTR_IGNORE_LOCKDEP()`, `DEVICE_ATTR_IGNORE_LOCKDEP()`,
  `__DEVICE_ATTR_IGNORE_LOCKDEP()`, and a file-local
  `DRIVER_ATTR_IGNORE_LOCKDEP()` defined in `drivers/base/bus.c` and again in
  `drivers/dma/idxd/compat.c`.
- Users: search `IGNORE_LOCKDEP`; for example `unbind` and `bind` in
  `drivers/base/bus.c`, `remove` in `drivers/usb/core/sysfs.c`.
- `drivers/pci/pci-sysfs.c`: only `remove` uses it, together with
  `device_remove_file_self()`; `dev_attr_dev_rescan` is a plain `__ATTR()`.
- `sysfs_attr_init()`: needed for a dynamically allocated attribute; without
  it the key falls back to `&attr->skey` in non-static memory, and
  `lockdep_init_map_type()` prints "BUG: key ... has not been registered!" and
  turns lockdep off.
