- `mfd_of_node_mutex`: a `DEFINE_MUTEX()` in `drivers/mfd/mfd-core.c`; every
  walk, `list_add_tail()` and `list_del()` on `mfd_of_node_list` runs under
  `scoped_guard(mutex, &mfd_of_node_mutex)`.
- Lookup and insert in `mfd_match_of_node_to_dev()`: two separate critical
  sections; the mutex is released between the "already claimed" walk and
  the `list_add_tail()`.
- `mfd_of_node_list`, `mfd_of_node_mutex` and `struct mfd_of_node_entry`:
  defined unconditionally; only the block in `mfd_add_device()` that adds
  entries is gated by `IS_ENABLED(CONFIG_OF)`.
- Entry removal (`fail_of_entry` in `mfd_add_device()`, and
  `mfd_remove_devices_fn()`): frees the entry only and does not call
  `of_node_put()` on `np`.
- `mfd_remove_devices()`: skips children whose `cell->level` is
  `MFD_DEP_LEVEL_HIGH`, so their entries stay until
  `mfd_remove_devices_late()`; `devm_mfd_add_devices()` unwinds with
  `mfd_remove_devices()`.
- `PLATFORM_DEVID_AUTO`: the MFD core keeps no id counter; it passes the
  value to `platform_device_alloc()`, and `platform_devid_ida` lives in
  `drivers/base/platform.c`.
