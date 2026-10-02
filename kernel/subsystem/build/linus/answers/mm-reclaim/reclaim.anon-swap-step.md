- Checks before allocation: `sc->gfp_mask & __GFP_IO` and
  `folio_maybe_dma_pinned()`, both to `keep_locked`; this block does not test
  `sc->may_swap` or `total_swap_pages`.
- Lazyfree folios: kept out of this block by its `folio_test_swapbacked()`
  entry test; it does not call `folio_test_lazyfree()`.
- Large folio split test: there is no can_split_folio(); the code compares
  `folio_expected_ref_count(folio)` with `folio_ref_count(folio) - 1` and
  goes to `activate_locked` on a mismatch.
- `folio_alloc_swap()` in `mm/swapfile.c` takes only the folio; there is no
  add_to_swap().
- `folio_alloc_swap()` on a large folio without `CONFIG_THP_SWAP`: returns
  `-EAGAIN` at once, so every large folio takes the split fallback.
- `folio_alloc_swap()` success: the folio is in the swap cache, which holds
  one reference per page; the slots have swap count zero.
- `folio_mark_dirty()` after success: needed because a `MADV_FREE` folio can
  have clean PTEs while `PG_swapbacked` is set; unmap would leave it clean,
  the dirty test would skip `pageout()`, and `__remove_mapping()` would free
  it unwritten.
