- Without `CONFIG_TRANSPARENT_HUGEPAGE`: `mapping_set_folio_order_range()`
  returns at once, and `mapping_min_folio_order()` and
  `mapping_max_folio_order()` return 0 whatever `mapping->flags` holds.
- Max-only setter: none; use `mapping_set_folio_order_range()`.
- **Potentially unsafe usage**: calling an order setter on a mapping that is
  already in use.
  - Unsafe: while folios can be added or are cached; the setter is a plain
    read-modify-write of `mapping->flags`, which also holds bits changed
    with `set_bit()`, and `__filemap_add_folio()` asserts each folio against
    the minimum.
  - Safe: in the inode constructor, as `btrfs_set_inode_mapping_order()`
    callers do.
  - Safe: with the inode lock and `filemap_invalidate_lock()` held and the
    cache emptied first, as `set_blocksize()` in `block/bdev.c` does, and
    `ext4_change_inode_journal_flag()` under the inode lock taken by
    `vfs_fileattr_set()`.
- Maximum order: nothing in `__filemap_add_folio()` checks it; of the order,
  only the minimum and the index alignment are asserted, so clamping is left
  to the code that allocates, as `__filemap_get_folio_mpol()` does.
- Split floor: `__folio_split()` in `mm/huge_memory.c` returns `-EINVAL` when
  the new order is below `mapping_min_folio_order()`.
- `min_order_for_split()`: in `mm/huge_memory.c`; returns 0 for an anon
  folio or one whose `folio->mapping` is NULL.
- PMD-size folios: test `mapping_pmd_folio_support()`, not
  `mapping_large_folio_support()`.
