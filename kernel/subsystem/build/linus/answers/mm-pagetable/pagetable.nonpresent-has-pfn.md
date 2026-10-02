- `softleaf_to_folio()` kind check: `VM_WARN_ON_ONCE(!softleaf_has_pfn(entry))`,
  so a hwpoison entry passes as well.
- Lock check: `softleaf_migration_sync()` does
  `VM_WARN_ON_ONCE(!folio_test_locked(folio))` for migration entries only;
  there is no `BUG_ON()`.
- Both checks vanish without `CONFIG_DEBUG_VM`; the folio is returned either
  way and no reference is taken.
- Split race: `softleaf_migration_sync()` issues `smp_rmb()` before the lock
  test, pairing with the write barrier in `__split_folio_to_order()`, so a new
  tail folio is not seen unlocked; the barrier is not under
  `CONFIG_DEBUG_VM`.
- `softleaf_to_page()` and `pmd_to_softleaf_folio()`: make the same lock
  check.
- Lifetime: the folio is valid only while the PTL covering the entry is held;
  the migrator holds a reference and must take that PTL to remove the entry.
- `softleaf_entry_wait_on_locked()` in `mm/filemap.c`: the waiter; it queues
  on the folio waitqueue under the PTL, drops the PTL, and takes no folio
  reference. There is no migration_entry_wait_on_locked() here.
- `softleaf_entry_wait_on_locked()` also serves device-private entries, from
  `do_swap_page()`.
