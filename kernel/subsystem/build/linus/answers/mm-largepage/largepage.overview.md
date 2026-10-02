- Deferred split shrinker: `deferred_split_lru` is drained by a NUMA- and
  memcg-aware shrinker; `thp_shrinker_init()` in `mm/huge_memory.c` allocates
  it with `SHRINKER_NUMA_AWARE | SHRINKER_MEMCG_AWARE`.
- Deferred split sublist: chosen by the folio's node and memcg at queue and
  unqueue time; see `deferred_split_folio()` and
  `__folio_unqueue_deferred_split()`. The folio links in through
  `_deferred_list`, which folios of order 0 and 1 do not have.
- Deferred split membership: not only partially mapped folios.
  `split_underused_thp` is set by default, and while it is set each newly
  PMD-mapped anon folio is queued too; see "Queueing for deferred split".
- `PG_partially_mapped`: the flag that tells the two kinds of queued folio
  apart. `deferred_split_scan()` splits a folio without it only when
  `thp_underused()` says so.
- Tail-page link: the `struct page` field is `compound_info`; `compound_head()`
  is a macro, not a field.
- `compound_info` when `compound_info_has_mask()` is true: holds an address
  mask plus bit 0, not a pointer to the head. Decode it with `compound_head()`
  or `page_folio()`, both built on `_compound_head()`.
- Per-page mapcounts: on by default. `CONFIG_PAGE_MAPCOUNT` is
  `def_bool !NO_PAGE_MAPCOUNT`, and `CONFIG_NO_PAGE_MAPCOUNT` has no default
  and exists only under `CONFIG_TRANSPARENT_HUGEPAGE`.
- `_large_mapcount`: counts every mapping of the folio, one per PTE and one
  per PMD or PUD mapping.
- `_entire_mapcount`: counts only the PMD and PUD mappings and the hugetlb
  mappings, which `_large_mapcount` also includes; see `__folio_add_rmap()` in
  `mm/rmap.c`.
- Rmap helper names: there is no folio_add_rmap_ptes() or folio_add_rmap_pmd().
  The add helpers are split by anon and file, for example
  `folio_add_anon_rmap_ptes()` and `folio_add_file_rmap_pmd()`.
- Hugetlb rmap: `hugetlb_add_file_rmap()` and `hugetlb_remove_rmap()` change
  `_entire_mapcount` and `_large_mapcount` directly and keep no MM-ID state.
  `folio_maybe_mapped_shared()` answers `mapcount > 1` for hugetlb.
- `struct thpsize`: one per order in `THP_ORDERS_ALL_ANON |
  THP_ORDERS_ALL_FILE_DEFAULT`, not anon orders only; see
  `hugepage_init_sysfs()` in `mm/huge_memory.c`.
- Huge zero folio lifetime without `CONFIG_PERSISTENT_HUGE_ZERO_FOLIO`:
  counted by `huge_zero_refcount`, once per mm under `MMF_HUGE_ZERO_FOLIO`,
  not by a folio reference per mapping.
- `CONFIG_PERSISTENT_HUGE_ZERO_FOLIO`: the huge zero folio is allocated once,
  never freed, and `mm_get_huge_zero_folio()` takes no count.
- `struct hstate` lists: `hugepage_freelists[]` is per node;
  `hugepage_activelist` is a single list per hstate. A hugetlb folio links
  into either through `folio->lru`.
- Hugetlb `vm_private_data`, shared VMA: points to `struct hugetlb_vma_lock`,
  or is NULL.
- Hugetlb `vm_private_data`, private VMA: holds the `struct resv_map` pointer
  with `HPAGE_RESV_OWNER` and `HPAGE_RESV_UNMAPPED` in its low bits, or is
  NULL.
- `hugetlb_vma_lock_read()` and its siblings on a private VMA that owns its
  reservation: take `rw_sema` in `struct resv_map`, not a
  `struct hugetlb_vma_lock`.
- Hugetlb index units: the page cache index of a hugetlb folio is in base
  pages (`hugetlb_add_to_page_cache()` shifts by `huge_page_order()`).
  `struct file_region` and `vma_hugecache_offset()` count in huge pages.
