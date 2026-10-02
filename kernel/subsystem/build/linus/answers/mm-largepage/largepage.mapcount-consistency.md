- `folio_lock_large_mapcount()`: defined only under `CONFIG_MM_ID`; without
  it `folio_add_large_mapcount()` is a plain `atomic_add()` and
  `folio_maybe_mapped_shared()` returns `true` for every large non-hugetlb
  folio.
- Stable under the lock: only against `folio_add_return_large_mapcount()` and
  `folio_sub_return_large_mapcount()`, which update `_large_mapcount` with
  `atomic_read()` then `atomic_set()`.
- hugetlb: its rmap helpers change `_large_mapcount` with `atomic_inc()`,
  `atomic_dec()` or, in `hugetlb_add_new_anon_rmap()`, `atomic_set()`, and
  never take the lock or track MM ids.
- `folio_set_large_mapcount()`: writes `_large_mapcount` and slot 0 without
  the lock; `folio_add_new_anon_rmap()` uses it on a folio not yet mapped.
- `__wp_can_reuse_large_anon_folio()`: never reads `_mm_id_mapcount[]`; it
  tests `FOLIO_MM_IDS_SHARED_BITNUM` in `_mm_ids` and compares
  `folio_large_mapcount()` with `folio_ref_count()`, both again under the
  lock.
- folio_test_large_maybe_mapped_shared(): not in this tree; the public test
  is `folio_maybe_mapped_shared()` in `include/linux/mm.h`.
- `folio_large_mapcount() <= 1`: `__wp_can_reuse_large_anon_folio()` returns
  `false` at once, so a large folio with one mapped page is copied, not
  reused.
- Swapcache: not a reason to give up; it calls `folio_free_swap()` under
  `folio_trylock()` and goes on. Only a failed `folio_trylock()` returns
  `false`.
- Folio lock: not held for the comparison.
