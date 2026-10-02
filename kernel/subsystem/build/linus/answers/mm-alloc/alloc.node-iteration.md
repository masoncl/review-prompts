- There is no for_each_possible_node() here; `for_each_node()` iterates
  `N_POSSIBLE`.
- SLUB: `kmem_cache_init()` fills `slab_nodes` with
  `for_each_node_state(node, N_MEMORY)`, not `N_NORMAL_MEMORY`.
- Array indexed by any nid: iterate `for_each_node()` and choose the
  allocation node separately, as `hugetlb_cgroup_css_alloc()` does with
  `node_state(node, N_NORMAL_MEMORY) ? node : NUMA_NO_NODE`.
- Raw loop to `nr_node_ids`: can visit ids that are not possible, so each
  entry needs a test; `for_each_kmem_cache_node()` in `mm/slub.c` tests the
  pointer.
- `struct kmem_cache`: `per_node[]` is declared with `MAX_NUMNODES` entries
  but `kmem_cache_init()` sizes the cache for `nr_node_ids` entries, so
  indexing up to `MAX_NUMNODES` overruns the object.
- With `MAX_NUMNODES == 1`: `nr_node_ids` and `nr_online_nodes` are the
  macros `1U`, and `node_state()` is `node == 0`.
- `nr_node_ids`: `MAX_NUMNODES` until `setup_nr_node_ids()` runs, from
  `free_area_init()` or earlier from architecture NUMA setup, for example
  `setup_node_to_cpumask_map()` in `mm/arch_numa.c`.
- `N_POSSIBLE`: narrowed by architecture code during `setup_arch()`, for
  example `numa_register_meminfo()` in `mm/numa_memblks.c`.
- `N_MEMORY` and `N_NORMAL_MEMORY`: first set in `free_area_init()`, called
  from `mm_core_init_early()` right after `setup_arch()`.
- `N_CPU`: first set in `init_cpu_node_state()`, called from
  `init_mm_internals()`, long after the allocators are up.
- Before `free_area_init()`, with `CONFIG_NUMA`: `NODE_DATA()` of a node the
  architecture did not set up is NULL.
- Hotplug tracking: `register_node_notifier()` in `drivers/base/node.c` and
  the `hotplug_node_notifier()` macro in `include/linux/node.h`; both are
  stubs returning 0 unless `CONFIG_MEMORY_HOTPLUG` and `CONFIG_NUMA` are set.
