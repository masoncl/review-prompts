# MM Large Folios, THP, and Hugetlb

## Main structures

### Objects and how they relate

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

## Where to look

**Core files**

| Job | File in this tree | Easy to miss |
|---|---|---|
| hugetlb sysfs | `mm/hugetlb_sysfs.c` | Exists; built with `mm/hugetlb.c` under `CONFIG_HUGETLBFS`. |
| hugetlb sysctl | `mm/hugetlb_sysctl.c` | Exists. `__nr_hugepages_store_common()`, which the sysfs and sysctl stores both call, is in `mm/hugetlb.c`. |
| hugetlb private header | `mm/hugetlb_internal.h` | Exists; included only by `mm/hugetlb.c` and the two files above. |
| rmap calls, PTE, PMD and PUD level | `mm/rmap.c` for add and remove; `include/linux/rmap.h` for dup and share | The dup and share forms, for example `folio_try_dup_anon_rmap_ptes()` and `folio_try_share_anon_rmap_pmd()`, are inline in the header. The single-PTE forms such as `folio_add_anon_rmap_pte()` are macros in `include/linux/rmap.h`. The level type is `enum pgtable_level` in `include/linux/pgtable.h`; there is no enum rmap_level. |
| rmap calls, hugetlb | `mm/rmap.c` and `include/linux/rmap.h` | `hugetlb_add_anon_rmap()` and `hugetlb_add_new_anon_rmap()` are in `mm/rmap.c`; the other hugetlb rmap helpers are inline in the header. |
| Large folio swap-in, anonymous | `mm/memory.c` and `mm/swap_state.c` | There is no alloc_swap_folio(). `do_swap_page()` picks orders with `thp_swapin_suitable_orders()`; `swapin_sync()` allocates in `swap_cache_alloc_folio()`. Only on `SWP_SYNCHRONOUS_IO` devices; `swapin_readahead()` reads order 0. |
| Large folio swap-in, shmem | `mm/shmem.c` | `shmem_swap_alloc_folio()`, called from `shmem_swapin_folio()`; it calls the same `swapin_sync()`. |

**Entry points**

| Job | Start reading from | Name or path that differs in this tree |
|---|---|---|
| Fault in an anonymous PMD-sized folio | `do_huge_pmd_anonymous_page()` | Mapping helper is `map_anon_folio_pmd_pf()`; `map_anon_folio_pmd_nopf()` is the form `mm/khugepaged.c` uses. |
| Split a huge PMD | `__split_huge_pmd()` | It calls `split_huge_pmd_locked()`, which calls `__split_huge_pmd_locked()`. With the PMD lock already held, enter at `split_huge_pmd_locked()`, as `mm/rmap.c` does; it has `VM_WARN_ON_ONCE()` for an address that is not PMD-aligned. |
| Split a large folio, uniform | `__split_huge_page_to_list_to_order()` in `mm/huge_memory.c` | `split_huge_page_to_list_to_order()` is an inline wrapper in `include/linux/huge_mm.h`. Both reach `__folio_split()`. |
| Split a large folio, non-uniform | `folio_split()` | No function named try_folio_split or try_folio_split_to_order exists; `folio_split_or_unmap()` in `mm/truncate.c` calls `folio_split()` directly. |
| Split an already unmapped anonymous folio | `folio_split_unmapped()` | Does not go through `__folio_split()`; calls `__folio_freeze_and_split_unmapped()` itself. |
| Collapse, both callers | `collapse_single_pmd()` | Called by `collapse_scan_mm_slot()` for khugepaged and by `madvise_collapse()`. There is no khugepaged_scan_mm_slot(). |
| Collapse, anonymous | `collapse_scan_pmd()` | There is no hpage_collapse_scan_pmd(). It calls `mthp_collapse()`, the only caller of `collapse_huge_page()`, which takes an `order` and can build a folio smaller than PMD size. |
| Collapse, file and shmem | `collapse_scan_file()`, then `collapse_file()` | There is no hpage_collapse_scan_file(). |
| Allocate a hugetlb folio | `alloc_hugetlb_folio()` | It does reservation and subpool accounting, then calls `hugetlb_alloc_folio()`, which charges cgroups and calls `dequeue_hugetlb_folio()` or `alloc_buddy_hugetlb_folio()`. There is no dequeue_hugetlb_folio_vma() or alloc_buddy_hugetlb_folio_with_mpol(). |
| Reserve hugetlb pages at mmap | `hugetlb_reserve_pages()` | Called from `hugetlbfs_file_mmap()`, installed as `.mmap` in `hugetlbfs_file_operations`. There is no hugetlbfs_file_mmap_prepare(). |
| Handle a hardware memory error | `memory_failure()` | hugetlb branch is `try_memory_failure_hugetlb()`; there is no memory_failure_hugetlb(). `memory_failure()` goes on to normal page handling only when it returns `-ENOENT`. |

## Large folio state

**Kinds of large folio**

- `PG_large_rmappable`: there is no folio_prep_large_rmappable() or
  folio_undo_large_rmappable() here; `page_rmappable_folio()` in
  `mm/internal.h` sets the flag.
- `page_rmappable_folio()`: runs in `__folio_alloc_noprof()`,
  `folio_alloc_noprof()`, `folio_alloc_mpol_noprof()` and
  `compaction_alloc_noprof()`, so any large folio from those has the flag,
  whoever allocated it.
- `alloc_pages()` with `__GFP_COMP`: does not set the flag.
- Other setters of the flag: `__split_folio_to_order()` for each new large
  folio, `zone_device_folio_init()`, and
  `migrate_vma_insert_huge_pmd_page()` in `mm/migrate_device.c`.
- Huge zero folio: large and PMD-order, but `alloc_huge_zero_folio()` clears
  the flag; `is_transparent_hugepage()` in `mm/huge_memory.c` tests for it
  separately.
- `__folio_rmap_sanity_checks()`: does not test `folio_test_large_rmappable()`,
  so the rmap functions accept large folios without the flag.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `folio_test_pmd_mappable()` and
  `folio_test_large_rmappable()` are constant `false`, hugetlb included, and
  `folio_set_large_rmappable()` is empty.
- `folio_test_large_rmappable()` on a folio not known to be large: only
  `VM_BUG_ON_PGFLAGS()` in `const_folio_flags()` catches it; without
  `CONFIG_DEBUG_VM_PGFLAGS` it reads the flags of the next `struct page`.

**Per-folio and per-page state**

- Anon exclusive, PMD-mapped or hugetlb: the head page's `PG_anon_exclusive`
  is the state itself, not a hint; no other copy exists while mapped.
- Anon exclusive, not mapped: kept in the entry, by `pte_swp_mkexclusive()`
  for swap (see `swp_pte_prepare()` in `mm/rmap.c`) and by the migration
  entry type for migration.
- Hardware poison, hugetlb: `hugetlb_update_hwpoison()` in
  `mm/memory-failure.c` sets `PG_hwpoison` on the head page and records the
  bad page in the list at `folio->_hugetlb_hwpoison`.
- `PG_has_hwpoisoned`: needs both `CONFIG_MEMORY_FAILURE` and
  `CONFIG_TRANSPARENT_HUGEPAGE`; otherwise the test is constant `false`.
- Mapcount under `CONFIG_NO_PAGE_MAPCOUNT`: `page->_mapcount` of pages in a
  large folio and `folio->_nr_pages_mapped` are not maintained; see
  `__folio_add_rmap()`.
- `folio_precise_page_mapcount()` in `fs/proc/internal.h`: `BUILD_BUG()`
  without `CONFIG_PAGE_MAPCOUNT`.
- `_mm_id_mapcount[]` and `_mm_ids`: maintained only under `CONFIG_MM_ID`,
  which `CONFIG_TRANSPARENT_HUGEPAGE` selects.
- `_entire_mapcount` and `_pincount` on 32-bit: in the third page of
  `struct folio`, so an order-1 folio has none and `folio_entire_mapcount()`
  returns 0 for it.

**Anonymous exclusive flag**

- `PageAnonExclusive()` on a hugetlb tail page: reads the head page's bit, no
  warning.
- `SetPageAnonExclusive()` and `ClearPageAnonExclusive()` on a hugetlb tail
  page: `VM_BUG_ON_PGFLAGS()`.
- `__folio_add_anon_rmap()`: takes `enum pgtable_level`; there is no
  RMAP_LEVEL_PMD here, the value is `PGTABLE_LEVEL_PMD`.
- `PGTABLE_LEVEL_PMD` with `RMAP_EXCLUSIVE`: sets the bit only on the `page`
  argument, so the caller passes the head page.
- `folio_move_anon_rmap()`: writes `folio->mapping` only; it does not set the
  flag.
- Write-fault reuse of a large PTE-mapped folio: `do_wp_page()` calls
  `SetPageAnonExclusive()` on `vmf->page` alone, under the page table lock,
  without the folio lock and without `folio_move_anon_rmap()`.
- `__folio_remove_rmap()`: does not clear the flag, so an unmapped page of a
  large folio can keep a stale set bit.
- Stale bits: `__split_folio_to_order()` drops them only from the pages that
  become new heads.
- `folio_try_share_anon_rmap_pte()` and `folio_try_share_anon_rmap_pmd()`:
  need the entry cleared or invalidated first, not flushed;
  `try_to_migrate_one()` defers the TLB flush when `should_defer_flush()`.
- Device-private folio: `__folio_try_share_anon_rmap()` clears the flag with
  no pin test, and `__folio_try_dup_anon_rmap()` skips the pin test.
- Fork, PTE batch: `__folio_try_dup_anon_rmap()` returns `-EBUSY` before it
  clears anything if the folio may be pinned and any page in the range is
  exclusive.
- Fork, after that `-EBUSY`: `copy_present_ptes()` returns `-EAGAIN`, then
  retries one page at a time with a preallocated folio.
- PMD split with `freeze`: `__split_huge_pmd_locked()` clears the head flag
  with `folio_try_share_anon_rmap_pmd()`, adds no PTE rmap, and writes the
  exclusivity into each PTE migration entry.
- PMD split with `freeze`, share fails: it splits as if `freeze` were false
  and leaves the failure to `try_to_migrate_one()`.
- PMD split of a migration entry: exclusivity comes from the entry type; page
  flags are not touched.
- **Unsafe usage**: `ClearPageAnonExclusive()` on a mapped page outside the
  rmap helpers.
  - Safe: `folio_try_share_anon_rmap_pte()` after the entry is cleared, as
    `try_to_migrate_one()` does; `__folio_try_share_anon_rmap()` holds the
    barriers that pair with `gup_must_unshare()`.
  - Safe: `folio_try_dup_anon_rmap_ptes()` at fork with the source entry
    still present, under `write_protect_seq`; `folio_needs_cow_for_dma()`
    asserts it.
  - Safe: `__ClearPageAnonExclusive()` on a folio whose reference count is
    zero, as `free_huge_folio()` does.

**Large mapcount lock**

- `folio_lock_large_mapcount()`: defined only under `CONFIG_MM_ID`; without
  it `folio_add_large_mapcount()` is a plain `atomic_add()` and
  `folio_maybe_mapped_shared()` returns `true` for every large non-hugetlb
  folio.
- Stable under the lock: only against `folio_add_return_large_mapcount()` and
  `folio_sub_return_large_mapcount()`, which update `_large_mapcount` with
  `atomic_read()` then `atomic_set()`.
- hugetlb: its rmap helpers change `_large_mapcount` with `atomic_inc()`,
  `atomic_dec()` or, in `hugetlb_add_new_anon_rmap()`, `atomic_set()`, and
  never take the lock or track MM ids.
- `folio_set_large_mapcount()`: writes `_large_mapcount` and slot 0 without
  the lock; `folio_add_new_anon_rmap()` uses it on a folio not yet mapped.
- `__wp_can_reuse_large_anon_folio()`: never reads `_mm_id_mapcount[]`; it
  tests `FOLIO_MM_IDS_SHARED_BITNUM` in `_mm_ids` and compares
  `folio_large_mapcount()` with `folio_ref_count()`, both again under the
  lock.
- folio_test_large_maybe_mapped_shared(): not in this tree; the public test
  is `folio_maybe_mapped_shared()` in `include/linux/mm.h`.
- `folio_large_mapcount() <= 1`: `__wp_can_reuse_large_anon_folio()` returns
  `false` at once, so a large folio with one mapped page is copied, not
  reused.
- Swapcache: not a reason to give up; it calls `folio_free_swap()` under
  `folio_trylock()` and goes on. Only a failed `folio_trylock()` returns
  `false`.
- Folio lock: not held for the comparison.

**Rmap calls by mapping level**

- PUD forms: only `folio_add_file_rmap_pud()` and `folio_remove_rmap_pud()`.
  There is no PUD dup function, file or anon, and no anon PUD add.
- `folio_dup_file_rmap_pmd()`: has no caller; `copy_huge_pmd()` returns 0
  for a non-anonymous VMA, unless the PMD is present, `pmd_special()` and not
  the huge zero PMD, and leaves the PMD to be refilled on fault.
- hugetlb file mapping at fork: `hugetlb_add_file_rmap()`; there is no
  hugetlb_dup_file_rmap().
- `folio_add_new_anon_rmap()`: picks the accounting from the folio size, not
  from a level argument. A folio for which `folio_test_pmd_mappable()` is true
  is counted as one entire mapping, so the caller must map it with a PMD.
- PMD forms without `CONFIG_TRANSPARENT_HUGEPAGE`: `WARN_ON_ONCE(true)` and no
  accounting; `folio_try_dup_anon_rmap_pmd()` returns `-EBUSY`.
- PUD forms: also need `CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD`, else the
  same stub.
- `__folio_rmap_sanity_checks()`: every check is `VM_WARN_ON_FOLIO()` or
  `VM_WARN_ON_ONCE()`, so a wrong level or a hugetlb folio passes silently
  without `CONFIG_DEBUG_VM`.

**First tail page flags**

- `PG_has_hwpoisoned`, `PG_large_rmappable`, `PG_partially_mapped`: declared
  with `FOLIO_FLAG()` only. No `__FOLIO_SET_FLAG` or `__FOLIO_CLEAR_FLAG` line
  uses `FOLIO_SECOND_PAGE`, so no non-atomic setter or clearer exists for
  them.
- Bits 0-7 of the same word: the folio order, read by `folio_large_order()`.
  The mapcounts are separate fields, not part of the word.
- `folio_set_order()` in `mm/internal.h` and `folio_reset_order()` in
  `include/linux/mm.h`: plain read-modify-write of all of `folio->_flags_1`.
- `__free_pages_prepare()` in `mm/page_alloc.c`: clears `PAGE_FLAGS_SECOND`
  from page 1 with a plain `&=`.
- Per-page flags of page 1, written with atomic bit operations: for example
  `PG_anon_exclusive` under the page table lock, `PG_hwpoison`, and arm64
  `PG_mte_tagged`.
- `memory_failure()`: calls `TestSetPageHWPoison()` before
  `get_hwpoison_page()`, so it can write the word while holding no reference.
- A new second-page flag: must avoid bits 0-7 and any `PF_ANY` flag; one that
  aliases a flag in `PAGE_FLAGS_CHECK_AT_FREE`, as `PG_has_hwpoisoned` aliases
  `PG_active`, must be in `PAGE_FLAGS_SECOND`, which `__free_pages_prepare()`
  clears from page 1 before `free_page_is_bad()` tests that page.
