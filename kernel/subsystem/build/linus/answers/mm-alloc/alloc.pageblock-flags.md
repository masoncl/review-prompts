- Isolation: the standalone bit `PB_migrate_isolate`, present only under
  `CONFIG_MEMORY_ISOLATION`. `PB_migrate_0` to `PB_migrate_2` keep the
  block's own type while it is isolated.
- `get_pfnblock_migratetype()` on an isolated block: returns
  `MIGRATE_ISOLATE`. Read the stored type with `__get_pfnblock_flags_mask()`
  and `PAGEBLOCK_MIGRATETYPE_MASK`, as `__move_freepages_block_isolate()`
  does.
- Names not in this tree: PB_migrate_end, PB_migrate_skip,
  PB_migratetype_bits, MIGRATETYPE_MASK, MIGRATETYPE_AND_ISO_MASK. The masks
  are `PAGEBLOCK_MIGRATETYPE_MASK` and `PAGEBLOCK_ISO_MASK`; the compaction
  bit is `PB_compact_skip`.
- Linkage: `set_pageblock_migratetype()`, `change_pageblock_range()`,
  `move_freepages_block()` and `__move_freepages_block()` are static in
  `mm/page_alloc.c`.
- Not static, for callers outside `mm/page_alloc.c`:
  `init_pageblock_migratetype()` (takes an `isolate` argument),
  `pageblock_isolate_and_move_free_pages()` and
  `pageblock_unisolate_and_move_free_pages()`.
- `set_pageblock_migratetype()` given `MIGRATE_ISOLATE`: returns without
  writing; only the warning depends on `CONFIG_DEBUG_VM`.
- `set_pageblock_migratetype()` on an isolated block: clears
  `PB_migrate_isolate`, because it writes with `PAGEBLOCK_ISO_MASK` in the
  mask. The warning is `VM_WARN_ONCE()`, so `CONFIG_DEBUG_VM` only.
- Page spanning several blocks: `change_pageblock_range()`. It assumes
  `start_order >= pageblock_order` and moves no free pages.
- `__move_freepages_block()`: moves the free pages only; the caller writes
  the type.
- `move_freepages_block()`: moves and writes the type; returns -1 and changes
  nothing when the block straddles a zone boundary.
- `pageblock_isolate_and_move_free_pages()`: when the block is part of a
  free page above `pageblock_order`, it splits that page with
  `split_large_buddy()` instead of moving list entries.
- **Unsafe usage**: writing a block's new type while its free pages are
  still on the old type's list.
  - Safe: move first, then write, as `move_freepages_block()` does;
    `move_to_free_list()` checks, with `VM_WARN_ONCE()`, that the block
    still has the old type.
  - Safe: for one page, delete it with the old type, write the type, add
    with the new type, as `try_to_claim_block()` does;
    `__del_page_from_free_list()` and `__add_to_free_list()` check each
    side with `VM_WARN_ONCE()`.
- **Potentially unsafe usage**: `change_pageblock_range()` with no move of
  free pages.
  - Unsafe: when the block holds other free pages; they stay on the old
    list.
  - Safe: when the page covers each block whole and is off the free lists:
    the allocated page in `reserve_highatomic_pageblock()`, or the buddy
    just deleted in `__free_one_page()`.
