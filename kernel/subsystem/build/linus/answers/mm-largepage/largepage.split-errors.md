| Value | Source | Folio afterwards |
|---|---|---|
| `-EBUSY` | NULL `->mapping` on a non-anon folio; writeback; anon folio not mapped (`folio_get_anon_vma()`); `filemap_release_folio()` | whole, mappings untouched |
| `-EINVAL` | `folio_check_splittable()` order tests; `split_at` outside folio; `new_order` not below order; below min order | whole, mappings untouched |
| `-EAGAIN` | precheck | whole, mappings untouched |
| `-EAGAIN` | `xas_load()` mismatch; freeze | whole, already unmapped |
| `-ENOMEM` | `xas_split_alloc()`, uniform | whole, mappings untouched |
| `xas_error()` | `xas_try_split()`, non-uniform | may be partly split |

- Huge zero folio: `folio_check_splittable()` returns `-EBUSY`; its
  `->mapping` is NULL and it is not anon, so the truncated-folio test catches
  it before the `is_huge_zero_folio()` test.
- Reference count failures: `-EAGAIN`, never `-EBUSY`.
- Failure after `unmap_folio()`: an anon folio is remapped by `remap_page()`
  with PTEs; a file folio stays unmapped and refaults.
- Partly split folio: the pieces made so far are unfrozen, put on the LRU and
  unlocked as on success; the first piece stays locked.
- `-EINVAL` from `folio_check_splittable()`: also fires the `VM_WARN_ONCE()`
  "Tried to split an unsplittable folio" in `__folio_split()`; the min-order
  `-EINVAL` does not.
- `-EXDEV`: not returned by the split.
- Without `CONFIG_TRANSPARENT_HUGEPAGE`: the split stubs in
  `include/linux/huge_mm.h` return `-EINVAL` after a
  `VM_WARN_ON_ONCE_PAGE()` or `VM_WARN_ON_ONCE_FOLIO()`.