- **Unsafe usage**: a non-atomic setter or clearer for a `FOLIO_SECOND_PAGE`
  flag, used on a folio that can be mapped.
  - Unsafe: `SetPageAnonExclusive()` on page 1 is a concurrent `set_bit()` on
    the same word that holds only the page table lock.
  - Safe: the atomic `folio_set_partially_mapped()`, as
    `deferred_split_folio()` uses it; `FOLIO_SET_FLAG` declares it with
    `set_bit()`.

## Huge PMD entries

**Huge PMD tests**

| Test | True for | Easy to miss |
|---|---|---|
| `pmd_trans_huge()` | present huge PMD, also one made invalid by `pmdp_invalidate()` | also true for a hugetlb PMD: x86 tests only `_PAGE_PSE`; riscv and s390 return `pmd_leaf()` |
| `pmd_leaf()` | arch leaf test | some architectures do not test present, for example x86, loongarch and powerpc book3s64 |
| `pmd_is_huge()` | present and `pmd_trans_huge()`, or any non-none non-present PMD | does not check the entry kind |

- `pmd_is_huge()`: defined in `include/linux/huge_mm.h`; constant false without
  `CONFIG_TRANSPARENT_HUGEPAGE`.
- `pmd_is_valid_softleaf()`: the test that a non-present PMD is a migration or
  device-private entry; `pmd_is_huge()` does not make it.
- `pmd_leaf()` on powerpc book3s64: true for a PMD softleaf entry, because
  `__swp_entry_to_pte()` sets `_PAGE_PTE`.
- `pmd_leaf()`: paired with a `pmd_present()` test where the PMD may be
  non-present, for example in `mm/pagewalk.c` and `mm/mremap.c`.
- `pmd_is_huge()` is the lockless gate in generic range walkers, for example
  `zap_pmd_range()` and `change_pmd_range()`; search for the rest.
- `pmd_trans_huge()` is used where only a present entry is wanted, for example
  `__handle_mm_fault()` after its `pmd_present()` test, and `__pte_offset_map()`.
- hugetlb: excluded by the VMA, not by any of the three tests.
- `vma_is_special_huge()`: static in `mm/huge_memory.c` and false for a DAX VMA;
  code elsewhere uses `vm_normal_folio_pmd()`.
- **Potentially unsafe usage**: taking a true `pmd_trans_huge()` or
  `pmd_is_huge()` to mean "maps a THP folio".
  - Unsafe: when the VMA may be hugetlb, DAX or PFN-mapped, or the entry may be
    the huge zero folio or non-present; `vm_normal_folio_pmd()` returns NULL
    for special and huge zero entries and reads `pmd_pfn()` of what it is given.
  - Safe: `madvise_free_huge_pmd()`: `mm/madvise.c` refuses `MADV_FREE` on a
    non-anonymous VMA, and under `pmd_trans_huge_lock()` it tests
    `is_huge_zero_pmd()` and `pmd_present()` before `pmd_folio()`.
  - Safe: `do_huge_pmd_numa_page()`: `pmd_same()` under `pmd_lock()`, then
    `vm_normal_folio_pmd()` and a NULL test.

**Non-present huge PMD entries**

- Kinds: migration and device-private only; `softleaf_is_valid_pmd_entry()` in
  `include/linux/leafops.h` defines the set.
