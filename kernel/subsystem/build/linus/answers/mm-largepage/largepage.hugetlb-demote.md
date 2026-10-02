- Copied explicitly: `HPG_cma`, with `folio_set_hugetlb_cma()` on every new
  folio; `HPG_vmemmap_optimized` is not copied.
- Vmemmap: restored on the source by `hugetlb_vmemmap_restore_folios()`
  first; the new folios are optimised again in
  `prep_and_add_allocated_folios()`.
- `HPG_cma` missing on a new folio: `__update_and_free_hugetlb_folio()` calls
  `free_frozen_pages()` on CMA memory instead of
  `hugetlb_cma_free_frozen_folio()`.
- `init_new_hugetlb_folio()`: takes only the folio; it sets the type, the
  list head, a NULL subpool and NULL cgroups, and writes neither
  `folio->private` nor the refcount.
- There is no prep_and_add_hugetlb_folios() here;
  `prep_and_add_allocated_folios()` adds the new folios to the pool.
- Source folio whose restore failed: `demote_free_hugetlb_folios()` skips it
  and leaves it on the list; see "Surplus adjustment" for the add-back.
