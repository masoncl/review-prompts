- **Potentially unsafe usage**: calling `softleaf_to_pfn()`,
  `softleaf_to_page()` or `softleaf_to_folio()` with no kind test in the same
  function.
  - Unsafe: when the entry can be swap, marker or none; the offset is then a
    swap slot, marker bits or 0, and the only check is
    `VM_WARN_ON_ONCE(!softleaf_has_pfn(entry))`, which is compiled out without
    `CONFIG_DEBUG_VM`.
  - Safe: after a specific predicate, as `check_pte()` does with
    `softleaf_is_migration()` under `PVMW_MIGRATION`, and with
    `softleaf_is_device_private()` or `softleaf_is_device_exclusive()`
    otherwise.
  - Safe: on an entry returned by `page_vma_mapped_walk()`, as
    `try_to_migrate_one()` and `remove_migration_pte()` do; `check_pte()` has
    already rejected every other non-present kind.
  - Safe: when the only caller made the test, as
    `try_restore_exclusive_pte()` in `mm/memory.c`, which
    `copy_nonpresent_pte()` calls after `softleaf_is_device_exclusive()`.
- Migration entry at fork: the only accounting in `copy_nonpresent_pte()` is
  `rss[mm_counter(folio)]++`; it takes no reference and no rmap, because the
  entry owns none.
- Swap entry at fork: the count is taken with `swap_dup_entry_direct()`;
  failure makes `copy_nonpresent_pte()` return `-EIO`. There is no
  swap_duplicate() here.
- Waiting on a migration or device-private entry: see "Folio behind a
  migration entry".