- Config: `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; there is no
  CONFIG_ARCH_ENABLE_THP_MIGRATION here. `thp_migration_supported()` tests it.
- Without `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`: `softleaf_from_pmd()` returns the
  none entry, and `set_pmd_migration_entry()` is a `BUILD_BUG()` stub.
- `pmd_is_device_private_entry()`: also needs `CONFIG_ZONE_DEVICE`, constant
  false otherwise.
- There is no is_pmd_migration_entry() or pmd_to_swp_entry() here;
  `pmd_is_migration_entry()` and `softleaf_from_pmd()` do those jobs.
- There is no pmd_swp_uffd_wp() or pmd_swp_mkuffd_wp() here; the helpers are
  `pmd_swp_uffd()`, `pmd_swp_mkuffd()`, `pmd_swp_clear_uffd()`, and `pmd_uffd()`
  for a present PMD.
- The uffd bit serves both write-protect and RWP; `userfaultfd_huge_pmd_wp()`
  and `userfaultfd_huge_pmd_rwp()` tell them apart by the VMA.
- There is no pmd_none_or_trans_huge_or_clear_bad() here.
- `softleaf_from_pmd()`: returns the none entry for a present or none PMD.
- `softleaf_from_pmd()`: strips the soft-dirty and uffd bits; read them from the
  PMD with `pmd_swp_soft_dirty()` and `pmd_swp_uffd()`.
- `pmd_to_softleaf_folio()`: decodes a PMD to a folio; returns NULL, with a
  `VM_WARN_ON_ONCE()`, for an entry that is not a valid PMD softleaf.
- `softleaf_to_folio()` and `softleaf_to_page()` on a migration entry:
  `VM_WARN_ON_ONCE()` if the folio is not locked; see
  `softleaf_migration_sync()`.
- Migration PMD: holds no folio reference and no mapcount.
- Device-private PMD: holds a reference and a PMD mapcount; see
  `zap_huge_pmd_folio()`.
- `set_pmd_migration_entry()`: accepts a present PMD or a device-private PMD,
  and anonymous or file folios.
- `set_pmd_migration_entry()`: returns 0 and does nothing unless `pvmw` is at a
  PMD mapping; returns `-EBUSY`, with the PMD restored, only when
  `folio_try_share_anon_rmap_pmd()` fails.

**Locking a huge PMD**

- `pmd_trans_huge_lock()`: tests `pmd_is_huge()` locklessly, and
  `__pmd_trans_huge_lock()` tests it again under `pmd_lock()`.
- There is no pmd_devmap() here.
- Lock is returned held for any non-none non-present PMD, not only for a
  migration or device-private entry; the `pmd_is_valid_softleaf()` test is
  left to the caller.
- `__pmd_trans_huge_lock()` called directly: no lockless test, the lock is
  always taken; `zap_huge_pmd()`, `move_huge_pmd()` and `change_huge_pmd()` do
  this.
- `huge_pmd_set_accessed()`: takes no lock; `__handle_mm_fault()` holds
  `pmd_lock()` around it, and it only makes the `pmd_same()` test.

**Deposited page table**

- `has_deposited_pgtable()` in `mm/huge_memory.c`: the test `zap_huge_pmd()`
  uses; it is static.
- `has_deposited_pgtable()` conditions, in order:
  1. `arch_needs_pgtable_deposit()`: every huge PMD has one.
  2. huge zero PMD: has one unless the VMA is DAX.
  3. otherwise: only if the folio is anonymous, which covers migration and
     device-private PMDs of anonymous folios.
- `arch_needs_pgtable_deposit()`: overridden only by powerpc book3s64, true
  when radix is not enabled.
- `insert_pmd()` (DAX, PFN map, huge zero in a DAX VMA): deposits only when
  `arch_needs_pgtable_deposit()`.
- The three operations use different tests:

| Operation | Test for a deposit |
|---|---|
| `zap_huge_pmd()` | `has_deposited_pgtable()`, by entry and folio |
| `__split_huge_pmd_locked()` | by VMA: anonymous always withdraws; otherwise only `arch_needs_pgtable_deposit()` |
| `move_huge_pmd()` | `pmd_move_must_withdraw()` |

- `pmd_move_must_withdraw()`, generic: PMD locks differ and
  `vma_is_anonymous()`; powerpc hash returns true always.
- `move_pages_huge_pmd()`: moves the deposit to the destination on every
  successful move.
- Order: `zap_huge_pmd()` withdraws only after the PMD is cleared, and
  `__split_huge_pmd_locked()`, for a present PMD, only after it is cleared or
  invalidated; `hash__pmdp_huge_get_and_clear()` zeroes the deposited table.
- **Potentially unsafe usage**: installing an anonymous huge PMD without
  `pgtable_trans_huge_deposit()` and `mm_inc_nr_ptes()`.
  - Unsafe: when the PMD was none and no table was added to its
    `pmd_huge_pte()` list for it; `__split_huge_pmd_locked()` withdraws
    unconditionally in an anonymous VMA, and the generic
    `pgtable_trans_huge_withdraw()` has no NULL test on `pmd_huge_pte()`.
  - Safe: when the entry replaced already had a deposit, as
    `do_huge_zero_wp_pmd()` does over a huge zero PMD and
    `remove_migration_pmd()` does over a migration PMD.
  - Safe: `move_huge_pmd()` when `pmd_move_must_withdraw()` is false; the old
    and new PMD share one `pmd_huge_pte()` list, so the deposit of the old
    entry serves the new one.
  - Safe: `collapse_huge_page()` deposits the old PTE table without
    `mm_inc_nr_ptes()`; that table was already counted.

**Splitting a huge PMD**

- `__split_huge_pmd_locked()`: does not test whether the PMD is huge, only
  `VM_WARN_ON_ONCE()`; its one caller `split_huge_pmd_locked()` decides.
- `split_huge_pmd_locked()`: splits when `pmd_trans_huge()` or
  `pmd_is_valid_softleaf()`; this is narrower than `pmd_is_huge()`, which
  `split_huge_pmd()` tests locklessly.
- `split_huge_pmd_locked()` and `__split_huge_pmd()`: four arguments, no folio
  argument.
- `split_huge_pmd_address()`: does nothing when `mm_find_pmd()` returns NULL.
- Non-anonymous VMA, by entry, after the PMD is cleared and, when
  `arch_needs_pgtable_deposit()`, the deposited table is freed:

| Entry | Further work |
|---|---|
| `vma_is_special_huge()` VMA | none |
| migration entry | file RSS counter reduced only; no rmap removal, no `folio_put()` |
| huge zero PMD | none |
| present folio, DAX included | dirty and referenced moved, `folio_remove_rmap_pmd()`, counter, `folio_put()` |

- There is no devmap test here; `vma_is_special_huge()` is PFN-map or mixed-map
  and not DAX.
- Device-private PMD: device-private PTE entries without `freeze`, migration
  PTE entries with `freeze`.
- uffd bit: read with `pmd_uffd()` or `pmd_swp_uffd()`, written with
  `pte_mkuffd()` or `pte_swp_mkuffd()`.
- `userfaultfd_rwp()` VMA with the uffd bit set: the present PTEs are remade
  with `PAGE_NONE`; no other protnone state is carried.

**PMD split accounting**

- Split without `freeze`: `folio_add_anon_rmap_ptes()` with `RMAP_EXCLUSIVE`
  sets `PG_anon_exclusive` on every subpage.
- Device-private PMD: accounted like a present PMD, but there is no
  `pmdp_invalidate()`; sharing cannot fail for a device-private folio.
- Migration PMD without `freeze`: no reference or mapcount change.
- Migration PMD with `freeze`: `put_page()` still drops one reference;
  `migrate_vma_split_unmapped_folio()` takes one first for that reason.
- Invalidate: `pmdp_invalidate()`, for a present PMD only;
  `pmdp_invalidate_ad()` is not used here.
- Order for a present PMD:
  1. `pmdp_invalidate()`
  2. share attempt if `freeze` and the page is exclusive
  3. `folio_ref_add()` and `folio_add_anon_rmap_ptes()` if not `freeze`
  4. `pgtable_trans_huge_withdraw()`
  5. PTE writes
  6. `folio_remove_rmap_pmd()`, then `put_page()` if `freeze`
  7. `smp_wmb()`, `pmd_populate()`
- Withdraw after invalidate: powerpc hash keeps per-PMD state in the deposited
  table; see `arch/powerpc/mm/book3s64/hash_pgtable.c`.

**Unmapping a PMD-mapped folio**

- PMD mapping reached in `try_to_unmap_one()` without `TTU_SPLIT_HUGE_PMD`:
  the only check is `VM_BUG_ON_FOLIO(!pvmw.pte, folio)`; without
  `CONFIG_DEBUG_VM` it compiles out and `ptep_get()` reads through a NULL
  `pvmw.pte`.
- `VM_LOCKED` VMA without `TTU_IGNORE_MLOCK`: handled before the PMD branch;
  the PMD is not split, `mlock_vma_folio()` runs and the walk ends as failed.
- `folio_test_lazyfree()` folio: tested before `TTU_SPLIT_HUGE_PMD`, with or
  without the flag; `unmap_huge_pmd_locked()` discards the PMD mapping.
- `unmap_huge_pmd_locked()` failure: the walk aborts; the PMD is not split even
  with the flag.
- MMU notifier range: `address` to `vma_address_end()`; it does not depend on
  `TTU_SPLIT_HUGE_PMD`.
- `try_to_migrate_one()` with the flag: `split_huge_pmd_locked()` with `freeze`
  true, then a restart.
- `try_to_migrate_one()` without the flag: `set_pmd_migration_entry()` under
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; a failure aborts the walk, there is no
  fallback to a split.
- **Potentially unsafe usage**: `try_to_unmap()` without `TTU_SPLIT_HUGE_PMD`.
  - Unsafe: when the folio can be PMD-mapped and is not lazyfree;
    `try_to_unmap_one()` reaches `VM_BUG_ON_FOLIO(!pvmw.pte, folio)`.
  - Safe: when the folio cannot be PMD order; `collapse_file()` rejects
    `is_pmd_order()` folios before the call.
  - Safe: set the flag for `folio_test_pmd_mappable()` folios, as
    `shrink_folio_list()` and `unmap_folio()` do.

**Huge PMD write fault**

- Huge zero PMD: `do_huge_zero_wp_pmd()` allocates a PMD-sized folio and maps
  it in place under its own MMU notifier range; the split runs only if it
  returns `VM_FAULT_FALLBACK`.
- `folio_trylock()` failure: no split; takes a reference, drops the PMD lock,
  sleeps in `folio_lock()`, retakes the PMD lock, rechecks `pmd_same()`, and
  returns 0 if the PMD changed.
- Count test, under the folio lock and the PMD lock:
  1. fall back if `folio_ref_count()` exceeds 1, plus `folio_nr_pages()` when
     the folio is in the swap cache
  2. `folio_free_swap()` if in the swap cache
  3. reuse only if `folio_ref_count()` is 1
- Unshare fault on a reusable folio: returns 0 with the PMD unchanged.
- `__split_huge_pmd()` on fallback: called with `freeze` false.

## Allocating large anonymous folios

**Allowed orders for a VMA**

- `enum tva_type` in `include/linux/huge_mm.h`: four values, `TVA_SMAPS`,
  `TVA_PAGEFAULT`, `TVA_KHUGEPAGED`, `TVA_FORCED_COLLAPSE`; the `type`
  argument is one of them, not a mask of flags.
- DAX and PFN/MIXEDMAP mask: `THP_ORDERS_ALL_SPECIAL_DAX`; there is no
  THP_ORDERS_ALL_SPECIAL or THP_ORDERS_ALL_FILE_DAX here.
- `vma_is_special_huge()`: static in `mm/huge_memory.c`, returns false for a
  DAX VMA and true for any other VMA with `VMA_PFNMAP_BIT` or
  `VMA_MIXEDMAP_BIT`; `__thp_vma_allowable_orders()` tests `vma_is_dax()`
  beside it.
- Anonymous orders: `THP_ORDERS_ALL_ANON` is 2 to `PMD_ORDER`; order 1 is never
  returned.
- File orders: `THP_ORDERS_ALL_FILE_DEFAULT` is 1 to `MAX_PAGECACHE_ORDER`; the
  function does not narrow a non-shmem file VMA to PMD order.
- `VM_NO_KHUGEPAGED` test: applies only to `TVA_KHUGEPAGED` and
  `TVA_FORCED_COLLAPSE`; a page fault or smaps query on such a VMA is not
  rejected by it.
- Process-wide disable: `vma_thp_disabled()` tests
  `MMF_DISABLE_THP_COMPLETELY` (the result is always 0) and
  `MMF_DISABLE_THP_EXCEPT_ADVISED` (ignored with `VM_HUGEPAGE` or forced
  collapse); there is no MMF_DISABLE_THP.
- File VMA and the global setting: `vma_can_map_huge_file()` in
  `mm/huge_memory.c` requires `hugepage_global_always()`, or `VM_HUGEPAGE` with
  `hugepage_global_enabled()`.
- Global setting bypassed: for `TVA_FORCED_COLLAPSE`, and for a
  `VMA_PFNMAP_BIT` VMA whose `vm_ops` has `->huge_fault`; see
  `vma_file_bypass_thp_tuneables()`.
- DAX VMA: returns before `vma_can_map_huge_file()`, so a DAX page fault gets
  its orders whatever the global setting is.
- `file_thp_enabled()` (collapse and smaps): needs `vm_file`, a regular file,
  not `IS_ANON_FILE()`, and `mapping_pmd_folio_support()`; there is no
  CONFIG_READ_ONLY_THP_FOR_FS in this tree.

**Smaller anonymous large folios**

- Allocation gfp: `vma_thp_gfp_mask(vma)`, which follows the defrag setting
  and `VM_HUGEPAGE` and can include direct reclaim.
- `pte_offset_map()` returning NULL: `alloc_anon_folio()` returns
  `ERR_PTR(-EAGAIN)` and `do_anonymous_page()` returns 0; no order-0 folio is
  allocated.
- `mem_cgroup_charge()` failure: counts
  `MTHP_STAT_ANON_FAULT_FALLBACK_CHARGE` and `MTHP_STAT_ANON_FAULT_FALLBACK`,
  then tries the next lower order.
- `folio_memcg_alloc_deferred()` runs after a successful charge; on failure the
  folio is put and the code jumps to the order-0 `folio_prealloc()`, without
  trying lower orders and without counting a fallback.
- `MTHP_STAT_ANON_FAULT_ALLOC`: counted in `map_anon_folio_pte_pf()` in
  `mm/memory.c`, after the PTEs are set; a folio dropped at the locked recheck
  is not counted.
- `userfaultfd_armed()` in `include/linux/userfaultfd_k.h`: tests
  `__VMA_UFFD_FLAGS`, which here includes `VMA_UFFD_RWP` beside missing, wp
  and minor.
- uffd-wp bit: set with `pte_mkuffd()`; there is no pte_mkuffd_wp() in this
  tree.

**Adding an allocation site**

- `add_mm_counter()` for `MM_ANONPAGES` and `MTHP_STAT_ANON_FAULT_ALLOC`: done
  by the static wrappers `map_anon_folio_pmd_pf()` and
  `map_anon_folio_pte_pf()`; `THP_FAULT_ALLOC` and `count_memcg_event_mm()` by
  `map_anon_folio_pmd_pf()` only.
- Caller of a `_nopf` helper: does its own `MM_ANONPAGES` update; the collapse
  does it in `__collapse_huge_page_copy_succeeded()` in `mm/khugepaged.c`.
- `update_mmu_cache_pmd()` and `update_mmu_cache_range()`: called inside the
  `_nopf` helpers, not left to the caller.
- `deferred_split_folio(folio, false)`: called inside
  `map_anon_folio_pmd_nopf()`; `map_anon_folio_pte_nopf()` does not call it.
- `mm_inc_nr_ptes()` and `pgtable_trans_huge_deposit()`: left to the caller of
  `map_anon_folio_pmd_nopf()`; see `__do_huge_pmd_anonymous_page()`.
- References: `map_anon_folio_pte_nopf()` adds `nr_pages - 1` with
  `folio_ref_add()`; `map_anon_folio_pmd_nopf()` adds none; both consume the
  caller's allocation reference, so an error path before the helper needs one
  `folio_put()`.
- `map_anon_folio_pte_nopf()` from a non-fault caller: takes no page table
  lock itself; `collapse_huge_page()` re-installs the table with
  `pmd_populate()` and holds the PTE lock, nested inside the PMD lock, around
  the call, because the helper calls `update_mmu_cache_range()`, which walks
  the page table on MIPS (`__update_tlb()`).
- Entry construction: `folio_mk_pmd()` and `folio_mk_pte()`; there is no
  mk_pmd() in this tree.
- Error paths after the charge in `__do_huge_pmd_anonymous_page()` (`release`,
  `unlock_release`, the `userfaultfd_missing()` branch): count no fallback
  stat; the failure branches inside `vma_alloc_anon_folio_pmd()` count
  `THP_FAULT_FALLBACK` and `MTHP_STAT_ANON_FAULT_FALLBACK`.

## Splitting a folio

**Split entry points**

| Function | Target order | Pieces | Where pieces go | Kept locked + referenced |
|---|---|---|---|---|
| `split_folio()`, `split_folio_to_list()` | 0, never the mapping's min order | uniform | LRU, or `list` | first piece (the pointer passed) |
| `split_folio_to_order()` | `new_order` | uniform | LRU | first piece (the pointer passed) |
| `split_huge_page()`, `split_huge_page_to_order()`, `split_huge_page_to_list_to_order()` | 0 for `split_huge_page()`, else `new_order` | uniform | LRU, or `list` | piece containing `page` |
| `folio_split()` | `new_order` for `split_at`'s piece | non-uniform | LRU, or `list` | first piece, wherever `split_at` is |
| `folio_split_unmapped()` | `new_order` | uniform | nowhere: no LRU, no list | every piece |

- `split_huge_page()`, `split_huge_page_to_order()`,
  `split_huge_page_to_list_to_order()`: when `page` is outside the first
  piece, the first piece is unlocked and put like any other.
- Anon folio, every entry point but `folio_split_unmapped()`: must be mapped
  at least once; `folio_get_anon_vma()` returns NULL for an unmapped folio
  and the split returns `-EBUSY`.
- `anon_vma` lock and `i_mmap_rwsem`: taken by `__folio_split()`, not by the
  caller.
- `list != NULL`: each new piece but `lock_at`'s is unlocked; each is on
  `list` with one extra reference from `lru_add_split_folio()`, unless the
  folio is device-private; the original folio is not added.
- `folio_split_unmapped()`: anon, unmapped and locked are `VM_WARN_ON_ONCE_FOLIO()`
  only; it does not call `folio_check_splittable()`, so order and writeback
  are not checked.
- `folio_split_unmapped()` afterwards: caller remaps, puts pieces on the LRU,
  unlocks each piece and owns one reference on each; see
  `migrate_vma_split_unmapped_folio()` in `mm/migrate_device.c`.

**Split preconditions**

- Folio lock: `VM_WARN_ON_ONCE_FOLIO()` in `__folio_split()` and
  `VM_WARN_ON_FOLIO()` in `folio_check_splittable()`.
- Large folio: `VM_WARN_ON_ONCE_FOLIO()` in `__folio_split()`.
- Small folio: fails `new_order >= old_order` in `__folio_split()` with
  `-EINVAL`.
- `folio_check_splittable()` tests, in this order:
  - non-anon folio with NULL `->mapping`: `-EBUSY`
  - anon folio and `new_order == 1`: `-EINVAL`
  - swap cache folio with non-uniform split or non-zero order: `-EINVAL`
  - `is_huge_zero_folio()`: `-EINVAL`
  - writeback: `-EBUSY`
- `__folio_split()` tests the rest itself: `split_at` and `lock_at` inside the
  folio, `new_order` below the current order, `mapping_min_folio_order()`,
  `filemap_release_folio()`, `folio_get_anon_vma()`, the reference count.
- No test on the split path rejects a hugetlb folio or a mapping without
  large folio support.
- On the LRU when `list == NULL`: `VM_WARN_ON()` in `lru_add_split_folio()`
  only.

**Reference counts at split**

- There is no can_split_folio() here; the precheck is inline in
  `__folio_split()`: `folio_expected_ref_count(folio) != folio_ref_count(folio) - 1`.
- Precheck position: after `filemap_release_folio()` and after the anon_vma
  or `i_mmap_rwsem` lock, before `unmap_folio()`.
- Freeze: `folio_ref_freeze(folio, folio_cache_ref_count(folio) + 1)` in
  `__folio_freeze_and_split_unmapped()`.
- `folio_cache_ref_count()` in `mm/huge_memory.c`: counts page cache or swap
  cache references only, so a mapping that survived `unmap_folio()` or a
  remaining `PG_private` fails the freeze.
- `folio_split_unmapped()`: same precheck with the same `- 1`.
- New pieces and the original: unfrozen to `folio_cache_ref_count() + 1`, not
  to `folio_expected_ref_count() + 1`.
- Removed by the split itself: mapcount references (`unmap_folio()`) and the
  `PG_private` reference (`filemap_release_folio()`).
- Per-CPU LRU batches: do not hold large folios; `folio_may_be_lru_cached()`
  in `mm/internal.h` is false for them and `__folio_batch_add_and_move()`
  flushes at once.
- `deferred_split_scan()`: its reference is taken in
  `deferred_split_isolate()` and dropped by `deferred_split_scan()` after its
  split attempt on that folio.
- A second reference of the caller's own on the same folio: stays until the
  caller drops it; `cmp_and_merge_page()` in `mm/ksm.c` drops it, then
  splits.

**Split return values**

| Value | Source | Folio afterwards |
|---|---|---|
| `-EBUSY` | NULL `->mapping` on a non-anon folio; writeback; anon folio not mapped (`folio_get_anon_vma()`); `filemap_release_folio()` | whole, mappings untouched |
| `-EINVAL` | `folio_check_splittable()` order tests; `split_at` outside folio; `new_order` not below order; below min order | whole, mappings untouched |
| `-EAGAIN` | precheck | whole, mappings untouched |
| `-EAGAIN` | `xas_load()` mismatch; freeze | whole, already unmapped |
| `-ENOMEM` | `xas_split_alloc()`, uniform | whole, mappings untouched |
| `xas_error()` | `xas_try_split()`, non-uniform | may be partly split |

- Huge zero folio: `folio_check_splittable()` returns `-EBUSY`; its
  `->mapping` is NULL and it is not anon, so the truncated-folio test catches
  it before the `is_huge_zero_folio()` test.
- Reference count failures: `-EAGAIN`, never `-EBUSY`.
- Failure after `unmap_folio()`: an anon folio is remapped by `remap_page()`
  with PTEs; a file folio stays unmapped and refaults.
- Partly split folio: the pieces made so far are unfrozen, put on the LRU and
  unlocked as on success; the first piece stays locked.
- `-EINVAL` from `folio_check_splittable()`: also fires the `VM_WARN_ONCE()`
  "Tried to split an unsplittable folio" in `__folio_split()`; the min-order
  `-EINVAL` does not.
- `-EXDEV`: not returned by the split.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: the split stubs in
  `include/linux/huge_mm.h` return `-EINVAL` after a
  `VM_WARN_ON_ONCE_PAGE()` or `VM_WARN_ON_ONCE_FOLIO()`.

**Minimum order of a mapping**

- `min_order_for_split()` on a truncated folio: returns 0; the return type is
  `unsigned int`, so there is no error value to test for.
- `min_order_for_split()`: counts no event.
- Min-order test: in `__folio_split()`, after `folio_check_splittable()`
  passed.
- `split_folio()` and `split_folio_to_list()`: pass order 0, so they return
  `-EINVAL` on a file folio whose mapping has a non-zero minimum order.
- `truncate_inode_partial_folio()`: reads `mapping_min_folio_order()` itself
  and passes it to `folio_split_or_unmap()`, which calls `folio_split()`; it
  does not call `min_order_for_split()`.
- **Potentially unsafe usage**: using the pre-split `struct folio` pointer
  after a successful split.
  - Unsafe: after `split_huge_page()` or `split_huge_page_to_order()` on a
    page outside the first piece; the split unlocked and put the first piece.
  - Safe: after `split_folio()` or `folio_split()`, where `lock_at` is the
    first page, as `madvise_free_huge_pmd()` does; the pointer names a
    smaller folio.
  - Safe: calling `page_folio()` again on the page passed to the split, as
    `try_to_merge_one_page()` in `mm/ksm.c` does; `__folio_split()` keeps the
    piece containing `lock_at`.
- **Potentially unsafe usage**: treating the kept piece as order 0.
  - Unsafe: after a split to a non-zero order, or after `folio_split()`,
    whose first piece can have any order from `new_order` to the old order
    minus one.
  - Safe: after a uniform split to order 0; `memory_failure()` treats a
    non-zero `new_order` as a failed split.
- Kept piece with NULL `->mapping`: possible when the piece containing
  `lock_at` starts at or beyond EOF, since
  `__folio_freeze_and_split_unmapped()` removes such pieces from the page
  cache; the first piece is never removed.

**State carried to the pieces**

- New head pages: `flags.f &= ~PAGE_FLAGS_CHECK_AT_PREP` clears every flag but
  hwpoison before the masked copy, so a flag outside the mask is lost,
  `PG_anon_exclusive` included; young and idle are set again by
  `folio_set_young()` and `folio_set_idle()`.
- Copy mask: includes `PG_mlocked`, `PG_locked`, `PG_swapcache` and
  `PG_dropbehind`.
- `folio_split_memcg_refs()`, `split_page_owner()`, `pgalloc_tag_split()`:
  called by `__split_unmapped_folio()` before `__split_folio_to_order()`,
  not inside it.
- `zone_device_private_split_cb()`, LRU, page cache and swap cache slots,
  unfreeze: done by `__folio_freeze_and_split_unmapped()`.
- Last cpupid: `folio_xchg_last_cpupid()`; there is no
  page_cpupid_xchg_last() here.
- `split_page_memcg()`: exists but is not used by the folio split.
- `_deferred_list`, mapcount fields, `_pincount` of a new large folio:
  re-initialised by `prep_compound_page()`, not copied.
- `PG_partially_mapped` and deferred-list membership: removed from the old
  folio at freeze time; no piece is queued again.
- `private` on a new head: `VM_WARN_ON_ONCE_PAGE()` only, not cleared.
- `_mapcount` on a new head: asserted to be -1, not reset.
- A change that adds per-folio state must:
  - add a head-page flag to the mask;
  - read state kept in the second page (`PAGE_FLAGS_SECOND`) before the loop,
    which overwrites that page when it becomes a head, as `handle_hwpoison`
    does;
  - set second-page state after `prep_compound_page()`;
  - fix the first piece separately: the loop skips it, and apart from the
    `PG_has_hwpoisoned` handling before the loop only `folio_set_order()` or
    `ClearPageCompound()` touch it;
  - tolerate repeated calls: a non-uniform split calls the function once per
    order, each time on the piece containing `split_at`;
  - not sleep: both callers of `__folio_freeze_and_split_unmapped()` have
    IRQs off and the folio is frozen;
  - put per-page accounting in `__split_unmapped_folio()`.

**Split lock order and freeze**

- Anon folio, in order:
  1. folio lock (caller)
  2. `folio_get_anon_vma()`, `anon_vma_lock_write()`
  3. precheck, `unmap_folio()`
  4. `local_irq_disable()`
  5. order above 1 only: `rcu_read_lock()`, `list_lru_lock()` on
     `deferred_split_lru`
  6. `folio_ref_freeze()`, dequeue, `list_lru_unlock()`
  7. swap cache only: `swap_cluster_get_and_lock()`
  8. `folio_lruvec_lock()`
- File folio, in order:
  1. folio lock (caller)
  2. `filemap_release_folio()`; `xas_split_alloc()` for a uniform split
  3. `i_mmap_lock_read()`
  4. precheck, `unmap_folio()`
  5. `local_irq_disable()`, `xas_lock()`
  6. `folio_ref_freeze()`, with no deferred-split lock
  7. `folio_lruvec_lock()`
- New pieces: unfrozen one by one to `folio_cache_ref_count() + 1`, under
  whichever of `xas_lock()`, the swap cluster lock and the lruvec lock are
  held.
- Original folio: unfrozen last, under the same locks.
- Release order: `lruvec_unlock()`, `swap_cluster_unlock()`, `xas_unlock()`,
  `local_irq_enable()`, `remap_page()`, `i_mmap_unlock_read()`, unlock and
  put the other pieces, `anon_vma_unlock_write()`.
- `i_mmap_rwsem`: dropped before any piece is unlocked; nothing after that
  touches the mapping or the inode.
- Kept piece: the one containing `lock_at`; see "Split entry points" for
  which page each entry point passes.
- Caller's reference: each piece is unfrozen with one reference above the
  cache count; the unlock loop puts it for every piece but `lock_at`'s.

**Retrying a failed split**

- `madvise_free_huge_pmd()`: ignores the result of `split_folio()`; no retry.
- `try_to_split_thp_page()`: calls `split_huge_page_to_order()`, once; it puts
  the reference on failure only when `release` is true.
- `s390_wiggle_split_folio()` in `arch/s390/kernel/uv.c`: an in-tree retry
  loop; at most two tries, retries on `-EBUSY` only and only for a dirty file
  folio whose mapping can write back, unlocks and runs
  `filemap_write_and_wait_range()` between tries, keeps its reference.
- `lru_add_drain()` between tries: does not release a large folio; see
  "Reference counts at split".
- `madvise_cold_or_pageout_pte_range()`: PTE path does `folio_trylock()` under
  the PTL, then `folio_get()`; PMD path does `folio_get()`, drops the PTL,
  then `folio_lock()`.
- **Potentially unsafe usage**: sleeping in `folio_lock()` on a large folio
  while holding the reference taken for the split.
  - Unsafe: in a loop that retries on failure while other tasks do the same;
    each waiter's reference fails the lock holder's precheck in
    `__folio_split()` with `-EAGAIN`.
  - Safe: `folio_trylock()` under the PTL and back off without taking the
    reference, as `move_pages_pte()` in `mm/userfaultfd.c` does.
  - Safe: a single attempt with no retry, as the PMD path of
    `madvise_cold_or_pageout_pte_range()` does.
- **Potentially unsafe usage**: retrying on `-EBUSY`.
  - Unsafe: when nothing between tries changes the state tested by
    `folio_check_splittable()` or `filemap_release_folio()`.
  - Safe: after writeback has been waited for, as
    `s390_wiggle_split_folio()` does.
- After success: `move_pages_pte()` unlocks, puts and looks the folio up
  again from the PTE; the madvise PTE loops retake `pte_offset_map_lock()`
  and reprocess the same PTE.

## Deferred split

**Deferred split queue**

- There is no struct deferred_split, split_queue_lock, split_queue,
  split_queue_len, get_deferred_split_queue() or
  folio_split_queue_lock_irqsave() in this tree, and neither
  `struct mem_cgroup` nor `struct pglist_data` holds a deferred-split queue.
- The queue: one static `struct list_lru`, `deferred_split_lru` in
  `mm/huge_memory.c`, initialised memcg-aware by `thp_shrinker_init()`.
- A queued folio: linked by `_deferred_list` on one `struct list_lru_one`,
  chosen from `folio_nid()` and `folio_memcg()`; sublists are per memcg and
  per node.
- Root memcg, no memcg, or `mem_cgroup_kmem_disabled()` (see
  `__list_lru_init()`): the folio goes on the per-node `lru` of
  `struct list_lru_node`.
- Lock: the `lock` field of that `struct list_lru_one`; it also covers the
  setting and clearing of the partially-mapped flag.
- Sublist choice: redone from `folio_memcg()` on every queue and unqueue, in
  `lock_list_lru_of_memcg()` in `mm/list_lru.c`; it moves to the parent memcg
  when the memcg has no sublist or its sublist is marked dead.
  `deferred_split_isolate()` is the exception: the walk hands it the sublist.
- `deferred_split_folio()` and `__folio_unqueue_deferred_split()`: take the
  lock with `list_lru_lock_irqsave()` under `rcu_read_lock()`.
- `__folio_freeze_and_split_unmapped()`: takes it with plain
  `list_lru_lock()`; its callers have disabled IRQs.
- `deferred_split_folio()` returns without queueing for: order <= 1;
  `!partially_mapped` with `split_underused_thp` off; a folio in the
  swapcache.
- `deferred_split_folio()`: tests neither anon nor hugetlb; the anon test and
  the `folio_is_device_private()` exclusion are in `__folio_remove_rmap()`.
- hugetlb fields (`_hugetlb_subpool` and the rest) are in `__page_3` of
  `struct folio`; `_deferred_list` is in `__page_2`; they do not overlap.

**Allocation sites and the queue**

- `folio_memcg_alloc_deferred()` in `mm/huge_memory.c`: allocates the
  `deferred_split_lru` sublists (`struct list_lru_memcg`) for the folio's
  memcg and for each ancestor that lacks them, through
  `folio_memcg_list_lru_alloc()`; it changes nothing in the folio.
- Precondition: the folio is already charged, since the memcg comes from
  `folio_memcg()`.
- Precondition: sleepable context, since it allocates with `GFP_KERNEL`;
  in-tree callers run it before taking the page table lock.
- Returns 0 without allocating when `mem_cgroup_disabled()`, when the lru is
  not memcg-aware, or when the memcg already has sublists; the stub without
  `CONFIG_TRANSPARENT_HUGEPAGE` returns 0.
- Returns `-ENOMEM` on failure; callers treat that as a failed folio
  allocation, for example `alloc_anon_folio()` puts the folio and falls back
  to order 0.
- Orders: required for anon folios of order > 1; `alloc_anon_folio()` and
  `__swap_cache_alloc()` guard the call with `order > 1`;
  `vma_alloc_anon_folio_pmd()` and `collapse_huge_page()` call it
  unconditionally.
- Folio from a site that did not call it, in a memcg that has no sublists:
  `deferred_split_folio()` neither fails nor skips; it queues the folio on
  the sublist of the nearest ancestor that has one, in the end the per-node
  global list.
- The only signal: `VM_WARN_ON(!css_is_dying())` in
  `lock_list_lru_of_memcg()`, compiled in under `CONFIG_DEBUG_VM` only.
- **Unsafe usage**: charging and mapping a new anon folio of order > 1
  without calling `folio_memcg_alloc_deferred()`.
  - Unsafe: once the folio is queued on an ancestor's sublist, a later
    allocation of the memcg's own sublists makes
    `__folio_unqueue_deferred_split()` lock the memcg's sublist and run
    `__list_lru_del()` on an entry that sits on the ancestor's list.
  - Safe: charge, then call it, then map, as `vma_alloc_anon_folio_pmd()`
    does; `lock_list_lru_of_memcg()` defines the requirement.
  - Safe: folios produced by a split, when the site that allocated the
    original folio called it; `__split_folio_to_order()` copies
    `memcg_data`, so they stay in the memcg of the original folio.

**Queueing for deferred split**

- Queuers, complete list for this tree:

| Site | Condition | `partially_mapped` |
| --- | --- | --- |
| `__folio_remove_rmap()` | see next bullets | true |
| `map_anon_folio_pmd_nopf()` | every new PMD-mapped anon THP, while `split_underused_thp` is on | false |
| `migrate_folio_move()` | src was queued before the move | src's flag |
| `deferred_split_scan()` | requeue, see below | unchanged |

- `__do_huge_pmd_anonymous_page()` does not call `deferred_split_folio()`
  itself; fault paths and `collapse_huge_page()` reach it through
  `map_anon_folio_pmd_nopf()`.
- `collapse_huge_page()` below PMD order: maps with
  `map_anon_folio_pte_nopf()`, which does not queue.
- `__folio_remove_rmap()` test: partially mapped, anon,
  `!folio_test_partially_mapped()` and `!folio_is_device_private()`.
- A folio in the swapcache: the rmap test passes but
  `deferred_split_folio()` returns early; the folio is not queued and the
  flag stays clear.
- Partially mapped under `CONFIG_NO_PAGE_MAPCOUNT`: decided from the folio's
  total mapcount, not per page; at PTE level it means mapcount non-zero,
  below the folio's page count, and no entire mapping.
- PMD-level removal queues too: when the last entire mapping goes away and
  PTE mappings of some but not all pages remain.
- `deferred_split_scan()` requeues with `list_lru_add_irq()` when the split
  did not happen and the folio is partially mapped, or when
  `folio_trylock()` failed.
- Callers of the rmap helpers do nothing about the queue themselves; the
  final put unqueues (see "Leaving the deferred split queue").
- **Unsafe usage**: calling `folio_remove_rmap_ptes()` or
  `folio_remove_rmap_pmd()` on an anon large folio whose refcount is already
  zero or frozen.
  - Unsafe: `folio_unqueue_deferred_split()` tests `list_empty()` without the
    lock and assumes nobody adds once the refcount is zero; a late add leaves
    a freed folio on the queue.
  - Safe: remove the rmap first, then drop the mapping's reference, as
    `try_to_unmap_one()` does; the unqueue in `__folio_put()` and
    `folios_put_refs()` runs only after the last reference is gone.
- Code that replaces a folio: unqueue the old one while it is frozen and
  still charged, as `__folio_migrate_mapping()` does.
- The replacement folio: does not inherit the queue entry; only an explicit
  `deferred_split_folio()` call puts it there. `migrate_folio_move()` samples
  `_deferred_list` and the flag of src before `move_to_new_folio()`.
- No memcg charge-moving code exists in this tree.

**Leaving the deferred split queue**

- Refcount: must be zero, at the final put or frozen;
  `__folio_unqueue_deferred_split()` has
  `WARN_ON_ONCE(folio_ref_count(folio))`. Holding a reference is not an
  alternative.
- Why zero: a non-empty `_deferred_list` may be linked on the on-stack list
  of `deferred_split_scan()`, which no lock covers; the shrinker holds a
  reference on every folio on that list.
- Unqueue sites: every caller of `folio_unqueue_deferred_split()`, plus two
  that delete the entry directly, `__folio_freeze_and_split_unmapped()` and
  `deferred_split_isolate()`.
- `__folio_put()` and `folios_put_refs()` are in `mm/folio.c`; there is no
  mm/swap.c here.
- `free_unref_folios()`: does not unqueue; its callers do, for example
  `shrink_folio_list()` and `move_folios_to_lru()`.
- There is no folio_undo_large_rmappable() and no memcg1_swapout(); the
  swapout site is `__memcg1_swapout()` in `mm/memcontrol-v1.c`.
- `__folio_freeze_and_split_unmapped()`: takes the sublist lock before
  `folio_ref_freeze()`, for anon folios of order > 1 only, so the shrinker
  never sees the frozen folio on the list.
- `__folio_freeze_and_split_unmapped()` when the freeze fails: drops the
  lock, returns `-EAGAIN`, and the folio stays queued.
- `deferred_split_isolate()`: a folio whose `folio_try_get()` fails is
  removed from the queue and its partially-mapped flag cleared, not skipped.
- `deferred_split_scan()`: a folio that is not partially mapped and is
  mlocked or not underused is not requeued by the scan.
- Before the memcg changes: the entry must be off the queue while
  `memcg_data` is still set; `__folio_unqueue_deferred_split()` warns on
  `!folio_memcg_charged()` unless `mem_cgroup_disabled()`.
- `uncharge_folio()` and `mem_cgroup_migrate()`: the
  `WARN_ON_ONCE(folio_unqueue_deferred_split())` there is a check that runs
  just before `memcg_data` is cleared; the real unqueue must already have
  happened.
- `mem_cgroup_replace_folio()`: does not call the helper.
- Memcg offline: needs no unqueue; `memcg_reparent_list_lrus()` splices each
  sublist into the parent's and marks the old one dead.

## Collapse

**Collapse daemon structure**

- `khugepaged_enter_vma()`: registers when `MMF_VM_HUGEPAGE` is clear,
  `hugepage_enabled()` is true and `collapse_possible()` returns nonzero. There
  is no hugepage_pmd_enabled() in this tree.
- `collapse_possible()` on an anonymous VMA with `TVA_KHUGEPAGED`: asks for
  `THP_ORDERS_ALL_ANON`, so an mm is registered when any anonymous order is
  allowed for the VMA, not only PMD order.
- `hugepage_madvise()`: only edits the flags, does not call
  `khugepaged_enter_vma()`; `madvise_update_vma()` in `mm/madvise.c` does.
  `mm/shmem.c` has no call.
- `khugepaged_fork()`: when the parent has `MMF_VM_HUGEPAGE`, calls
  `__khugepaged_enter()` for the child, which allocates a new slot;
  `MMF_VM_HUGEPAGE` is not in `MMF_INIT_LEGACY_MASK`, so the flag is not
  inherited.
- Slot type: `struct mm_slot` from `mm_slot_alloc()`; there is no
  struct khugepaged_mm_slot.
- `__khugepaged_exit()` when the slot is the scan cursor: takes and releases
  `mmap_write_lock()` to wait for the daemon, frees nothing.
- `collect_mm_slot()`: frees the slot only when `collapse_test_exit()` sees
  `mm_users == 0`; it does not clear `MMF_VM_HUGEPAGE`.
- mm with `MMF_DISABLE_THP_COMPLETELY` or with no eligible VMA: the cursor moves
  past it, the slot stays on `khugepaged_scan.mm_head` until the mm exits.
- Function names in this tree; there is no khugepaged_scan_mm_slot(),
  hpage_collapse_scan_pmd(), hpage_collapse_scan_file() or
  hugepage_vma_check():

| Scope | Function |
|---|---|
| one mm | `collapse_scan_mm_slot()` |
| one PMD range, anon or file | `collapse_single_pmd()` |
| anon scan | `collapse_scan_pmd()` -> `mthp_collapse()` -> `collapse_huge_page()` |
| file scan | `collapse_scan_file()` -> `collapse_file()` |
| mm exiting | `collapse_test_exit()` |
| VMA filter | `collapse_possible()` |

- `collapse_scan_mm_slot()`: uses `mmap_read_trylock()`; on failure it moves
  the cursor to the next mm.
- `collapse_single_pmd()`: sends every non-anonymous VMA that passed
  `collapse_possible()` to `collapse_scan_file()`, shmem included;
  `madvise_collapse()` uses it too.

**File mappings eligible for collapse**

- `file_thp_enabled()` tests, in order: `vma->vm_file` set; not
  `IS_ANON_FILE()`; `mapping_pmd_folio_support()` on the mapping;
  `S_ISREG()`.
- Not tested: `inode_is_open_for_write()`, `VM_EXEC`, any config symbol.
- CONFIG_READ_ONLY_THP_FOR_FS, filemap_nr_thps_inc() and filemap_nr_thps():
  not in this tree. Opening a file for write does not drop its page cache, and
  `collapse_file()` has no writer recheck.
- `mapping_pmd_folio_support()` in `include/linux/pagemap.h`: true when
  `mapping_min_folio_order()` <= `PMD_ORDER` <= `mapping_max_folio_order()`. A
  non-shmem filesystem that has not set a folio order range reaching
  `PMD_ORDER` is never collapsed.
- Eligible regular files include files open for writing and writable
  mappings.
- `vma_can_map_huge_file()` in `mm/huge_memory.c`: runs
  `vma_file_check_thp_tuneables()` before `file_thp_enabled()`. The daemon needs
  `hugepage_global_always()`, or `hugepage_global_enabled()` with
  `VM_HUGEPAGE`; `TVA_FORCED_COLLAPSE` skips that test.
- Dirty or writeback folio of a non-shmem file: `collapse_file()` fails with
  `SCAN_PAGE_DIRTY_OR_WRITEBACK`; it calls `filemap_flush()` only when the inode
  is not open for write.
- MADV_COLLAPSE on that result: `collapse_single_pmd()` calls
  `filemap_write_and_wait_range()` and retries once, when
  `mapping_can_writeback()`.

**Collapse to smaller orders**

- mTHP collapse is in this tree; see `mthp_collapse()` in `mm/khugepaged.c`.
  There is no collapse_scan_bitmap() and no mthp_bitmap; the bitmap is
  `mthp_present_ptes` in `struct collapse_control`.
- `collapse_possible_orders()`: `THP_ORDERS_ALL_ANON` only for `TVA_KHUGEPAGED`
  on an anonymous VMA; MADV_COLLAPSE and file VMAs get PMD order only.
- `mthp_collapse()`: no stack. It walks an offset from 0 to `HPAGE_PMD_NR`; at
  each offset it tries the enabled orders downward, not below
  `KHUGEPAGED_MIN_MTHP_ORDER`, then advances by the size last tried and
  restarts at `max_order_from_offset()`.
- Attempt condition per order: occupied bits in the range >=
  `(1 << order) - collapse_max_ptes_none()`.
- `collapse_max_ptes_none()` below PMD order: `(1 << order) - 1` when the sysfs
  value equals `KHUGEPAGED_MAX_PTES_LIMIT`; 0 for every other value, with a
  `pr_warn_once()` if it was nonzero. There is no shift scaling.
- `collapse_max_ptes_none()` with a uffd-armed `vma`: 0. `mthp_collapse()`
  passes a NULL `vma`, so that rule applies in
  `__collapse_huge_page_isolate()`, and in `collapse_scan_pmd()` only when PMD
  order is the only enabled order.
- `collapse_scan_pmd()`: applies `collapse_max_ptes_swap()` and
  `collapse_max_ptes_shared()` for `HPAGE_PMD_ORDER` to the whole PMD. If
  either is exceeded the scan fails and no smaller order is tried.
- Swap PTEs: not set in `mthp_present_ptes`; `unmapped` is added to the occupied
  count only for the PMD-order attempt.
- Below PMD order, swap PTE inside the range: `__collapse_huge_page_swapin()`
  fails at the first one with `SCAN_EXCEED_SWAP_PTE` and swaps nothing in.
- Below PMD order, shared folio inside the range:
  `__collapse_huge_page_isolate()` fails with `SCAN_EXCEED_SHARED_PTE`.
- Below PMD order, folio in the range with `folio_order()` >= target order:
  `__collapse_huge_page_isolate()` returns `SCAN_PTE_MAPPED_HUGEPAGE`;
  `mthp_collapse()` skips to the next offset without trying a lower order.
- Result handling in `mthp_collapse()`: the `switch` lists which results try
  the next lower order; any result not listed, for example `SCAN_VMA_CHECK` or
  `SCAN_COPY_MC`, stops work on the whole PMD.
- `mthp_collapse()` return: `SCAN_SUCCEED` if any range collapsed.
- Counters: `count_collapse_event()` bumps the mTHP counter of the order it is
  given, `MTHP_STAT_COLLAPSE_EXCEED_NONE`, `MTHP_STAT_COLLAPSE_EXCEED_SWAP` or
  `MTHP_STAT_COLLAPSE_EXCEED_SHARED`, and the vm event only for PMD order.
  Below PMD order `__collapse_huge_page_swapin()` bumps
  `MTHP_STAT_COLLAPSE_EXCEED_SWAP` with `count_mthp_stat()` directly.

**Installing a smaller collapsed folio**

- `pmdp_collapse_flush()`: runs for every order; a smaller collapse also
  detaches the whole PTE table.
- Install order below PMD order: `pmd_populate()` re-installs the table first,
  then `map_anon_folio_pte_nopf()` writes the PTEs. The table is live while the
  PTEs are written.
- Locks for that install: PMD lock, with the PTE lock taken inside it by
  `spin_lock_nested()` and `SINGLE_DEPTH_NESTING` when the two differ;
  `map_anon_folio_pte_nopf()` calls `update_mmu_cache_range()`, which on MIPS
  (`__update_tlb()`) walks the page table from the pgd, so the table must be
  linked first.
- PMD-order install: `pgtable_trans_huge_deposit()`, then
  `map_anon_folio_pmd_nopf()` in `mm/huge_memory.c`, which also calls
  `deferred_split_folio()`.
- Write barrier: there is no explicit `smp_wmb()` in `collapse_huge_page()`;
  `__folio_mark_uptodate()` supplies it for both orders.
- `map_anon_folio_pte_nopf()` in `mm/memory.c`: adds `nr_pages - 1` folio
  references; the collapse passes `uffd_wp` false.
- anon_vma write lock below PMD order: held until after the install, because
  PTEs outside the range still map folios that rmap can reach.
- mmu notifier range: only the collapsed sub-range, with `MMU_NOTIFY_CLEAR`;
  the TLB flush in `pmdp_collapse_flush()` covers the whole PMD.
- `hugepage_vma_revalidate()`: is passed the PMD-aligned address and requires
  the whole PMD range inside the VMA for every order.

**Anonymous collapse locking**

- `collapse_huge_page()` entry: mmap_lock is not held. `collapse_scan_pmd()`
  calls `mmap_read_unlock()` before `mthp_collapse()` and sets `*lock_dropped`.
- mmap_lock after the swap-in stage: held for write until `out_up_write`; it is
  not downgraded.
- Write stage order: `hugepage_vma_revalidate()`, `vma_start_write()`,
  `check_pmd_still_valid()`, `anon_vma_lock_write()`.
- anon_vma write lock: released after isolation only for PMD order; for a
  smaller order it is held until `out_up_write`.
- `hugepage_vma_revalidate()`: checks `collapse_test_exit_or_disable()`, then
  `thp_vma_suitable_order()` with `PMD_ORDER` whatever the target order, then
  `thp_vma_allowable_orders()` for the target order, then, when `expect_anon`
  is true, `vma->anon_vma` and `vma_is_anonymous()`.
- `hugepage_vma_revalidate()` lookup: uses `find_vma()`, which can return a VMA
  above the address; the suitability test is what rejects it.
- `check_pmd_still_valid()`: compares the `pmd_t *` pointer from a new walk and
  the entry state; it does not compare the entry value with an earlier one.
- `__collapse_huge_page_swapin()`: called only when `unmapped` is nonzero.
- PTE lock for isolation: taken by `pte_offset_map_lock()` on the stack copy
  `_pmd`, since the real PMD is clear; dropped with `spin_unlock()` while the
  table stays mapped until `out_up_write`.
- `__collapse_huge_page_copy()`: holds no page table lock for the copy;
  `__collapse_huge_page_copy_succeeded()` takes the PTE lock per entry to clear
  it.
- Install below PMD order: PMD lock plus PTE lock nested inside; PMD order
  takes the PMD lock only.

**Collapse and lockless walkers**

- `tlb_remove_table_sync_one()`: an IPI broadcast only with
  `CONFIG_MMU_GATHER_RCU_TABLE_FREE`; an empty inline in
  `include/asm-generic/tlb.h` otherwise, where the TLB flush in
  `pmdp_collapse_flush()` is the only wait.
- x86: `arch/x86/Kconfig` selects `MMU_GATHER_RCU_TABLE_FREE` unconditionally,
  so the call is a real IPI there.
- Refcount test after the sync: `folio_expected_ref_count()` compared with
  `folio_ref_count()` in `__collapse_huge_page_isolate()`; there is no
  is_refcount_suitable().
- File paths `retract_page_tables()` and `try_collapse_pte_mapped_thp()`: call
  `pmdp_get_lockless_sync()` after `pmdp_collapse_flush()`, not
  `tlb_remove_table_sync_one()`.
- `pmdp_get_lockless_sync()` in `include/linux/pgtable.h`: empty unless
  `CONFIG_GUP_GET_PXX_LOW_HIGH` is set and `CONFIG_PGTABLE_LEVELS` > 2.
- Clearing PTEs in place under the PTE lock, PMD still set: needs no IPI;
  `try_collapse_pte_mapped_thp()` does it, and `gup_fast_pte_range()` rereads
  the PTE after taking its reference.
- **Potentially unsafe usage**: detaching a PTE table with
  `pmdp_collapse_flush()` and not calling `tlb_remove_table_sync_one()` before
  going on.
  - Unsafe: when the table is kept, deposited or re-installed, as an anonymous
    collapse does. A walker that entered before the clear can be reading the
    table when it is refilled, and `zap_deposited_table()` in
    `mm/huge_memory.c` frees a deposited table with `pte_free()`, with no grace
    period.
  - Safe: when the table is already empty and goes to `pte_free_defer()`, as
    `retract_page_tables()` does. `gup_fast_pte_range()` maps the table with
    `pte_offset_map()`, which holds `rcu_read_lock()` until `pte_unmap()`, and
    `pte_free_defer()` in `mm/pgtable-generic.c` frees through `call_rcu()`.

**File collapse and rollback**

- Old folios before commit: stay in their page cache slots, locked, isolated
  from the LRU, each with two references beyond the page cache's: the pin and
  the one from `folio_isolate_lru()`. `collapse_file()` does not call
  `folio_ref_freeze()`.
- Refcount test: `folio_ref_count()` must equal `2 + folio_nr_pages()`, checked
  once under `xas_lock_irq()`; a new mapping needs the folio lock after that,
  for example `folio_trylock()` in `next_uptodate_folio()`.
- `try_to_unmap()` result: not checked. A folio that is still mapped fails the
  refcount test with `SCAN_PAGE_COUNT`.
- xa_lock in the first loop: held for `folio_trylock()`, dropped for
  isolating, releasing and unmapping each folio, retaken for the refcount
  test.
- Non-shmem folio: must be clean before `folio_isolate_lru()` and again after
  `try_to_unmap()`, which moves PTE dirty bits to the folio.
- `nr_none`: counts shmem holes only. A hole in a regular file is filled by
  `page_cache_sync_readahead()` or the collapse fails.
- New folio before commit: locked, with `mapping` and `index` set, not in the
  xarray, not uptodate.
- Slots changed before commit: only shmem holes, set to `XA_RETRY_ENTRY`.
- Point of no return: after the hole recheck and the `userfaultfd_missing()`
  walk, with the xa_lock held; one multi-index `xas_store()` replaces all old
  entries.
- `folio_mark_dirty()` on the new folio: shmem only.
- Rolled back: retry entries back to NULL, `mapping->nrpages` and
  `shmem_uncharge()` for `nr_none`, old folios unlocked and put back on the
  LRU, new folio `mapping` cleared and freed. The xarray needs no other repair.
- Not rolled back: PTEs removed by `try_to_unmap()`, private data dropped by
  `filemap_release_folio()`, folios brought in by swap-in or readahead.
- filemap_nr_thps_inc() and filemap_nr_thps_dec(): not in this tree.
- Page tables, first: `try_to_unmap()` per old folio in the first loop, flushed
  by `try_to_unmap_flush()` before the copy.
- Page tables, second: `retract_page_tables()` after the store and before
  `folio_unlock()` of the new folio. It relies on that lock to keep faults from
  refilling the table.
- `file_backed_vma_is_retractable()`: skips a VMA with `anon_vma`, with
  `userfaultfd_protected()`, or with `VMA_MAYBE_GUARD_BIT`;
  `retract_page_tables()` calls it again under the PTE lock.
- MADV_COLLAPSE: `collapse_file()` turns success into
  `SCAN_PTE_MAPPED_HUGEPAGE`; `collapse_single_pmd()` then takes
  `mmap_read_lock()` and calls `try_collapse_pte_mapped_thp()` with
  `install_pmd` true.
- Daemon finding a PMD-order folio already in the cache:
  `collapse_scan_file()` returns `SCAN_PTE_MAPPED_HUGEPAGE` and
  `collapse_single_pmd()` calls `try_collapse_pte_mapped_thp()` with
  `install_pmd` false, which retracts the table in that mm only.

## Page cache and swap

**Page cache references**

- `filemap_free_folio()`: one unconditional
  `folio_put_refs(folio, folio_nr_pages(folio))`; no separate `folio_put()`
  path for a small folio, and no count argument.
- hugetlb folios: get `folio_nr_pages()` references too.
  `hugetlb_add_to_page_cache()` calls `__filemap_add_folio()`; `huge` there
  only skips the statistics.
- shmem folios: `__filemap_add_folio()` asserts `!folio_test_swapbacked()`.
  `shmem_add_to_page_cache()` takes the references and
  `shmem_delete_from_page_cache()` drops them at swap-out, in
  `shmem_writeout()`.
- There is no delete_from_page_cache() here. `filemap_free_folio()` is static
  in `mm/filemap.c`; its callers are `filemap_remove_folio()` and
  `delete_from_page_cache_batch()`.
- `filemap_remove_folio()`: removes and drops the references in one call.
  Nothing has to follow it.
- `__filemap_remove_folio()` called directly: drops no page cache reference.
  The caller does, for example `folio_unmap_invalidate()` in `mm/truncate.c`.
- `__remove_mapping()` in `mm/vmscan.c`: consumes the references in the freeze
  and returns the folio at refcount 0. `remove_mapping()` restores the caller's
  reference with `folio_ref_unfreeze(folio, 1)`.
- Folio still mapped at removal: `filemap_unaccount_folio()` has
  `VM_BUG_ON_FOLIO(folio_mapped(folio), folio)`. `truncate_cleanup_folio()` and
  `folio_unmap_invalidate()` call `unmap_mapping_folio()` first.
- **Unsafe usage**: one `folio_put()` for the page cache after removing a folio
  that may be large.
  - Safe: `folio_put_refs(folio, folio_nr_pages(folio))` after
    `__filemap_remove_folio()`, as `folio_unmap_invalidate()` does. It matches
    `folio_ref_add(folio, nr)` in `__filemap_add_folio()`.
  - Safe: no put at all after `__remove_mapping()` succeeded, as
    `remove_mapping()` does; the freeze took the references.

**Mapping past end of file**

- `finish_fault()`: maps the whole folio or exactly one PTE. A non-shmem folio
  that crosses `file_end` sets `needs_fallback`, which forces `nr_pages = 1`
  and skips `do_set_pmd()`. No partial range is mapped.
- `do_set_pmd()`, `filemap_map_pmd()`, `set_pte_range()`: make no `i_size`
  test. The tests are in `filemap_map_pages()`, `filemap_map_folio_range()`
  and `finish_fault()`.
- `file_end` differs by one between the two sites, with the same comparison
  against `folio_next_index()`:

| Site | `file_end` | Folio that ends exactly at the last page of the file |
|---|---|---|
| `finish_fault()` | `DIV_ROUND_UP(i_size, PAGE_SIZE)` | mapped whole, PMD allowed |
| `filemap_map_pages()`, `filemap_map_folio_range()` | that value minus 1 | no PMD, PTE range clamped |

- `filemap_map_folio_range()`: maps the whole folio by PTEs only when the same
  `file_end` test as the PMD case passes; otherwise it maps only the clamped
  range.
- `filemap_map_pages()`: reads `i_size` once, at entry. The only later read is
  in `next_uptodate_folio()`, once per folio after `folio_trylock()`, and it
  tests only the current index.
- `finish_fault()` test: applies to every VMA with `vm_file`, not only to
  mappings that use `filemap_fault()`.
- `shmem_mapping()`: the only exemption. Without `CONFIG_SHMEM` it is a stub
  that returns `false`, so nothing is exempt.
- There is no try_folio_split_or_unmap() or try_folio_split_to_order() here.
  `folio_split_or_unmap()` in `mm/truncate.c` calls `folio_split()` down to
  `mapping_min_folio_order()`.
- Failed split, non-shmem: `folio_split_or_unmap()` calls `try_to_unmap()` on
  the whole folio, so pages below the new EOF are unmapped too. It does not
  call `unmap_mapping_range()` or `unmap_mapping_folio()`.
- Failed split, shmem: `folio_split_or_unmap()` does not call
  `try_to_unmap()`.
- After a failed split, `truncate_inode_partial_folio()` decides by the dirty
  flag:
  - dirty: returns `false`; the folio stays in the page cache and
    `truncate_inode_pages_range()` skips it.
  - clean: `truncate_inode_folio()` removes the whole folio, including the
    part below the new EOF.
- Zeroing of the truncated part: skipped when `mapping_inaccessible()`.
- Successful split: `__folio_freeze_and_split_unmapped()` removes the
  after-split folios at or past `end` from the page cache. `end` comes from
  `i_size`, raised by `shmem_fallocend()` for shmem.

**Large folio swap-in**

- There is no alloc_swap_folio(), swapin_folio(), add_to_swap_cache(),
  __read_swap_cache_async() or SWAP_HAS_CACHE here. A cached slot is a folio
  entry in the swap table, tested with `swp_tb_is_folio()`.
- `swap_cache_alloc_folio()`: takes an `orders` mask, not one order. It
  returns a new folio or `ERR_PTR()`; never NULL, never an existing folio.
- New folio on return: locked, in the swap cache, memcg-charged, passed to
  `folio_add_lru()`, not uptodate. `folio->swap` is `targ_entry` rounded down
  to the folio size.
- Fallback is inside `swap_cache_alloc_folio()`: on `-EBUSY` or `-ENOMEM` it
  tries the next lower order set in `orders`.
- Order 0 is tried only if `BIT(0)` is in `orders`. `do_swap_page()` passes
  it; `shmem_swap_alloc_folio()` passes one order and retries with 0 itself.
- Errors from `swap_cache_alloc_folio()`:

| Error | Cause | Fallback |
|---|---|---|
| `-EEXIST` | target slot already has a folio | none, returned at once |
| `-ENOENT` | target slot has count 0, or cluster has no table | none |
| `-EBUSY` | another slot in the range fails the check | next order |
| `-ENOMEM` | allocation, memcg charge or `folio_memcg_alloc_deferred()` failed | next order |
| `-EINVAL` | `orders` is 0, or its highest order exceeds `SWAPFILE_CLUSTER` pages | none, with a warning |

- `__swap_cache_add_check()`: runs under `ci->lock`, before the allocation and
  again before the insert. Every slot needs a count, no folio, and the same
  zeromap bit as the target; the second run also needs the same memcg id.
- `swap_zeromap_batch()`: static in `mm/page_io.c`; callers of
  `swap_cache_alloc_folio()` do not use it.
- Memcg charge: made after the insert. On failure `__swap_cache_alloc()`
  removes the folio, restores the shadow and returns `-ENOMEM`.
- Page tables: `swap_cache_alloc_folio()` checks the swap table only.
  `thp_swapin_suitable_orders()` filters `orders` by the PTEs beforehand.
- `SWP_SYNCHRONOUS_IO`: there is no swap cache bypass. The flag selects
  `swapin_sync()`, which skips readahead and allows large orders.
  `swap_cache_read_folio()` always passes `BIT(0)`.
- `swapin_sync()`: returns `ERR_PTR()` on failure, and NULL without
  `CONFIG_SWAP`. `swapin_readahead()` returns NULL on failure.
- `swapin_sync()` result: may be an older swap cache folio, unlocked and of
  any order. Take the size from the folio, as `shmem_swapin_folio()` does
  with `shmem_split_large_entry()`.
- After locking the folio: `folio_matches_swap_entry()` is required, as in
  `do_swap_page()` and `shmem_swapin_folio()`.
- Fresh large folio whose PTEs changed: `do_swap_page()` does not map part of
  it. It calls `swap_cache_del_folio()` and returns for a retry.
- Swap device: must be pinned across the call, for example with
  `get_swap_device()`; `__swap_offset_to_cluster()` has only a
  `VM_WARN_ON_ONCE()` for a device with no users.
- **Unsafe usage**: reading swap data into a folio that is not in the swap
  cache.
  - Safe: `swap_cache_alloc_folio()` then `swap_read_folio()`, as
    `swapin_sync()` does. `swap_read_folio()` takes the slot from
    `folio->swap`, and `zswap_load()` warns if the folio is not swap cache.
- **Unsafe usage**: a large order in `orders` once zswap has been enabled.
  `zswap_load()` warns, unlocks and leaves the folio not uptodate, which gives
  `VM_FAULT_SIGBUS` in `do_swap_page()`.
  - Safe: order 0 only when `!zswap_never_enabled()`, as
    `thp_swapin_suitable_orders()` and `shmem_swap_alloc_folio()` do.
- **Unsafe usage**: leaving a new folio from `swap_cache_alloc_folio()` in the
  swap cache without reading into it. `do_swap_page()` returns
  `VM_FAULT_SIGBUS` for a folio that is not uptodate.
  - Safe: `swap_cache_del_folio()`, `folio_unlock()`, `folio_put()`, as the
    error path of `zswap_writeback_entry()` does.

## Hugetlb folios and the pool

**Hugetlb in generic code**

- `try_to_unmap()` in `mm/rmap.c`: installs
  `try_to_unmap_poisoned_hugetlb_one()` as the callback for a hugetlb folio;
  `try_to_unmap_one()` is not reached with one.
- `try_to_unmap_one()`: its hwpoison and unmap paths use `set_pte_at()`,
  `dec_mm_counter()` and `folio_remove_rmap_ptes()`, so a new caller must go
  through `try_to_unmap()`.
- `try_to_unmap_poisoned_hugetlb_one()`: expects `TTU_HWPOISON` and a
  hwpoisoned folio, and calls `page_vma_mapped_walk()` once, not in a loop.
- `try_to_migrate_one()`: still handles hugetlb inline, branching on
  `folio_test_hugetlb()`.
- `page_vma_mapped_walk()`: both callbacks use it; for a hugetlb VMA it
  returns the one entry in `pvmw.pte` under `huge_pte_lock()`.
- Hugetlb VMA lock in the callbacks: `hugetlb_vma_trylock_write()`, only for
  a non-anon folio and only around `huge_pmd_unshare()`; it is dropped before
  the entry is cleared.
- `huge_pmd_unshare()`: takes a `struct mmu_gather *` first; the callbacks
  bracket it with `tlb_gather_mmu_vma()` and `tlb_finish_mmu()`.
- `huge_pmd_unshare()` returning 1: the callback calls
  `huge_pmd_unshare_flush()` and ends the walk; `huge_pmd_unshare_flush()`
  asserts `i_mmap_rwsem` is still write-held.
- Clearing the entry: `huge_ptep_clear_flush()`; the callbacks call neither
  `huge_ptep_get_and_clear()` nor `flush_hugetlb_tlb_range()`.
- `hugetlb_folio_mapping_lock_write()`: a trylock on `i_mmap_rwsem`; it
  returns NULL on contention and the caller must give up.
- `remove_migration_ptes()`: must get the same `TTU_RMAP_LOCKED`, so that it
  uses `rmap_walk_locked()` while the caller still holds `i_mmap_rwsem`.
- There is no unmap_and_move_huge_page() here;
  `unmap_and_move_hugetlb_folio()` in `mm/migrate.c` does that.
- **Unsafe usage**: `try_to_migrate()` or `try_to_unmap()` on a non-anon
  hugetlb folio without `i_mmap_rwsem` write-held and `TTU_RMAP_LOCKED`.
  - Safe: take `hugetlb_folio_mapping_lock_write()` on the locked folio and
    pass `TTU_RMAP_LOCKED`, as `unmap_and_move_hugetlb_folio()` and
    `unmap_poisoned_folio()` do; `__huge_pmd_unshare()` asserts the lock.
  - Safe: an anon hugetlb folio needs neither; both callbacks skip the
    unshare when `folio_test_anon()` is true.

**Testing for hugetlb**

- `page_is_unmovable()` in `mm/page_isolation.c`: holds neither
  `hugetlb_lock` nor a reference.
- `page_is_unmovable()`: calls `size_to_hstate(PAGE_SIZE << order)`, with
  `order` read once by `compound_order()` and rejected above
  `MAX_FOLIO_ORDER`; a NULL hstate counts as unmovable.
- Setting the type: `init_new_hugetlb_folio()` calls `__folio_set_hugetlb()`
  without `hugetlb_lock`, on a frozen folio not yet in a pool.
- Clearing the type: every `__folio_clear_hugetlb()` call is under
  `hugetlb_lock`, so a positive test stays positive while the lock is held.
- `remove_hugetlb_folio()`: clears the type itself unless the folio is
  vmemmap-optimised; an optimised folio keeps it until after its vmemmap is
  restored, for example in `__update_and_free_hugetlb_folio()`.
- Under `hugetlb_lock`, type set and refcount 0: the folio is in the pool
  only if `HPG_freed` is set; otherwise it is being allocated or freed.
- `HPG_freed` clear with refcount 0: `dissolve_free_hugetlb_folio()` and
  `alloc_and_dissolve_hugetlb_folio()` drop the lock and retry.
- Taking a reference from a PFN: `folio_isolate_hugetlb()` and
  `get_hwpoison_hugetlb_folio()` do it under `hugetlb_lock`, after testing the
  type and `HPG_migratable`; `get_hwpoison_hugetlb_folio()` does not need
  `HPG_migratable` when `unpoison` is true. There is no
  isolate_hugetlb() here.
- After the reference is taken: recheck `page_folio(page)`, because demotion
  can change the folio; see `__get_hwpoison_page()` and `do_migrate_range()`.
- Lockless reads of `HPG_*` flags: usable as a hint only;
  `scan_movable_pages()` in `mm/memory_hotplug.c` bounds `folio_nr_pages()`
  and lets the caller revalidate.
- **Unsafe usage**: `folio_hstate()` on a folio after `remove_hugetlb_folio()`.
  - Safe: carry `h` from before the removal, as `free_huge_folio()` does when
    it calls `update_and_free_hugetlb_folio()`; `folio_hstate()` asserts the
    type with `VM_BUG_ON_FOLIO()`.
  - Safe: `size_to_hstate(folio_size(folio))`, as `free_hpage_workfn()` does.

**Freeing a hugetlb folio**

- Surplus test in `free_huge_folio()`: only that
  `h->surplus_huge_pages_node[nid]` is non-zero for the folio's node; it does
  not test whether this folio was allocated as surplus.
- Reservation: restored by `h->resv_huge_pages++` in `free_huge_folio()`
  under `hugetlb_lock`, not by a call to `hugetlb_acct_memory()`.
- Subpool pointer: in `folio->_hugetlb_subpool`; only the `HPG_*` flags are
  in `folio->private`.
- `HPG_raw_hwp_unreliable`: `__update_and_free_hugetlb_folio()` returns
  without freeing such a folio, after the counters have dropped it, so it
  reaches neither the pool nor the allocator.
- Waiting for the deferred free: `wait_for_freed_hugetlb_folios()`, as
  `test_pages_isolated()` does, or `flush_free_hpage_work()` inside
  `mm/hugetlb.c`.

**Surplus adjustment**

- `remove_hugetlb_folio()`: decrements `free_huge_pages` only if the folio
  has `HPG_freed`; `add_hugetlb_folio()` always increments it.
- Exact undo: `dissolve_free_hugetlb_folio()` passes its own
  `adjust_surplus` to both calls, and `demote_pool_huge_page()` passes
  `false` to both.
- Failed free: `__update_and_free_hugetlb_folio()` and
  `bulk_vmemmap_restore_error()` pass `true`, whatever the removal passed.
- Failed free with `true`: the folio becomes a free surplus page, and
  `persistent_huge_pages()` stays as the remover left it.
- `set_max_huge_pages()`: does not call `add_hugetlb_folio()` itself; it
  reaches `bulk_vmemmap_restore_error()` through
  `update_and_free_pages_bulk()`.
- `add_hugetlb_folio()`: asserts that the folio is still vmemmap-optimised,
  so it serves only as the rollback of a failed vmemmap restore.
- **Unsafe usage**: `remove_hugetlb_folio()` with `adjust_surplus` true while
  `h->surplus_huge_pages_node[nid]` is zero; the unsigned counter wraps.
  - Safe: test the per-node counter under `hugetlb_lock` first, as
    `free_huge_folio()` and `remove_pool_hugetlb_folio()` do.

**Pool counter invariants**

- `add_hugetlb_folio()`: does not change the refcount; the folio must already
  be at 0, which `enqueue_hugetlb_folio()` asserts.
- `account_new_hugetlb_folio()`: increments only `nr_huge_pages` and
  `nr_huge_pages_node[nid]`; the caller enqueues the folio or raises the
  surplus counters in the same hold of `hugetlb_lock`, except for a folio it
  marks `HPG_temporary`, as `alloc_migrate_hugetlb_folio()` does.
- `max_huge_pages`: the helpers do not touch it; callers adjust it, for
  example `dissolve_free_hugetlb_folio()` only when `adjust_surplus` is false.
- **Unsafe usage**: `remove_hugetlb_folio()` then an `add_hugetlb_folio()`
  rollback on an hstate for which `hstate_is_gigantic_no_runtime()` is true;
  the removal is a no-op, so the add-back reinitialises `folio->lru` while
  the folio is still on the free list.
  - Safe: test `hstate_is_gigantic_no_runtime()` in `mm/hugetlb_internal.h`
    first, as `dissolve_free_hugetlb_folio()` does.
  - Safe: `demote_pool_huge_page()` has no test of its own;
    `hugetlb_init_hstates()` leaves `demote_order` 0 for such an hstate, and
    `demote_pool_huge_page()` returns `-EINVAL` when `demote_order` is 0.

**Hugetlb demotion**

- Copied explicitly: `HPG_cma`, with `folio_set_hugetlb_cma()` on every new
  folio; `HPG_vmemmap_optimized` is not copied.
- Vmemmap: restored on the source by `hugetlb_vmemmap_restore_folios()`
  first; the new folios are optimised again in
  `prep_and_add_allocated_folios()`.
- `HPG_cma` missing on a new folio: `__update_and_free_hugetlb_folio()` calls
  `free_frozen_pages()` on CMA memory instead of
  `hugetlb_cma_free_frozen_folio()`.
- `init_new_hugetlb_folio()`: takes only the folio; it sets the type, the
  list head, a NULL subpool and NULL cgroups, and writes neither
  `folio->private` nor the refcount.
- There is no prep_and_add_hugetlb_folios() here;
  `prep_and_add_allocated_folios()` adds the new folios to the pool.
- Source folio whose restore failed: `demote_free_hugetlb_folios()` skips it
  and leaves it on the list; see "Surplus adjustment" for the add-back.

**Hugetlb vmemmap optimisation**

- Head vmemmap page after optimisation: a newly allocated copy, mapped
  read-write; it holds the first `HUGETLB_VMEMMAP_RESERVE_PAGES` struct pages.
- Every other vmemmap page of the folio: mapped `PAGE_KERNEL_RO` onto one
  shared page per zone and order, `vmemmap_tails[]` in `struct zone`.
- Shared tail page: filled by `init_compound_tail()` with a NULL head, so it
  carries node, zone and the tail marker, and no state of any one folio.
- `compound_head()` on such a tail: still finds the right head, because
  `compound_info` holds a mask when `compound_info_has_mask()` is true.
- Not in this tree: fake head pages, a static key for the optimisation, and
  RCU synchronisation in optimise or in the refcount helpers.
- Fields hugetlb keeps in tail pages, such as `_hugetlb_subpool`: stay
  writable; `hugetlb_vmemmap_init()` checks `__NR_USED_SUBPAGE` against
  `HUGETLB_VMEMMAP_RESERVE_PAGES` at build time.
- `hugetlb_vmemmap_optimize_folio()`: returns void and can leave the folio
  unoptimised; test `folio_test_hugetlb_vmemmap_optimized()` per folio.
- `vmemmap_optimize_enabled`: a runtime sysctl, so one pool can hold
  optimised and unoptimised folios.
- `hugetlb_vmemmap_restore_folio()`: expects the hugetlb type set and
  refcount 0, and returns 0 for a folio that is not optimised.
- Restore allocation: `GFP_KERNEL | __GFP_RETRY_MAYFAIL` on the folio's node,
  in `alloc_vmemmap_page_list()`; `__GFP_THISNODE` is not set.
- **Potentially unsafe usage**: reading a tail struct page of an optimised
  hugetlb folio.
  - Unsafe: for per-page state such as `PG_hwpoison`, refcount or
    `private`; past the first `HUGETLB_VMEMMAP_RESERVE_PAGES` struct pages
    the read returns the shared page's value.
  - Safe: for node, zone or the head lookup, which `init_compound_tail()`
    sets; `hugetlb_bootmem_init_migratetype()` passes such tail pages on.
  - Safe: for a poisoned subpage, ask `is_raw_hwpoison_page_in_hugepage()`,
    which reads the list that `hugetlb_update_hwpoison()` fills, as
    `adjust_range_hwpoison()` in `fs/hugetlbfs/inode.c` does.

## Hugetlb reservations

**Hugetlb allocation functions**

- `hugetlb_alloc_folio()` in `mm/hugetlb.c`: the VMA-less core of
  `alloc_hugetlb_folio()`, which is its only caller.
- `hugetlb_alloc_folio()`: has no stub without `CONFIG_HUGETLB_PAGE` in
  `include/linux/hugetlb.h`.

| Function | Reservations | Cgroup | Pool counters |
|---|---|---|---|
| `alloc_hugetlb_folio()` | reserve map, subpool, `hugetlb_set_folio_subpool()`; turns `map_chg` and `gbl_chg` into `alloc_flags` | charges nothing itself | none itself; `hugetlb_acct_memory()` only on the failure and race paths |
| `hugetlb_alloc_folio()` | no reserve map, no subpool; `resv_huge_pages--` and restore-reserve flag only with `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS` | hugetlb cgroup usage and `mem_cgroup_charge_hugetlb()` always; rsvd only with `HUGETLB_ALLOC_CHARG_CGROUP_RSVD` | `dequeue_hugetlb_folio()`, else surplus via `alloc_buddy_hugetlb_folio()` |
| `alloc_hugetlb_folio_nodemask()` | dequeues only if `available_huge_pages()` | none | fallback `alloc_migrate_hugetlb_folio()`: `nr_huge_pages` only, `HPG_temporary`, not surplus |
| `alloc_hugetlb_folio_reserve()` | `resv_huge_pages--`; sets neither the restore-reserve flag nor the folio's subpool | none | dequeue only |
| `alloc_surplus_hugetlb_folio()` | none | none | `account_new_hugetlb_folio()` and `surplus_huge_pages++` itself, under `hugetlb_lock`; NULL once `surplus_huge_pages` reaches `nr_overcommit_huge_pages` |
| `alloc_fresh_hugetlb_folio()` | none | none | none; the caller calls `account_new_hugetlb_folio()` under `hugetlb_lock` |
| `alloc_pool_huge_folio()` | none | none | none; `prep_and_add_allocated_folios()` accounts and enqueues |

- dequeue_hugetlb_folio_vma(), alloc_buddy_hugetlb_folio_with_mpol() and
  prep_new_hugetlb_folio(): not in this tree.
- `hugetlb_alloc_folio()` with `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS`:
  dequeues even when `available_huge_pages()` is 0; if dequeue returns NULL,
  the surplus folio still gets the flag and the `resv_huge_pages--`.
- `hugetlb_alloc_folio()` without that flag: dequeues only if
  `available_huge_pages()` is non-zero; the test is in its own body.
- Pool growth in `set_max_huge_pages()`: uses `alloc_pool_huge_folio()`, not
  `alloc_fresh_hugetlb_folio()`.
- `alloc_hugetlb_folio()` and `hugetlb_alloc_folio()` in `mm/hugetlb.c`:
  return `ERR_PTR()` on failure, never NULL.
- `alloc_hugetlb_folio_nodemask()` and `alloc_hugetlb_folio_reserve()`: return
  NULL on failure.
- `alloc_hugetlb_folio_reserve()` user `memfd_alloc_folio()`: sets the folio's
  subpool itself, after `hugetlb_add_to_page_cache()`.

**Reservation bookkeeping**

- Shared `struct resv_map`: lives in `struct hugetlbfs_inode_info`, reached
  with `inode_resv_map()`; nothing in hugetlb uses the mapping's private
  pointer for it.
- Child VMA of a private mapping after fork: `hugetlb_dup_vma_private()`
  clears `vm_private_data`, so it has no reserve map and no flags.
- `HPAGE_RESV_UNMAPPED`: set by `__unmap_hugepage_range()` when it is passed a
  specific folio, as `unmap_ref_private()` does; `hugetlb_no_page()` then
  fails the fault.
- VMA with no reserve map: `__vma_reservation_common()` returns 1 for every
  mode and touches nothing.
- Private mapping: a map entry means the reservation was consumed, and
  `__vma_reservation_common()` inverts the region result (>0 becomes 0, 0
  becomes 1).
- `vma_del_reservation()`: the exception; it returns the raw region result for
  private mappings too.
- Pending add from `vma_needs_reservation()`: completed by any one of
  `vma_commit_reservation()`, `vma_end_reservation()`,
  `vma_add_reservation()` or `vma_del_reservation()`.
- `resv_map_release()`: has `VM_BUG_ON()` on a non-zero `adds_in_progress`.
- `map_chg_state`: a typedef with no enum tag; values `MAP_CHG_REUSE`,
  `MAP_CHG_NEEDED`, `MAP_CHG_ENFORCED`.
- `MAP_CHG_ENFORCED`: set when `cow_from_owner` is true; the reserve map is
  not consulted, and neither commit nor end runs.
- `map_chg != MAP_CHG_REUSE` in `alloc_hugetlb_folio()`: sets
  `HUGETLB_ALLOC_CHARG_CGROUP_RSVD`.
- `hugetlb_reserve_pages()`: returns `chg` (>= 0) on success and a negative
  errno on failure; callers test `< 0`.

**Subpool accounting**

- `hugetlb_reserve_pages()` when `hugetlb_acct_memory()` fails: puts back only
  `chg - gbl_reserve`, and passes that put's return, negated, to
  `hugetlb_acct_memory()`.
- Same path, the remaining `gbl_reserve` pages: `used_hpages` is lowered
  directly under `spool->lock`, then `unlock_or_release_subpool()`; they do
  not go through `hugepage_subpool_put_pages()`.
- `hugetlb_reserve_pages()` reserve-map unwind: `region_abort()` for shared;
  for private, `kref_put()` of the map and `set_vma_resv_map()` to NULL.
  `hugetlb_reserve_pages()` itself does not call `region_del()`.
- `free_huge_folio()`: does not pass the put's return to
  `hugetlb_acct_memory()`; a put return of 0 makes it do `resv_huge_pages++`.
- **Potentially unsafe usage**: passing the negated return of
  `hugepage_subpool_get_pages()` to `hugetlb_acct_memory()`.
  - Unsafe: when the same pages also go back through
    `hugepage_subpool_put_pages()`; with a minimum size the put can return
    less than the get did, and `return_unused_surplus_pages()` subtracts
    whatever it is given from `resv_huge_pages`.
  - Safe: to reverse an earlier successful `hugetlb_acct_memory()` of that
    same value, with only `chg - gbl_reserve` going through the put, as
    `hugetlb_reserve_pages()` does when `region_add()` fails.
  - Safe: put first, then pass its negated return, as
    `hugetlb_unreserve_pages()` and `hugetlb_vm_op_close()` do;
    `hugepage_new_subpool()` charged `min_hpages` globally, so pages that
    refill `rsv_hpages` stay reserved.

**Restoring a reservation**

- Flag set at allocation: in `hugetlb_alloc_folio()`, under
  `HUGETLB_ALLOC_USE_GLOBAL_RESERVATIONS`; `alloc_hugetlb_folio()` passes that
  flag when `gbl_chg == 0`.
- Flag set at unmap: `__unmap_hugepage_range()` sets it when the folio is anon
  and no longer mapped, `__vma_private_lock()` is true and
  `h->surplus_huge_pages` is 0.
- Same unmap path: it then calls `vma_needs_reservation()` and clears the flag
  again if that fails.
- Flag cleared on instantiation: inside `hugetlb_add_new_anon_rmap()` in
  `mm/rmap.c`, and in `hugetlb_add_to_page_cache()` on success only.
- `free_huge_folio()` with the flag set: does `resv_huge_pages++` and skips
  `hugepage_subpool_put_pages()`.
- `restore_reserve_on_error()` with the flag set: `vma_add_reservation()` if
  the map shows no reservation, `vma_end_reservation()` if it shows one; it
  clears the flag if `vma_needs_reservation()` fails.
- `restore_reserve_on_error()` with the flag clear: `vma_del_reservation()` if
  the map shows a reservation, `vma_end_reservation()` if not.
- Flag clear and a map call fails: it sets the flag when
  `vma_del_reservation()` fails, and for a private mapping when
  `vma_needs_reservation()` fails.
- Failure inside `hugetlb_alloc_folio()` after the flag is set (memcg charge):
  it calls `free_huge_folio()` itself, and `alloc_hugetlb_folio()` ends the
  pending add; `restore_reserve_on_error()` is not needed there.
- **Potentially unsafe usage**: calling `restore_reserve_on_error()` without
  the hugetlb fault mutex for that index.
  - Unsafe: when the VMA has a reserve map; another `alloc_hugetlb_folio()`
    at the same index can change the entry between the allocation and the
    restore.
  - Safe: under the mutex, which `hugetlb_fault()` takes before it
    allocates, as `hugetlb_no_page()`, `hugetlb_wp()`,
    `hugetlb_mfill_atomic_pte()` and `hugetlbfs_fallocate()` do.
  - Safe: on the child VMA of a private mapping in
    `copy_hugetlb_page_range()`; `hugetlb_dup_vma_private()` left it no
    reserve map, so every reserve-map call returns 1 and changes nothing.

## Hugetlb faults and page tables

**Fault path lock order**

- `unmap_ref_private()`: takes `i_mmap_lock_write()` itself; nothing else in
  `hugetlb_wp()` takes `i_mmap_rwsem`, and `hugetlb_wp()` takes no folio
  lock.
- Anon folio under a present PTE: locked only by `hugetlb_fault()`, with
  `folio_trylock()`, only when `folio_test_anon()` is true, and after
  `huge_pte_lock()`.
- File folio under a present PTE: enters `hugetlb_wp()` unlocked, despite the
  comment above `hugetlb_wp()`.
- Page cache folio in `hugetlb_no_page()`: locked before the page table lock,
  unlocked before the `hugetlb_wp()` call.
- `hugetlb_wp()`, `cow_from_owner` path: the anon folio lock stays held while
  the mutex and VMA lock are dropped, so `i_mmap_rwsem` is taken for write
  under a folio lock, the reverse of the hugetlbfs order listed in
  `mm/rmap.c`.
- Userfaultfd RWP branch in `hugetlb_fault()` (protnone PTE with
  `huge_pte_uffd()`): sync mode returns through `hugetlb_handle_userfault()`
  with `VM_UFFD_RWP`, dropping VMA lock and mutex; async mode takes only the
  page table lock.

**Hugetlb VMA lock**

- Private mapping: has a lock only if `__vma_private_lock()` is true, which
  needs a reservation map pointer and `HPAGE_RESV_OWNER`.
- Private VMA without `HPAGE_RESV_OWNER`, such as a child after fork: no lock;
  every lock helper returns without doing anything.
- Shared VMA at final unmap: `__hugetlb_zap_end()` with `ZAP_FLAG_UNMAP` calls
  `__hugetlb_vma_unlock_write_free()`, which clears `vm_private_data` before
  `i_mmap_rwsem` is dropped; from then on the VMA has no lock.

**Walking hugetlb page tables**

- `huge_pte_lockptr()` in `include/linux/hugetlb.h` chooses by huge page size:

| Size | Lock |
|---|---|
| >= `PUD_SIZE` | `pud_lockptr()` |
| >= `PMD_SIZE`, or `CONFIG_HIGHPTE` | `pmd_lockptr()` |
| smaller | `ptep_lockptr()` |

- Hugetlb VMA lock: `hugetlb_fault()` holds it in addition to `mmap_lock` or
  the per-VMA lock, not instead of them; rmap walkers such as
  `try_to_migrate_one()` hold it with `i_mmap_rwsem` and without `mmap_lock`.
- `hugetlb_split()`: unshares without the hugetlb VMA lock; it asserts
  `vma_assert_write_locked()` and `i_mmap_assert_write_locked()` instead.
- `i_mmap_rwsem`: `__huge_pmd_unshare()` reaches `pud_clear()` only after
  `i_mmap_assert_write_locked()`; the comment above `huge_pte_offset()` in
  `include/linux/hugetlb.h` says a holder is not protected from unsharing.
- Private mapping: `hugetlb_wp()` calls `hugetlb_walk()` under the per-VMA
  lock too; `hugetlb_fault()` calls `vma_end_read()` on `VM_FAULT_RETRY`.
- **Potentially unsafe usage**: using a `pte_t *` from `hugetlb_walk()` after
  the hugetlb VMA lock was dropped.
  - Unsafe: on a VMA that passes `__vma_shareable_lock()`, when
    `i_mmap_rwsem` is not held either; the PUD can be cleared and the pointer
    is into a table this mm no longer maps.
  - Safe: while `i_mmap_rwsem` is still held, which `__huge_pmd_unshare()`
    asserts write-held, as `try_to_migrate_one()` does after
    `hugetlb_vma_unlock_write()`.
  - Safe: on a VMA without `VM_MAYSHARE`, which `want_pmd_share()` never
    shares; `hugetlb_wp()` drops the lock around `unmap_ref_private()` there,
    then walks again and compares with `pte_same()`.

**PMD table sharing**

- Sharer count: `pt_share_count`, an `atomic_t` in `struct ptdesc`, not the
  page refcount; 0 means not shared, see `ptdesc_pmd_is_shared()`.
- `huge_pmd_share()`: takes `i_mmap_lock_read()` itself and holds it until
  after `pmd_alloc()`.
- `hugetlb_fault()` as caller: holds the fault mutex and the hugetlb VMA lock
  for read, not `i_mmap_rwsem`.
- `want_pmd_share()` and `page_table_shareable()`: both require
  `vm_private_data` to be set.
- `page_table_shareable()`: compares `vm_flags` with `VM_LOCKED_MASK` masked
  out.
- `uffd_disable_huge_pmd_share()`: true for `VMA_UFFD_WP`, `VMA_UFFD_RWP` or
  `VMA_UFFD_MINOR`.
- There is no vma_shareable() here; the tests are inline in
  `want_pmd_share()`, built under `CONFIG_HUGETLB_PMD_PAGE_TABLE_SHARING`.

**Unsharing a PMD table**

- `tlb_unshare_pmd_ptdesc()` in `include/asm-generic/tlb.h`: does the count
  decrement, adds the `PUD_SIZE` range to the gather and sets
  `unshared_tables`; `huge_pmd_unshare()` itself only clears the PUD and
  calls `mm_dec_nr_pmds()`.
- Left to the caller: `huge_pmd_unshare_flush()` before `i_mmap_rwsem` is
  dropped.
- `huge_pmd_unshare_flush()`: asserts only `i_mmap_assert_write_locked()`.
- Hugetlb VMA lock and page table lock: not needed for the flush.
- `__huge_pmd_unshare()` assertions: run only when the size is `PMD_SIZE` and
  the table is shared, so lockdep is silent about a missing lock otherwise.
- `hugetlb_vma_assert_locked()`: `lockdep_assert_held()`, so read mode passes.
- `hugetlb_split()`: unshares with `check_locks` false, without the hugetlb
  VMA lock.
- Page table lock: required by the kerneldoc of `huge_pmd_unshare()`;
  nothing asserts it.
- `try_to_unmap_one()` does not call `huge_pmd_unshare()`; in `mm/rmap.c`
  `try_to_unmap_poisoned_hugetlb_one()` and `try_to_migrate_one()` do.
- **Unsafe usage**: calling `huge_pmd_unshare_flush()` after
  `i_mmap_rwsem` was dropped, or leaving the flush to `tlb_finish_mmu()`,
  which has `VM_WARN_ON_ONCE()` on `fully_unshared_tables`.
  - Safe: dropping the hugetlb VMA lock before the flush while
    `i_mmap_rwsem` stays held for write, as `try_to_migrate_one()` does;
    `huge_pmd_unshare_flush()` asserts only `i_mmap_rwsem`.
  - Safe: dropping the page table lock before the flush, as
    `__unmap_hugepage_range()` does; `huge_pmd_unshare_flush()` does not
    assert it.

**Unsharing and lockless walkers**

- Unsharing frees no table and records no table in the `struct mmu_gather`;
  it records a range and the flags `unshared_tables` and
  `fully_unshared_tables`.
- The wait: `tlb_remove_table_sync_one()` in `tlb_flush_unshared_tables()`,
  called from `huge_pmd_unshare_flush()`, after the TLB flush.
- Condition for the IPI: `fully_unshared_tables`, set by
  `tlb_unshare_pmd_ptdesc()` only when its decrement left the table unshared.
- `tlb_flush_mmu_tlbonly()` before `huge_pmd_unshare_flush()`, as in
  `hugetlb_change_protection()`: `__tlb_reset_range()` clears
  `unshared_tables` but not `fully_unshared_tables`, so the IPI is still sent.

**Folio lock under fault mutex**

- The lock holder that matters: `hugetlb_wp()` on the `cow_from_owner` path
  keeps the anon folio locked while it drops and retakes the fault mutex.
- `cow_from_owner`: set only when `folio_test_anon(old_folio)`, so only anon
  folios are ever locked across that window.
- `hugetlb_no_page()`: unlocks a page cache folio before it calls
  `hugetlb_wp()`; a new anon folio stays locked.
- **Potentially unsafe usage**: a blocking folio lock while the fault mutex
  is held.
  - Unsafe: on an anon folio that is already mapped; the sleeper holds the
    mutex that `hugetlb_wp()` needs to retake before it can unlock.
  - Safe: on a page cache folio, as `hugetlb_no_page()` and
    `remove_inode_single_folio()` do; `hugetlb_wp()` never drops the mutex
    for a folio that is not anon.
  - Safe: on a new anon folio not yet mapped, as `hugetlb_no_page()` does;
    the `cow_from_owner` path of `hugetlb_wp()` only runs on a folio found
    under a present PTE.

**Hugetlb copy-on-write**

- Reuse test in a VMA without `VM_MAYSHARE`:
  `folio_mapcount(old_folio) == 1 && folio_test_anon(old_folio)`
  and nothing else.
- `PageAnonExclusive()`: not part of the test; it is set after the decision.
- Reuse: the PTE becomes writable through `set_huge_ptep_maybe_writable()`,
  only with `VM_WRITE` and not on `FAULT_FLAG_UNSHARE`.
- There is no page_move_anon_rmap() here; `folio_move_anon_rmap()` does that.
- There is no outside_reserve here; the flag is `cow_from_owner`, true when
  the VMA has `HPAGE_RESV_OWNER` and `folio_test_anon(old_folio)`.
- `unmap_ref_private()`: skips `VM_MAYSHARE` VMAs and VMAs with
  `HPAGE_RESV_OWNER`.
- Recheck after `unmap_ref_private()`: no new folio exists on this path; on a
  mismatch `hugetlb_wp()` returns 0 with the page table lock held.

**Hugetlb page cache insertion**

- Folio state on entry: not locked and not visible to anyone else;
  `hugetlb_add_to_page_cache()` sets the lock bit itself with the non-atomic
  `__folio_set_locked()`.
- On success: returns with the folio locked, the caller unlocks it, as
  `hugetlbfs_fallocate()` does.
- On failure: clears the lock bit with `__folio_clear_locked()` before it
  returns the error.

## Memory failure

**Memory failure return values**

- 0: `action_result()` in `mm/memory-failure.c` returns it only for
  `MF_RECOVERED` and `MF_DELAYED`; `MF_IGNORED` and `MF_FAILED` give `-EBUSY`.
- `-EOPNOTSUPP`: every such return from `memory_failure()` comes from
  `hwpoison_filter()`.
- `MF_SOFT_OFFLINE`: not a `memory_failure()` case; `memory_failure_work_func()`
  sends those entries to `soft_offline_page()`.
- `-EIO` from `get_hwpoison_page()`: never reaches the caller; `memory_failure()`
  turns it into `action_result()` with `MF_IGNORED`, so `-EBUSY`.
- `-EHWPOISON` has two sources in `mm/memory-failure.c`:
  - the page, or the hugetlb folio that holds it, was already poisoned;
  - a first error hit a large folio that could not be split to order 0, after
    `kill_procs_now()` ran.
- Already-poisoned page with `MF_ACTION_REQUIRED`: the return value is that of
  `kill_accessing_process()`:

| Value | Meaning |
|---|---|
| 0 | the walk found no entry for the pfn in `current`; no signal sent |
| `-EHWPOISON` | the walk found the pfn |
| `-EFAULT` | `current->mm` is NULL |

- `-ENXIO`: also returned by `mf_generic_kill_procs()` for
  `MEMORY_DEVICE_PRIVATE` and `MEMORY_DEVICE_COHERENT`.
- `kill_me_maybe()` on `-EHWPOISON` or `-EOPNOTSUPP`: returns at once; it sends
  no signal and makes no further check.
- `memory_failure_cb()` in `drivers/acpi/apei/ghes.c`: makes the same test as
  `kill_me_maybe()`; quiet on 0, `-EHWPOISON`, `-EOPNOTSUPP`, else
  `force_sig(SIGBUS)`.
- `arch/arm64`: has no call to `memory_failure()`; it goes through
  `drivers/acpi/apei/ghes.c`.
- `enum mf_result` in `include/linux/mm.h`: `MF_IGNORED` is 0, so a raw result
  passed on would read as success; convert with `action_result()`.
- `-ENOENT` from `try_memory_failure_hugetlb()`: means "not hugetlb, carry on";
  `memory_failure()` consumes it and never returns it.

**Memory failure on large folios**

- Target order: `min_order_for_split()` in `mm/huge_memory.c`; 0 for anon,
  `mapping_min_folio_order()` for a file folio.
- Truncated file folio (`folio->mapping` NULL): `min_order_for_split()` returns
  0; the split then fails with `-EBUSY` in `folio_check_splittable()`.
- Return value on failure: `memory_failure()` returns `-EHWPOISON`, not
  `-EBUSY`.
- `-EBUSY`: is what `soft_offline_in_use_page()` returns; it does not split at
  all when the minimum order is above 0.
- Before the return: `memory_failure()` re-reads `page_folio(p)` and calls
  `kill_procs_now()`, which signals with `forcekill` true.
- Tasks signalled by `kill_procs_now()`: only those `task_early_kill()`
  selects, not every task that maps the page.
  - with `MF_ACTION_REQUIRED`: `current`, if its mm maps the page or, for a
    file folio, has a VMA that covers it;
  - early-kill tasks (`PF_MCE_EARLY` or `sysctl_memory_failure_early_kill`).
- `try_to_split_thp_page()`: always unlocks; calls `put_page()` only when the
  split failed and `release` is true.
- After the failure: `memory_failure()` does not call
  `hwpoison_user_mappings()`; the folio stays in use with `PG_hwpoison` on `p`.
- `PG_has_hwpoisoned` afterwards: for example it makes `do_set_pmd()` refuse a
  PMD mapping and `shmem_file_read_iter()` copy page by page.

**Poison flags on large folios**

- `PG_has_hwpoisoned`: stored only in the flags of the second page of the
  folio (`FOLIO_SECOND_PAGE` in `include/linux/page-flags.h`), never the head.
- `PG_has_hwpoisoned` is an alias of `PG_active`, so the bit left on a page
  that becomes an order-0 folio would read as `PG_active`.
- Hugetlb per-page record: `struct raw_hwp_page` list in
  `mm/memory-failure.c`; with `HPG_raw_hwp_unreliable` set the list is gone.
- Hugetlb free: `__update_and_free_hugetlb_folio()` calls
  `folio_clear_hugetlb_hwpoison()`, which moves `PG_hwpoison` from the head to
  the listed pages.
- Split: there is no __split_huge_page() here; `__split_folio_to_order()` in
  `mm/huge_memory.c` handles the flag, with `page_range_has_hwpoisoned()`.
- Split sequence in `__split_folio_to_order()`:
  - clears the flag on the original folio, always;
  - if it was set and `new_order` is above 0, sets it again on each resulting
    folio whose range holds a `PG_hwpoison` page;
  - sets it on a new folio only after `prep_compound_page()`.
- One page that may be in a hugetlb folio: `PageHWPoison()` on a tail is false.

| Helper | Result for a hugetlb tail | Context |
|---|---|---|
| `is_page_hwpoison()` | true if the head has `PG_hwpoison` | any |
| `is_raw_hwpoison_page_in_hugepage()` | true for the listed page; for all if unreliable | takes `mf_mutex`, may sleep |

- **Potentially unsafe usage**: `folio_test_hwpoison()` alone to decide
  whether a folio holds poison.
  - Unsafe: on a large folio that is not hugetlb; it reads the head page only
    and misses a poisoned tail page.
  - Safe: on a hugetlb folio, where `hugetlb_update_hwpoison()` sets the flag
    on the head, as `hugetlbfs_read_iter()` does.
  - Safe: `folio_contain_hwpoisoned_page()` on any folio, as
    `shrink_folio_list()` and `do_migrate_range()` do.
- **Unsafe usage**: `folio_test_has_hwpoisoned()` on a folio that may be
  order 0; `const_folio_flags()` reads the next `struct page`.
  - Safe: after `folio_test_large()`, as `shmem_file_read_iter()` does.
  - Safe: after `is_pmd_order()`, as `do_set_pmd()` does.

**Reading poisoned contents**

- `thp_underused()` and `try_to_map_unused_to_zeropage()`: compare with
  `pages_identical()` (plain `memcmp_pages()`); neither calls `memchr_inv()`.
- `thp_underused()`: returns false when `folio_contain_hwpoisoned_page()` is
  true, before it reads any page.
- `try_to_map_unused_to_zeropage()`: returns false on `PageHWPoison(page)`,
  before `pages_identical()`.
- `folio_mc_copy()` callers: there is no migrate_folio_extra() here;
  `__migrate_folio()` and `migrate_huge_page_move_mapping()` in `mm/migrate.c`
  call it, both before the mapping is switched.
- `copy_mc_highpage()` and `copy_mc_user_highpage()`: on failure they call
  `memory_failure_queue()` on the source pfn themselves; the caller only
  handles the non-zero return.
- Without an arch `copy_mc_to_kernel` (`#ifdef` in `include/linux/highmem.h`):
  both helpers are plain copies that return 0 and queue nothing.
