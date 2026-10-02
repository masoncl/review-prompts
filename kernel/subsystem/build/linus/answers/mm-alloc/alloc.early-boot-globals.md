- `free_area_init()`: static in `mm/mm_init.c`, takes no arguments, called
  only from `mm_core_init_early()`, which `start_kernel()` calls
  immediately after `setup_arch()`.
- Arch code does not call `free_area_init()`; it supplies zone limits
  through `arch_zone_limits_init()`.
- Everything in `setup_arch()` runs before the zone fields and
  `arch_zone_lowest_possible_pfn[]` are set.
- `parse_early_param()`: the call in `start_kernel()` comes after
  `mm_core_init_early()`; it runs the handlers only once, so it does nothing
  when `setup_arch()` already called it, as for example
  `arch/x86/kernel/setup.c` does.
- `high_memory`: `set_high_memory()`, last step of `free_area_init()`, sets
  it only when it is still NULL.
- `high_memory` on arches that assign it in `setup_arch()` is valid from
  that assignment, for example `initmem_init()` in
  `arch/x86/mm/init_32.c`; search `arch/` for `high_memory =`.
- `node_states` in `mm/page_alloc.c` has a static initialiser:
  `N_POSSIBLE` all nodes, `N_ONLINE` node 0; without `CONFIG_NUMA` also
  node 0 in `N_NORMAL_MEMORY`, `N_HIGH_MEMORY`, `N_MEMORY` and `N_CPU`.
- With `MAX_NUMNODES == 1`: `node_state()` returns `node == 0` and
  `node_set_state()` is empty (`include/linux/nodemask.h`); the masks are
  "not yet valid" only on NUMA builds.
- `N_MEMORY`: the lasting setter at boot is the `for_each_node()` loop in
  `free_area_init()`, for nodes with `node_present_pages`.
- `early_calculate_totalpages()` also sets `N_MEMORY`, but
  `find_zone_movable_pfns_for_nodes()` restores the saved mask before it
  returns.
- `N_CPU`: not set by `free_area_init()`; `init_cpu_node_state()` and
  `vmstat_cpu_online()` in `mm/vmstat.c` set it, under `CONFIG_SMP`.
- `memblock_end_of_DRAM()`: returns an exclusive end and reads
  `memblock.memory.regions[cnt - 1]`; call it only after the arch has added
  memory.
