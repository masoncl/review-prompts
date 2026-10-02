- Shared bit: read with
  `test_bit(FOLIO_MM_IDS_SHARED_BITNUM, &folio->_mm_ids)`; there is no
  folio_test_large_maybe_mapped_shared() in this tree.
- Lock, with `CONFIG_MM_ID`, non-hugetlb folio: slots, shared bit and
  `_large_mapcount` change under `folio_lock_large_mapcount()`, a bit
  spinlock in `_mm_ids`, except in `folio_set_large_mapcount()` on a new
  folio; the PTL does not serialise different MMs.
  `folio_maybe_mapped_shared()` reads without it.
- Clearing: `folio_sub_return_large_mapcount()` clears the bit when the
  unmapping MM has no slot left and one slot's count equals the new total,
  not only at full unmap.
- `CONFIG_NO_PAGE_MAPCOUNT`: plays no part in `folio_maybe_mapped_shared()`.
- hugetlb: `folio_mapcount() > 1`; hugetlb folios have no mm-id tracking.
- True for a folio one MM maps, all cases:
  - large, non-hugetlb, without `CONFIG_MM_ID`: always, even unmapped; that
    test comes before the `mapcount <= 1` test
  - large: more than two MMs mapped it and the one left has mappings that no
    slot counts; the bit stays set until the folio is fully unmapped
  - large, 32-bit: the per-MM count overflowed, which frees the slot and sets
    the bit
  - small or hugetlb: the same MM maps it more than once, such as a page
    cache folio in two VMAs or a KSM folio
- False for a folio several MMs map: hugetlb with a shared page table, which
  counts once. `queue_folios_hugetlb()` in `mm/mempolicy.c` and
  `pagemap_hugetlb_range()` in `fs/proc/task_mmu.c` pair the test with
  `hugetlb_pmd_shared()`.