- x86 `copy_mc_to_kernel()` in `arch/x86/lib/copy_mc.c`: is a plain `memcpy()`
  that returns 0 unless `copy_mc_fragile_key` is on or the CPU has
  `X86_FEATURE_ERMS`.
- Page that may be in a hugetlb folio: test with the helpers under "Poison
  flags on large folios"; for example `read_kcore_iter()` in `fs/proc/kcore.c`
  uses `is_page_hwpoison()`.
- **Potentially unsafe usage**: testing `PageHWPoison()` on the first page,
  then copying a range that spans several pages of a large folio.
  - Unsafe: when another page in the range has `PG_hwpoison`; the plain copy
    reads it.
  - Safe: copy `PAGE_SIZE` at a time when `folio_test_has_hwpoisoned()` is
    set, as `shmem_file_read_iter()` does with `fallback_page_copy`.
  - Safe: cut the range at the first poisoned page, as
    `adjust_range_hwpoison()` in `fs/hugetlbfs/inode.c` does.

## Model gaps

### Other mistakes models make

- Models take `add_hugetlb_folio()` to drop the caller's reference. A free
  hugetlb folio in the pool has refcount 0; `folio_ref_unfreeze()` sets it to
  1 when the folio is handed out, for example in
  `dequeue_hugetlb_folio_node_exact()`.
