- Static `dev_dax->pgmap`: a `kmemdup()` copy made in
  `__devm_create_dev_dax()`, owned by the `struct dev_dax` and freed in
  `dev_dax_release()`; the caller's `data->pgmap` is not kept (in
  `drivers/dax/pmem.c` it is a stack variable).
- Static `dev_dax->pgmap` across bindings: the same copy is handed to every
  driver that binds, so whatever one driver writes into it is seen by the
  next; `fsdev_acquire_pgmap()` resets `vmemmap_shift` and
  `fsdev_clear_pgmap_ops()` clears `ops` and `owner` on unbind.
- Dynamic `dev_dax->pgmap`: `devm_kzalloc()`ed by the driver that binds, in
  `dev_dax_probe()` or `fsdev_acquire_pgmap()`, and freed by devres on unbind.
- **Unsafe usage**: leaving `dev_dax->pgmap` pointing at a `devm_kzalloc()`ed
  pagemap of a dynamic device after probe has failed or the driver has
  unbound.
  - Unsafe: `dev_dax_probe()` and `fsdev_acquire_pgmap()` return `-EINVAL`
    for a dynamic device whose `pgmap` is not NULL, so the device cannot be
    bound again.
  - Safe: `fsdev_dax_probe()` assigns `dev_dax->pgmap` after its last step
    that can fail, and registers `fsdev_kill()` so that `kill_dev_dax()`
    clears it on unbind.
- `dev_dax->ranges[0]` at creation: `__devm_create_dev_dax()` calls
  `alloc_dev_dax_range()` with `data->size` for static and dynamic devices
  alike; a `data->size` of 0 makes no range.
- Lock helpers: there are no dax_region_lock or dax_dev_lock guard helpers;
  callers use `down_write_killable()`, `down_read_interruptible()` and
  `down_write()` directly on `dax_region_rwsem` and `dax_dev_rwsem`.
- `dax_bus_lock`: a mutex, guards only the per-driver `ids` list used by
  `do_id_store()` and `dax_match_id()`.
- `dax_region_rwsem` held for write: asserted by `alloc_dev_dax_range()`,
  `trim_dev_dax_range()`, `adjust_dev_dax_range()` and
  `devm_register_dax_mapping()`, so it is the lock for `dev_dax->ranges`,
  `dev_dax->nr_range` and the children of `dax_region->res`.
- `dax_dev_rwsem`: asserted by `dev_dax_size()` and, for write, by
  `__free_dev_dax_id()`; also taken for write to change `dev_dax->align` and
  `dev_dax->memmap_on_memory`.
- Ranges changed under `dax_region_rwsem` alone: `__devm_create_dev_dax()`
  before `device_add()`, and `unregister_dev_dax()` after `device_del()`;
  `size_store()` and `mapping_store()`, on a registered device, hold both.
- `get_dax_range()`: takes `dax_region_rwsem` for write, so the mapping
  `start`, `end` and `page_offset` show functions hold the write lock.
- `delete_store()`: takes `device_lock()` on the region device, then on the
  victim, then `dax_dev_rwsem` for write, and not `dax_region_rwsem`;
  `unregister_dev_dax()` takes that later, after `dax_dev_rwsem` and the
  victim's device lock are dropped.
- `unregister_dev_dax()`: holds `dax_region_rwsem` for write across
  `device_del()`, so the bound driver's `remove` and devm actions run with it
  held.
- `dax_bus_probe()`: takes `dax_dev_rwsem` for read under the device lock of
  the `struct dev_dax`.
