- `folio_mapcount()` and `folio_mapped()`: safe on a small typed folio; they
  return 0 and false through `page_mapcount_is_type()`.
- `page_type_has_type()`: the boundary is `PGTY_mapcount_underflow << 24`.
  There is no PAGE_MAPCOUNT_RESERVE.
- Type setters from `PAGE_TYPE_OPS()` and `FOLIO_TYPE_OPS()`: the check that
  the field was `UINT_MAX` is `VM_BUG_ON_PAGE()` or `VM_BUG_ON_FOLIO()`, so
  without `CONFIG_DEBUG_VM` a set on a mapped page silently overwrites the
  mapcount.
- Setting a type that is already set, or clearing when the field is already
  `UINT_MAX`: returns early, no check.
- `PageSlab()`: tests only the page passed. `PageHuge()` is the type test that
  goes through `page_folio()`.
- Hugetlb: has `FOLIO_TYPE_OPS()` only, so there is `folio_test_hugetlb()` and
  no per-page test other than `PageHuge()`.
- `folio_precise_page_mapcount()` in `fs/proc/internal.h`: filters with
  `page_mapcount_is_type()`, not `page_has_type()`.
- Typed folio with mappings: hugetlb. It is the one type that
  `folio_expected_ref_count()` in `include/linux/mm.h` exempts from its
  `page_has_type()` test; see "Expected reference count".
