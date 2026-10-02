- `pack_shadow()` takes a `file` argument; a file shadow keeps
  `BITS_PER_LONG - EVICTION_SHIFT` counter bits, an anon shadow
  `SWAP_COUNT_SHIFT` fewer (`EVICTION_SHIFT_ANON`, `EVICTION_MASK_ANON`).
- Reason for the anon limit: the swap table entry keeps the swap count and,
  when `SWAP_TABLE_HAS_ZEROFLAG`, the zero flag in its top
  `SWP_TB_FLAGS_BITS`; `shadow_to_swp_tb()` in `mm/swap_table.h` has a
  `VM_WARN_ON_ONCE()` for a shadow with bits there.
- `bucket_order` is an array indexed by `WORKINGSET_ANON` and
  `WORKINGSET_FILE`; `workingset_init()` sets each from its own bit count.
- A new field in the shadow must be added to `EVICTION_SHIFT`; the
  `BUILD_BUG_ON()` in `lru_gen_eviction()` checks that `LRU_GEN_WIDTH` plus
  `LRU_REFS_WIDTH` still fit in the bits left by the larger of the two
  shifts.
- Memcg id packed: `mem_cgroup_private_id()`, looked up again with
  `mem_cgroup_from_private_id()`.
- `lru_gen_eviction()` token: `min_seq` shifted by `LRU_REFS_WIDTH`, or-ed
  with `max(refs - 1, 0)`; it is not shifted by `bucket_order` and does not
  call `workingset_age_nonresident()`.
- Swapped-out folio: the shadow is in the per-cluster swap table
  (`table` in `struct swap_cluster_info`), one entry per slot; read with
  `swap_cache_get_shadow()`.
- `shadow_nodes` list and its shrinker: cover page-cache xarray nodes only;
  swap table shadows are not on it.
