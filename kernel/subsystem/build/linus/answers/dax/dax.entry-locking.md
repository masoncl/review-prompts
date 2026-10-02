- `dax_unlock_entry()`: the caller must not hold the `i_pages` lock; it
  takes the lock with `xas_lock_irq()`, stores, drops it, then wakes.
- `put_unlocked_entry()`: every call site in `fs/dax.c` holds the `i_pages`
  lock; the body reads only `xas->xa` and `xas->xa_index` and drops nothing.
- `wait_entry_unlocked()`: entered with the lock held, returns with it
  dropped; it waits non-exclusively and does not re-look-up the entry.
- `wait_entry_unlocked()` callers: `dax_lock_folio()` and
  `dax_lock_mapping_entry()`, which retake the lock and reload in their loop.
- `wait_table`: a file-scope static array in `fs/dax.c`, shared by all
  mappings; `struct exceptional_entry_key` tells entries on one queue apart.
- `dax_entry_waitqueue()`: decides PMD or PTE from the entry value passed
  in, not from the slot; a waker must pass an entry of the size the waiters
  saw.
- PMD downgrade in `grab_mapping_entry()`: passes the old PMD entry to
  `dax_wake_entry()` after the slot was set to NULL.
- `__dax_invalidate_entry()`: wakes with `WAKE_ALL` on every path that found
  an entry, also when it removed nothing because a mark was set.
- `dax_writeback_one()`: after the flush it wakes with `dax_wake_entry()` and
  `WAKE_NEXT` directly, while holding the `i_pages` lock.
