- put_locked_mapping_entry() is not in this tree; `dax_unlock_entry()`
  unlocks an entry, also for `dax_unlock_folio()` and
  `dax_unlock_mapping_entry()`.
- `grab_mapping_entry()` and `dax_insert_entry()`: return the value without
  `DAX_LOCKED`; only the slot holds the locked form.
- Entry from `get_next_unlocked_entry()`: valid only while the `i_pages`
  lock is held; `dax_insert_pfn_mkwrite()` calls `dax_lock_entry()` before
  `xas_unlock_irq()`.
- `wait_entry_unlocked_exclusive()`: its result carries the same lock-or-put
  duty; it returns NULL when the entry is gone, and then no wake is needed.
- `wait_entry_unlocked_exclusive()` use: inside `xas_for_each()` walks on an
  entry already loaded, as in `dax_delete_mapping_range()`.
- `dax_unlock_entry()`: accepts a fresh `XA_STATE` at the index, as
  `dax_unlock_folio()` and `dax_unlock_mapping_entry()` build one.
- **Unsafe usage**: passing `dax_unlock_entry()` a value that has
  `DAX_LOCKED` set, or the value from before `dax_insert_entry()` replaced it.
  - Unsafe: `BUG_ON(dax_is_locked(entry))` fires for a locked value; a stale
    value is stored as-is over the new entry.
  - Safe: unlock with what `dax_insert_entry()` returned, as
    `dax_fault_iter()` writes it through `void **entry` for
    `dax_iomap_pte_fault()`.
- **Potentially unsafe usage**: a lookup or store through an `xa_state` again
  after the `i_pages` lock was dropped, with no explicit `xas_reset()`.
  - Unsafe: when `xas->xa_node` still points at a node from before the drop;
    `xas_start()` in `lib/xarray.c` continues from it.
  - Safe: `xas_reset()` before relocking, as `dax_insert_entry()` and
    `dax_unlock_entry()` do; it sets `XAS_RESTART`, which `xas_start()` tests.
  - Safe: `xas_reset()` after the zero-entry unmap in `grab_mapping_entry()`,
    then `xas_set()` back to the fault index after the downgrade.
  - Safe: `xas_set()` after relocking, as `dax_lock_folio()` and
    `dax_lock_mapping_entry()` do after `wait_entry_unlocked()`; `xas_set()`
    sets `XAS_RESTART`.
  - Safe: `xas_pause()` before the drop inside a walk, as
    `dax_layout_busy_page_range()` does every `XA_CHECK_SCHED` entries;
    `xas_pause()` in `lib/xarray.c` sets `XAS_RESTART`.
  - Safe: `goto retry` in `grab_mapping_entry()` after `xas_nomem()` returned
    true; `xas_nomem()` in `lib/xarray.c` sets `XAS_RESTART`.
  - Safe: after `get_next_unlocked_entry()` or
    `wait_entry_unlocked_exclusive()` slept; both call `xas_reset()` and look
    up again before they return.
