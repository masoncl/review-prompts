- `remove_hugetlb_folio()`: decrements `free_huge_pages` only if the folio
  has `HPG_freed`; `add_hugetlb_folio()` always increments it.
- Exact undo: `dissolve_free_hugetlb_folio()` passes its own
  `adjust_surplus` to both calls, and `demote_pool_huge_page()` passes
  `false` to both.
- Failed free: `__update_and_free_hugetlb_folio()` and
  `bulk_vmemmap_restore_error()` pass `true`, whatever the removal passed.
- Failed free with `true`: the folio becomes a free surplus page, and
  `persistent_huge_pages()` stays as the remover left it.
- `set_max_huge_pages()`: does not call `add_hugetlb_folio()` itself; it
  reaches `bulk_vmemmap_restore_error()` through
  `update_and_free_pages_bulk()`.
- `add_hugetlb_folio()`: asserts that the folio is still vmemmap-optimised,
  so it serves only as the rollback of a failed vmemmap restore.
- **Unsafe usage**: `remove_hugetlb_folio()` with `adjust_surplus` true while
  `h->surplus_huge_pages_node[nid]` is zero; the unsigned counter wraps.
  - Safe: test the per-node counter under `hugetlb_lock` first, as
    `free_huge_folio()` and `remove_pool_hugetlb_folio()` do.
