- `dev_dax->target_node < 0`: `dev_dax_kmem_probe()` returns `-EINVAL`; there
  is no fallback node.
- Range trimming: `dax_kmem_range()` uses `memory_block_aligned_range()` from
  `include/linux/memory.h`.
- Two passes, not one per range: `dax_kmem_init_resources()` reserves every
  range with `request_mem_region()` first, then `dax_kmem_do_hotplug()` adds
  every range whose `data->res[i]` is set.
- Add call: `__add_memory_driver_managed()`, which takes the online type as
  an argument; `dax_kmem_do_hotplug()` does not call
  `add_memory_driver_managed()`.
- Online type at probe: `dev_dax_kmem_probe()` reads
  `mhp_get_default_online_type()` and passes it down;
  `__add_memory_resource()` onlines the blocks when it is not `MMOP_OFFLINE`.
- `data->state`: set to that online type after probe, `DAX_KMEM_UNPLUGGED`
  before; see `struct dax_kmem_data`.
- `state` attribute of the dax device: `state_store()` lets user space pick
  the online type per device; it accepts "unplugged", "online",
  "online_kernel" and "online_movable".
- `state` write of "offline": `dax_kmem_parse_state()` rejects it with
  `-EINVAL`.
- `state` write of an online type: allowed only from `DAX_KMEM_UNPLUGGED`,
  else `-EBUSY`, unless it is the state already held, which succeeds; a
  device probed with `MMOP_OFFLINE` must be written "unplugged" first.
- `state` write of "unplugged": `dax_kmem_do_hotremove()` offlines and removes
  every added range with `offline_and_remove_memory_ranges()`; on failure
  nothing is removed and the state is unchanged.
- `dax_kmem_do_hotremove()` without `CONFIG_MEMORY_HOTREMOVE`: returns
  `-EBUSY`.
- `dev_dax_kmem_remove()`: never offlines; with `CONFIG_MEMORY_HOTREMOVE`,
  `dax_kmem_remove_ranges()` calls only `remove_memory()`, which returns
  `-EBUSY` for a range with an online block; without it
  `dev_dax_kmem_remove()` removes nothing.
- `dev_dax_kmem_remove()` does not read `data->state`; memory block `state`
  files can change blocks without updating it.
- Mixed result in `dax_kmem_remove_ranges()`: ranges that are offline are
  removed and their `data->res[i]` freed, even when another range is online
  and the rest of the driver data is then leaked.
