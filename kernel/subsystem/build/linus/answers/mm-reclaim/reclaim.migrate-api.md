- Negative return: only `-ENOMEM`, when `get_new_folio()` returns NULL.
  `-EAGAIN`, `-EBUSY` and other per-folio errors are never returned; they are
  counted.
- `-ENOMEM` on a large folio: `migrate_pages_batch()` first tries
  `try_split_folio()`; if the split works the folio counts as one failure
  and migration continues with no error. With `MR_NUMA_MISPLACED` this split
  is not tried.
- `-ENOMEM` return: folios already unmapped in the batch are still moved
  first. `from` then holds every folio that was not migrated: the failed
  ones, every untried folio and any split pieces.
- Return 0: forced whenever `from` is empty at the end. A large folio that
  was split and whose pieces all migrated then does not count as a failure.
- Positive return: counts folios, not list entries; a split large folio
  whose pieces fail to migrate leaves several pieces on `from` for one
  counted failure.
- `*ret_succeeded`: base pages, not folios, despite the kerneldoc.
- Folios left on `from`: the caller owns them and must consume the list.
  `putback_movable_pages()` is the usual way, not the only one.
  - `demote_folio_list()` in `mm/vmscan.c` leaves them on the list;
    `shrink_folio_list()` splices them back onto `folio_list`.
  - `damon_migrate_folio_list()` in `mm/damon/ops-common.c` drops
    `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE` and calls `folio_putback_lru()`
    itself.
