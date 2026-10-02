| Job | File in this tree | Not where expected |
|---|---|---|
| LRU batching, activation, `lru_add_drain()`, `release_pages()` | `mm/folio.c` | There is no mm/swap.c. |
| Multi-generation LRU | `mm/vmscan.c` | `lru_gen_eviction()` and `lru_gen_refault()` are in `mm/workingset.c`; `lru_gen_inc_refs()` and `lru_gen_clear_refs()` are in `mm/folio.c`. |
| Shrinkers | `mm/shrinker.c` | `shrink_slab()` is defined here; `mm/vmscan.c` calls it and, of the slab code, defines only `drop_slab()` and `drop_slab_node()`. |
| Swap slot allocator | `mm/swapfile.c` | No mm/swap_slots.c, no include/linux/swap_slots.h. `struct swap_info_struct` has no swap_map member; the per-slot count is in the swap table entry, see `__swp_tb_get_count()` in `mm/swap_table.h`. |
| Swap cache | `mm/swap_state.c` | One `swap_space` for all devices. |
| Swap table (stores the swap cache) | `mm/swap_table.h` | Header only, no mm/swap_table.c. One table per cluster: `table` in `struct swap_cluster_info`, `mm/swap.h`. Allocated and freed by `swap_cluster_alloc_table()` and `swap_cluster_free_table()` in `mm/swapfile.c`. |
| Swap I/O | `mm/page_io.c` | Back ends are `struct swap_ops` in `include/linux/swap_ops.h`: `swap_bdev_ops` is the default on every device; a filesystem installs its own with `swap_fs_activate()`. There is no swap_rw address-space operation. |
| zswap | `mm/zswap.c` | Calls `zs_malloc()` in `mm/zsmalloc.c` directly; no zpool layer exists, neither mm/zpool.c nor include/linux/zpool.h. |
| Memory cgroup charge code | `mm/memcontrol.c` | cgroup v1 code is in `mm/memcontrol-v1.c` under `CONFIG_MEMCG_V1`. |
| Memory cgroup owner of a swap slot | `mm/swap_table.h` | No mm/swap_cgroup.c, no include/linux/swap_cgroup.h. The id is in `struct swap_memcg_table`, written by `__swap_cgroup_set()` from `__mem_cgroup_try_charge_swap()` in `mm/memcontrol.c`. |
