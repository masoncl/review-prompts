- Folio lock: `VM_WARN_ON_ONCE_FOLIO()` in `__folio_split()` and
  `VM_WARN_ON_FOLIO()` in `folio_check_splittable()`.
- Large folio: `VM_WARN_ON_ONCE_FOLIO()` in `__folio_split()`.
- Small folio: fails `new_order >= old_order` in `__folio_split()` with
  `-EINVAL`.
- `folio_check_splittable()` tests, in this order:
  - non-anon folio with NULL `->mapping`: `-EBUSY`
  - anon folio and `new_order == 1`: `-EINVAL`
  - swap cache folio with non-uniform split or non-zero order: `-EINVAL`
  - `is_huge_zero_folio()`: `-EINVAL`
  - writeback: `-EBUSY`
- `__folio_split()` tests the rest itself: `split_at` and `lock_at` inside the
  folio, `new_order` below the current order, `mapping_min_folio_order()`,
  `filemap_release_folio()`, `folio_get_anon_vma()`, the reference count.
- No test on the split path rejects a hugetlb folio or a mapping without
  large folio support.
- On the LRU when `list == NULL`: `VM_WARN_ON()` in `lru_add_split_folio()`
  only.
