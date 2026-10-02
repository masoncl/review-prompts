- Block order: `__kho_preserve_pages_order()` takes
  `min(count_trailing_zeros(pfn), ilog2(end_pfn - pfn))`, then lowers it until
  the first and last pfn of the block give the same `pfn_to_nid()`.
- `MAX_PAGE_ORDER`: no cap in `kho_preserve_pages()` or in
  `kho_restore_pages()`.
- Scratch overlap: `WARN_ON()` and `-EINVAL` only under
  `CONFIG_KEXEC_HANDOVER_DEBUG`.
- `kho_restore_pages()`: does not call `__kho_preserve_pages_order()`; it
  advances by its own `min(count_trailing_zeros(pfn), ilog2(end_pfn - pfn))`.
- Pages initialised per step: `1 << info.order` from the stored order in
  `kho_restore_page()`; the step and the stored order are never compared.
- Wrong `nr_pages` on restore: fails only when the walk lands on a pfn that
  is not online or whose `page->private` lacks `KHO_PAGE_MAGIC`; otherwise it
  returns the first page.
- `kho_restore_pages()` failure: returns NULL with no undo; blocks already
  restored stay restored.
