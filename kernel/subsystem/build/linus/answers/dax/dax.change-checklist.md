- `dax_insert_entry()`: entered with the entry lock held and the `i_pages`
  lock not held; it takes the `i_pages` lock itself.
- `__dax_invalidate_entry()`: takes the `i_pages` lock itself.
- `dax_lock_entry()`: has no assertion.
- Slot still holds the caller's locked entry: checked by the `WARN_ON_ONCE`
  in `dax_insert_entry()`, on the replace branch only.
- `dax_insert_entry()` non-replace branch: discards the `xas_load()` result,
  so nothing checks the slot there.
- `dax_disassociate_entry()`: has no `WARN_ON_ONCE` of its own and does not
  use its `mapping` or `trunc` argument.
- Folio belongs to the mapping it is removed from: nothing checks.
- `dax_disassociate_entry()` on a shared folio: only decrements
  `folio->share`; `->mapping` is cleared when the folio is not shared or the
  count reaches 0, in `dax_folio_reset_order()`.
- Pages idle when the last association goes: `dax_folio_put()` has
  `WARN_ON_ONCE(folio_ref_count())` per page, for order 0 too, whatever
  `trunc` was.
- Folio is order 0 when associated on the non-shared path: checked by
  `WARN_ON_ONCE(folio_order(folio))` in `dax_folio_init()`.
- Folio has no references when made compound: checked in `dax_folio_init()`
  for an order above 0.
- Marks on removal: `xas_store()` of NULL clears them through
  `xas_init_marks()`; `fs/dax.c` removal paths clear none explicitly.
- `dax_delete_mapping_range()`: a removal path with no mark test and no
  `WARN_ON_ONCE` of its own; `dax_break_layout()` calls it only when no busy
  page was found.
- `dax_delete_mapping_entry()`: `WARN_ON_ONCE(!ret)` checks that an entry was
  found and removed.
- Removal sites: search for callers of `dax_disassociate_entry()`; each calls
  it under the `i_pages` lock before its `xas_store()`, which in
  `dax_insert_entry()` is inside `dax_lock_entry()`.
