- Folio state on entry: not locked and not visible to anyone else;
  `hugetlb_add_to_page_cache()` sets the lock bit itself with the non-atomic
  `__folio_set_locked()`.
- On success: returns with the folio locked, the caller unlocks it, as
  `hugetlbfs_fallocate()` does.
- On failure: clears the lock bit with `__folio_clear_locked()` before it
  returns the error.
