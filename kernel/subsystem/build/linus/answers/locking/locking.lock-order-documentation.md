- `Documentation/filesystems/locking.rst`: gives the locks held around each
  VFS method; it states no lock order.
- Inode lock order: `Documentation/filesystems/directory-locking.rst` and the
  comment above `enum inode_i_mutex_lock_class` in `include/linux/fs.h`.
- `fs/namespace.c`: has no lock-order block at the top of the file;
  `fs/dcache.c` ("Ordering:") and `fs/inode.c` ("Lock ordering:") do.
- `Documentation/mm/process_addrs.rst`, section "Lock ordering": reproduces
  the comments at the top of `mm/rmap.c` and `mm/filemap.c`.
- Scheduler: two "Lock order:" comments in `kernel/sched/core.c`, one above
  `raw_spin_rq_lock_nested()` and one above `find_proxy_task()` that adds
  `mutex->wait_lock` and `p->blocked_lock`.
- Networking: `Documentation/networking/netdevices.rst` says which of
  `rtnl_lock` and the instance lock is held for each operation.
- Netdev instance lock order: "take after rtnl_lock", and for queue leasing
  the virtual device's lock before the physical device's, are in the comment
  on `lock` in `struct net_device`, `include/linux/netdevice.h`.
- Two netdev instance locks of one lockdep class: `netdev_lock_cmp_fn()` in
  `include/net/netdev_lock.h` allows them together only under `rtnl_lock`;
  it is set only by `netdev_lockdep_set_classes()`, which gives each call
  site its own class.
- `double_rq_lock()`: orders by `rq_order_less()`, which compares CPU numbers
  (the core's CPU first under `CONFIG_SCHED_CORE`), not addresses.
- `double_rq_lock()`, same-object case: it compares `__rq_lockp()` of the two
  runqueues, since two runqueues can share one lock.
- `unix_state_double_lock()` in `net/unix/af_unix.c`: orders by address and
  uses plain lock calls; the annotation is `unix_state_lock_cmp_fn()` set on
  the class, not a subclass at the call site.
