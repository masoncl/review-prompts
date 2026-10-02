- `do_pages_move()`: returns `-ENODEV` both for
  `node < 0 || node >= MAX_NUMNODES` and for `!node_state(node, N_MEMORY)`;
  it returns `-EINVAL` for neither and does not call `node_online()`.
- `do_pages_move()` cpuset test: `-EACCES` when the node is not in
  `cpuset_mems_allowed()` of the target task, which `find_mm_struct()`
  fetched; it is not `current->mems_allowed`.
- `node_state()`, `node_online()`, `node_possible()`: `test_bit()` on
  `node_states[]` with no bounds check, so the range test must come first.
- `numa_valid_node()` in `include/linux/numa.h`: the range test
  `nid >= 0 && nid < MAX_NUMNODES`; it rejects `NUMA_NO_NODE`.
- `MAX_NUMNODES` bounds `node_data[]` and `node_states[]`; an array allocated
  with `nr_node_ids` entries needs `nid < nr_node_ids`, as `compact_store()`
  in `mm/compaction.c` tests before `node_online()`.
- `numa_node_store()` in `drivers/pci/pci-sysfs.c`: accepts `NUMA_NO_NODE`,
  otherwise requires range and `node_online()`.
- Possible but offline node: `NODE_DATA()` is non-NULL on every architecture
  once `free_area_init()` in `mm/mm_init.c` has run; it calls
  `alloc_offline_node_data()` for each possible node whose entry is NULL.
- Possible but offline node, zonelists: `__build_all_zonelists()` builds them
  for every possible node; `ZONELIST_FALLBACK` holds the `N_MEMORY` nodes,
  `ZONELIST_NOFALLBACK` is empty.
- Node that is not possible: its `node_data[]` entry can be NULL, and
  `node_zonelist()` makes no NULL test.
- Without `CONFIG_NUMA`: `NODE_DATA()` returns `&contig_page_data` for any
  nid.
- `of_node_to_nid()` in `drivers/of/of_numa.c`: tests only
  `nid < MAX_NUMNODES && node_possible(nid)`, so the result can be offline.
- `numa_map_to_online_node()`: a macro in `include/linux/numa.h` for
  `numa_nearest_node(node, N_ONLINE)`; it passes `NUMA_NO_NODE` through, does
  no range check, and without `CONFIG_NUMA` returns `NUMA_NO_NODE` for every
  input.
