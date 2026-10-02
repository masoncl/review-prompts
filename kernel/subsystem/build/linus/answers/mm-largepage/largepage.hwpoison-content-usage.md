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
