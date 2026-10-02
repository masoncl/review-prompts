- `keep`: its `VM_BUG_ON_FOLIO()` fires on `folio_test_lru()` or
  `folio_test_unevictable()`; the `folio_test_active()` assertions are after
  the hwpoison check and at `activate_locked`.
- `activate_locked`: `folio_set_active()`, `stat->nr_activate[]` and
  `PGACTIVATE` happen only when `folio_test_mlocked()` is false; an mlocked
  folio goes back unactivated.
- `activate_locked`: a swap-cache folio gets `folio_free_swap()` when
  `mem_cgroup_swap_full()` or `folio_test_mlocked()`; otherwise it stays in
  the swap cache.
- `activate_locked_split`: only sets `nr_pages` to 1 and subtracts the rest
  from `sc->nr_scanned`; it does not split and counts no fallback.
- `activate_locked_split` is reached only from a failed `folio_alloc_swap()`
  on a folio that is not large; a failed `split_folio_to_list()` goes to
  `activate_locked` with the folio still large.
- `shrink_folio_list()` has no lazyfree label and no `walk_done` label; a
  lazyfree folio is handled inline: `folio_ref_freeze(folio, 1)` fails to
  `keep_locked`, succeeds to the unlock before `free_it`.
- `free_it` has a third producer: a folio with buffers and no mapping, after
  `filemap_release_folio()`, is unlocked and `folio_put_testzero()` jumps
  there.
- Failed `folio_put_testzero()` in that branch: adds `nr_pages` to
  `nr_reclaimed` and does `continue` with the folio on no list; the holder of
  the other reference frees it.
- hwpoisoned large folio: `keep_locked`; only a small one takes the
  `unmap_poisoned_folio()`, `folio_put()`, `continue` exit.
- Folios that `demote_folio_list()` could not move: spliced back onto
  `folio_list` and the loop reruns from `folio_trylock()` with
  `do_demote_pass` false; with `sc->proactive` there is no rerun and they are
  returned to the caller.
- Swap step before unmap: `ttu_anon_folio()` in `mm/rmap.c` warns and fails
  the unmap of an anon folio whose `folio_test_swapbacked()` and
  `folio_test_swapcache()` differ.
- `keep_locked` and `keep` undo no earlier step: after a split the tails are
  already on `folio_list`; after `folio_alloc_swap()` the folio stays in the
  swap cache, dirty, on `keep_locked` (as the `may_enter_fs()` failure does).
