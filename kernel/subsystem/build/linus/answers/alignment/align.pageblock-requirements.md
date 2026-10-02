- `start_isolate_page_range()` and `undo_isolate_page_range()`: round out
  themselves, to `pageblock_start_pfn(start_pfn)` and
  `pageblock_align(end_pfn)`; an unaligned range is accepted.
- `VM_BUG_ON(!pageblock_aligned(boundary_pfn))` in
  `isolate_single_pageblock()`: tests the rounded value, not the caller's.
- First and last pageblock of `start_isolate_page_range()`: scanned whole for
  unmovable pages, including the part outside the caller's range, so an
  unmovable page there fails the call with `-EBUSY`.
- A `MIGRATE_CMA` block under `PB_ISOLATE_MODE_CMA_ALLOC` is not scanned;
  see `has_unmovable_pages()`.
- `test_pages_isolated()`: no rounding; it walks from the given `start_pfn`
  in steps of `pageblock_nr_pages`.
- `test_pages_isolated()` need not get the range that was isolated:
  `alloc_contig_frozen_range_noprof()` passes `outer_start`.
- `alloc_contig_range_noprof()`: a wrapper around
  `alloc_contig_frozen_range_noprof()` in `mm/page_alloc.c`.
- `alloc_contig_range_noprof()` with `__GFP_COMP`: `WARN_ON()` and `-EINVAL`
  before anything is isolated.
- `alloc_contig_frozen_range_noprof()`: passes the raw `start` and `end` to
  `start_isolate_page_range()` and `undo_isolate_page_range()`; it calls
  neither `pageblock_start_pfn()` nor `pageblock_align()`.
- `alloc_contig_frozen_range_noprof()` with `__GFP_COMP`: `-EINVAL` and
  `WARN()` unless the free pages it took are exactly `[start, end)` and the
  size is a power of two.
- Rounded-out part of the boundary pageblocks in
  `alloc_contig_frozen_range_noprof()`: only isolated for the call, then
  released by `undo_isolate_page_range()` at `done`.
- Pages outside `[start, end)` that are taken and given back, without
  `__GFP_COMP`: only those of a free page straddling `start` (see
  `find_large_buddy()`) or `end`, returned with
  `__free_contig_frozen_range()`.
- `CMA_MIN_ALIGNMENT_PAGES` in `include/linux/cma.h`: exactly
  `pageblock_nr_pages`, with no link to `MAX_PAGE_ORDER`.
- `cma_declare_contiguous_nid()`: the work is in
  `__cma_declare_contiguous_nid()` in `mm/cma.c`.

| Argument of `__cma_declare_contiguous_nid()` | Not aligned |
|---|---|
| fixed base | `pr_err()` and `-EINVAL` |
| base, not fixed | rounded up |
| size | rounded up, no error |
| `limit` | rounded down |

- Fixed base: tested against `alignment` after it is raised to at least
  `CMA_MIN_ALIGNMENT_BYTES`, so a larger caller alignment binds the base too.
- Fixed base of 0: passes the test and is then treated as not fixed.
- `online_pages()` and `offline_pages()`: make the pageblock and section
  test themselves.
- `check_hotplug_memory_range()`: tests `memory_block_size_bytes()` alignment
  on add and remove, in `__add_memory_resource()` and `try_remove_memory()`.
- `try_remove_memory()`: wraps that test in `BUG_ON()`.
- Memmap-on-memory: `mhp_supports_memmap_on_memory()` refuses a memmap that
  is not whole pageblocks.
- Under `MEMMAP_ON_MEMORY_FORCE`,
  `memory_block_memmap_on_memory_pages()` rounds it up with
  `pageblock_align()` instead.
