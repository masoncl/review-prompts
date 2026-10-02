- `struct swap_info_struct` is defined in `include/linux/swap.h`;
  `struct swap_cluster_info` in `mm/swap.h`.
- There is no swap_map array, no zeromap bitmap, no cont_lock and no
  SWP_FS_OPS flag in this tree, and no swap count continuation pages.
- Per-slot state: one `atomic_long_t` in the cluster's `table`; the entry kinds
  are in the comment at the top of `mm/swap_table.h`.
- `ci->memcg_table`: per-slot memcg id under `CONFIG_MEMCG`, written by
  `__swap_cgroup_set()`.
- `ci->flags == CLUSTER_FLAG_NONE`: the cluster is on no list, as left by
  `isolate_lock_cluster()`.
- `si->ops`: see "Swap device operations".
- `si->avail_list` on `swap_avail_head`: one plist, not one per node.
- `si->inuse_pages`: atomic; the page count in it changes under `ci->lock`; it
  carries `SWAP_USAGE_OFFLIST_BIT`, so read it with `swap_usage_in_pages()`.
- `SWP_HIBERNATION` in `si->flags`: swapoff returns `-EBUSY` while it is set.

| Lock | Protects |
|---|---|
| `swapon_mutex` | `si->swap_file` as `swap_start()` walks it |
| `swap_lock` | `swap_info[]`, `nr_swapfiles`, `swap_active_head`, `total_swap_pages`, `SWP_USED`, `SWP_WRITEOK`, `SWP_HIBERNATION` |
| `percpu_swap_cluster.lock` | this CPU's `si[]` and `offset[]` |
| `si->global_cluster_lock` | `si->global_cluster`; taken only without `SWP_SOLIDSTATE` |
| `ci->lock` | `count`, `flags`, `order`, `extend_table`, `memcg_table`, `zero_bitmap`, writes to table entries |
| `si->lock` | the cluster lists and `ci->list`; `SWP_WRITEOK` together with `swap_lock` |
| `swap_avail_lock` | `swap_avail_head`, `SWAP_USAGE_OFFLIST_BIT` |

- Allocator order: `percpu_swap_cluster.lock` -> `si->global_cluster_lock` ->
  `ci->lock` -> `si->lock`.
- `ci->lock` is outside `si->lock`: `move_cluster()` takes `si->lock` with
  `ci->lock` held.
- `isolate_lock_cluster()`: holds `si->lock`, so it only `spin_trylock()`s
  `ci->lock` and skips a contended cluster.
- `swap_avail_lock`: innermost; taken under `ci->lock` by `swap_usage_add()`
  and `swap_usage_sub()`, and under `si->lock` at swapon and swapoff.
- `swap_alloc_slow()`: takes `swap_avail_lock` under the local lock and drops
  it before it touches a device.
- Folio lock is outside `ci->lock`; `swap_cluster_get_and_lock()` asserts it.
