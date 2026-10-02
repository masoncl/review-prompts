- `struct folio`: still a union with `struct page` in this tree; `page_folio()`
  is a cast of `_compound_head()` and `folio_page()` is pointer arithmetic.
  No folio is allocated separately from the memmap.
- Kind of memory: recorded in `page_type`, which shares storage with
  `_mapcount` on the head page (`enum pagetype`, `FOLIO_TYPE_OPS()`). Slab,
  page table, hugetlb, zsmalloc and large kmalloc are page types, not flags.
- Overlays of `struct page` other than `struct folio`: for example
  `struct slab`, `struct ptdesc`, `struct netmem_desc` in
  `include/net/netmem.h`, `struct zpdesc` in `mm/zpdesc.h`.
  `struct page_pool` is not an overlay; `struct netmem_desc` points to it.
- `struct obj_cgroup`: what `folio->memcg_data` points to for a charged folio
  (`commit_charge()` in `mm/memcontrol.c`). It is not a `struct mem_cgroup`
  pointer.
- Folio → `struct mem_cgroup`: one more hop, `folio_memcg()` →
  `obj_cgroup_memcg()`, which asserts `rcu_read_lock()` or `cgroup_mutex`.
- Folio → memcg and folio → `struct lruvec` are not fixed for the folio's
  life: `memcg_reparent_objcgs()` points the objcg at the parent memcg and
  `lru_reparent_memcg()` in `mm/folio.c` splices the child's LRU lists into
  the parent's; with `lru_gen_enabled()` it is `lru_gen_reparent_memcg()` in
  `mm/vmscan.c` instead.
- Swap cache slots: one per page, in a per-cluster table hung off
  `struct swap_cluster_info` (`mm/swap.h`); each slot of a large folio holds
  the folio's PFN (`__swap_cache_do_add_folio()`), so there is no multi-index
  entry.
- Large folio ↔ `struct mm_struct`: under `CONFIG_MM_ID` (selected by
  `CONFIG_TRANSPARENT_HUGEPAGE`) a large non-hugetlb folio records up to two
  `mm_id` values with a mapcount each; `folio_maybe_mapped_shared()` reads the
  result.
- `_large_mapcount` of a non-hugetlb folio under `CONFIG_MM_ID`: added to and
  subtracted from with plain read and set under the bit spinlock taken by
  `folio_lock_large_mapcount()` in `include/linux/rmap.h`, not with an atomic
  add. The hugetlb rmap helpers use `atomic_inc()` and `atomic_dec()` without
  that lock.
- `migrate_info`: third user of the slot shared by `private` and `swap`;
  on a migration destination folio it holds a `struct anon_vma` pointer plus
  state bits (`__migrate_folio_record()` in `mm/migrate.c`).
