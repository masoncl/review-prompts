- Constant forms in `include/linux/pageblock-flags.h`: every one is capped by
  `PAGE_BLOCK_MAX_ORDER`, not `MAX_PAGE_ORDER`.
  - `CONFIG_HUGETLB_PAGE` without `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`:
    `MIN_T(unsigned int, HUGETLB_PAGE_ORDER, PAGE_BLOCK_MAX_ORDER)`.
  - `CONFIG_TRANSPARENT_HUGEPAGE` without hugetlb:
    `MIN_T(unsigned int, HPAGE_PMD_ORDER, PAGE_BLOCK_MAX_ORDER)`.
  - neither: `PAGE_BLOCK_MAX_ORDER`.
- Variable form: `unsigned int pageblock_order __read_mostly` is defined in
  `mm/page_alloc.c`, under `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`.
- `CONFIG_HUGETLB_PAGE_SIZE_VARIABLE`: the only `select` is in
  `arch/powerpc/Kconfig`, for `PPC_BOOK3S_64 && HUGETLB_PAGE`; there is no
  ia64 in this tree.
- `set_pageblock_order()`: one call site, in `free_area_init()` in
  `mm/mm_init.c`; `sparse_init()` does not call it.
- `mm_core_init_early()` calls `free_area_init()` before `sparse_init()`.
- `set_pageblock_order()` body: starts from `PAGE_BLOCK_MAX_ORDER` and lowers
  to `HUGETLB_PAGE_ORDER` when that is smaller and `HPAGE_SHIFT > PAGE_SHIFT`.
- `set_pageblock_order()` has no assertion and does not mention
  `MAX_PAGE_ORDER`.
- Before `set_pageblock_order()` runs the variable is 0, so
  `pageblock_nr_pages` is 1 and `CMA_MIN_ALIGNMENT_BYTES` is `PAGE_SIZE`.
- `cma_init_reserved_mem()` in `mm/cma.c`: returns `-EINVAL` with a
  `pr_err()` while `pageblock_order` is 0.
- `arch_mm_preinit()` in `arch/powerpc/mm/mem.c`: does its CMA reservations
  there because they need `pageblock_order` set.
- `PAGE_BLOCK_MAX_ORDER` and the `#error` for
  `PAGE_BLOCK_MAX_ORDER > MAX_PAGE_ORDER`: both in `include/linux/mmzone.h`;
  the bound is a preprocessor test, not a runtime check.
- `pageblock_order < MAX_PAGE_ORDER`: one free buddy page can cover several
  pageblocks.
- `__move_freepages_block_isolate()` in `mm/page_alloc.c`: skips
  `find_large_buddy()` and the split when
  `pageblock_order == MAX_PAGE_ORDER`.
