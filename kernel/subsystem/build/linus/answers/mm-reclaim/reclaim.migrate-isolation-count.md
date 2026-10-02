- Return type of `collect_longterm_unpinnable_folios()` in `mm/gup.c`:
  `unsigned long`, not void.
- Return value: the number of folios for which `folio_is_longterm_pinnable()`
  was false. It is counted before any isolation is tried.
- The count includes folios that are never listed: device-coherent folios,
  and folios for which `folio_isolate_hugetlb()` or `folio_isolate_lru()`
  failed.
- `check_and_migrate_movable_pages_or_folios()`: tests the count, not
  `list_empty()`. Only a zero count returns 0 and keeps the pins.
- Empty list: guarantees only that nothing was isolated. It says nothing
  about whether the folios are pinnable.
- Zero return: every folio examined passed `folio_is_longterm_pinnable()` at
  that moment, and the list is empty.
- Non-zero count with an empty list: `migrate_longterm_unpinnable_folios()`
  unpins everything, skips `migrate_pages()` and returns `-EAGAIN`, or
  `-EBUSY` if `migrate_device_coherent_folio()` failed.
- Retry loop: `__gup_longterm_locked()` repeats while the result is
  `-EAGAIN`. There is no __get_longterm_locked().
- Device-coherent folios: migrated in `migrate_longterm_unpinnable_folios()`
  with `migrate_device_coherent_folio()`, not during collection.
- LRU drain: `lru_cache_drain_for_folio()` in `mm/folio.c`. It drains when
  the refcount differs from `folio_expected_ref_count()` plus the pin
  references: 1 with `folio_has_pincount()`, else `GUP_PIN_COUNTING_BIAS`.
