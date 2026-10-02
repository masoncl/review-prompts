- References are on the page that holds the entry (`ctx->ptep`): one from
  `zalloc_page`, one per counted entry.
- `stage2_pte_is_counted()`: any non-zero entry, so annotations count.
- `stage2_free_walker()`: dispatches to `stage2_free_leaf()` and
  `stage2_free_table_post()`.
- `stage2_free_table_post()` on a table that still has counted entries
  (`page_count(childp) != 1`): returns 0 and frees nothing.
- `stage2_free_table_post()` on an empty table: puts both references, then
  clears the entry, so a later chunk of `stage2_destroy_range()` does not
  walk into the freed page.
- Replacing a valid entry: `stage2_try_break_pte()` drops the old entry's
  reference after the TLBI; `stage2_make_pte()` takes one for the new entry.
- `stage2_map_walk_table_pre()`: returns the error before
  `mm_ops->free_unlinked_table()` when the replace fails; this walker has
  then not unlinked the subtree.
- `level` passed to `mm_ops->free_unlinked_table()` and
  `kvm_pgtable_stage2_free_unlinked()`: the level of the entry that pointed
  at the table; the walk starts at `level + 1`.
- `kvm_pgtable_stage2_free_unlinked()`: warns if the root's `page_count()` is
  not 1 after the walk, and puts it anyway.
- **Potentially unsafe usage**: dropping the last reference on a table page
  with `mm_ops->put_page()` or `kvm_pgtable_stage2_free_unlinked()` from a
  visitor.
  - Unsafe: when the page was linked in a table that a walk flagged
    `KVM_PGTABLE_WALK_SHARED` can be in; that walker still reads the page
    inside the `rcu_read_lock()` taken by `kvm_pgtable_walk_begin()`.
  - Safe: `mm_ops->free_unlinked_table()` after the entry is replaced, as
    `stage2_map_walk_table_pre()` does; `stage2_free_unlinked_table()` defers
    the free with `call_rcu()`.
  - Safe: when the page was never linked, as `stage2_map_walk_leaf()` and
    `stage2_split_walker()` do after `stage2_try_break_pte()` fails.
  - Safe: in a walk without `KVM_PGTABLE_WALK_SHARED` under the write lock,
    as `stage2_unmap_walker()` does on the host; `__unmap_stage2_range()`
    asserts the write lock.
