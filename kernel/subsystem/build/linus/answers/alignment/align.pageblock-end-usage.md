- `@end_pfn` of `start_isolate_page_range()` and
  `undo_isolate_page_range()`: one past the last pfn, although the kerneldoc
  says "The last PFN".
- `offline_pages()` passes `start_pfn + nr_pages` as that end, and
  `alloc_contig_frozen_range_noprof()` passes `end`.
- Last block in `start_isolate_page_range()`: starts at
  `isolate_end - pageblock_nr_pages`; the function does not use
  `pageblock_start_pfn(end_pfn - 1)`.
- `pageblock_start_pfn(end_pfn - 1)` for the last block of an exclusive end:
  see `compact_zone()` and `reset_cached_positions()` in `mm/compaction.c`,
  and the `VM_BUG_ON()` in `has_unmovable_pages()`.
- `pageblock_end_pfn(pfn)`: `pfn` is a page frame inside the block; for an
  aligned exclusive end it returns the end of the next block. The last pfn of
  a block is `pageblock_end_pfn(pfn) - 1`, as in `__reset_isolation_pfn()` in
  `mm/compaction.c`.
- **Potentially unsafe usage**: acting on the first and the last pageblock of
  a range one after the other.
  - Unsafe: when the range lies in one pageblock, both are the same block; a
    second `set_migratetype_isolate()` on it returns `-EBUSY`.
  - Safe: test `isolate_start == isolate_end - pageblock_nr_pages` first, as
    `start_isolate_page_range()` does to set `skip_isolation`.
- **Potentially unsafe usage**: `start_isolate_page_range()` on an empty
  range.
  - Unsafe: with `start_pfn == end_pfn` and both aligned, it isolates the
    block at `start_pfn` and the block before it; the function has no test.
  - Safe: reject a zero length before the call, as `offline_pages()` does
    with `!nr_pages`.
- **Potentially unsafe usage**: using a rounded-out block without checking
  the zone.
  - Unsafe: when the zone starts or ends inside the block, part of the
    rounded block belongs to another zone or to none.
  - Safe: clamp to `zone->zone_start_pfn` and `zone_end_pfn()`, as
    `fast_isolate_around()` and `__reset_isolation_pfn()` in
    `mm/compaction.c` do.
  - Safe: refuse the block, as `prep_move_freepages_block()` does with
    `zone_spans_pfn()` on both ends; isolation then returns `-EBUSY`.
- Memmap of the boundary blocks: `isolate_single_pageblock()` calls
  `pfn_to_page()` on the rounded block start with no online test.
- Middle blocks of `start_isolate_page_range()`: the page passed to
  `set_migratetype_isolate()` comes from `__first_valid_page()`; for the
  boundary blocks it does not.
