- PTE fault, real PMD entry: `grab_mapping_entry()` locks and returns the
  PMD entry; nothing is removed or split.
- PTE fault, real PMD entry: `dax_insert_entry()` leaves it in place when the
  iomap lacks `IOMAP_F_SHARED`, and only sets marks.
- PTE fault, empty PMD entry: removed without `unmap_mapping_pages()`; only a
  zero PMD entry is unmapped first.
- PTE fault, locked PMD entry of any kind: `get_next_unlocked_entry()` waits
  for the unlock before the kind is looked at.
- PMD fault, any PTE entry in range: conflict, also for a zero or an empty
  PTE entry; nothing is removed and no PMD entry is installed.
- PMD fault, locked PTE entry: no wait; `get_next_unlocked_entry()` tests the
  order before the lock bit.
- `dax_is_conflict()`: true only for `XA_RETRY_ENTRY`, which
  `get_next_unlocked_entry()` returns; it is not a fault code.
- `grab_mapping_entry()`: turns the conflict into
  `xa_mk_internal(VM_FAULT_FALLBACK)`; `XA_RETRY_ENTRY` never reaches its
  caller.
- `grab_mapping_entry()` errors: `xa_mk_internal(VM_FAULT_OOM)` or
  `xa_mk_internal(VM_FAULT_SIGBUS)`; callers test `xa_is_internal()` and
  decode with `xa_to_internal()`.
- `dax_insert_pfn_mkwrite()`: does not go through `grab_mapping_entry()`; at
  order 0 it treats any PMD entry, real ones too, as a race.
- `dax_insert_pfn_mkwrite()` on a race or conflict: calls
  `put_unlocked_entry()` with `WAKE_NEXT` and returns `VM_FAULT_NOPAGE`.
