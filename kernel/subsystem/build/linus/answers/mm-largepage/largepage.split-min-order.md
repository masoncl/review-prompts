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