- Models take the khugepaged limits to be scaled by a shift for orders below
  PMD order. `collapse_max_ptes_swap()` and `collapse_max_ptes_shared()` in
  `mm/khugepaged.c` return 0 below PMD order when `cc->is_khugepaged`.
- Models do not know `VM_UFFD_RWP`. A fault on a protnone huge PMD with the
  uffd bit in a `userfaultfd_rwp()` VMA goes to `do_huge_pmd_uffd_rwp()`;
  `remove_migration_pmd()` puts `PAGE_NONE` back when `pmd_swp_uffd()` and
  `userfaultfd_rwp()` both hold; `userfaultfd_protected()` covers both modes.
- Models take a pfn that is not memory to give `-ENXIO` from
  `memory_failure()`. A pfn for which `pfn_valid()` and
  `arch_is_platform_page()` are both false goes to `memory_failure_pfn()`,
  which signals the tasks collected through ranges registered with
  `register_pfn_address_space()` and returns what `action_result()` returns.
- Models take the huge zero folio to be refcounted. `set_huge_zero_folio()`
  in `mm/huge_memory.c` marks its PMD with `pmd_mkspecial()`.
- Models take a tail page to hold a pointer to its head.
  `compound_info_has_mask()` in `include/linux/page-flags.h` is true only
  with `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` and a power-of-two
  `struct page`, and `set_compound_head()` takes the order.
- Models decode non-present PTEs with is_swap_pte(), pte_to_swp_entry() and
  is_migration_entry(). None is defined in this tree; code uses
  `softleaf_from_pte()` and tests such as `softleaf_is_migration()` in
  `include/linux/leafops.h`.
- Models write the uffd-wp bit helpers with a _wp suffix. Here the PTE and
  hugetlb tests are `pte_uffd()` and `huge_pte_uffd()`; `userfaultfd_wp()`
  and `vmf_orig_pte_uffd_wp()` keep their names.
- Models look for `lru_add_drain()` in mm/swap.c. That file is not in this
  tree; it is in `mm/folio.c`.
