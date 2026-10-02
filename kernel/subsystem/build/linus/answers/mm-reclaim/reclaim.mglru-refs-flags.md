- `folio_update_gen()` and `lru_gen_set_refs()`: both take a `vma_flags`
  argument for `is_exec_file_folio()`.
- `folio_update_gen()`: a file folio in an executable VMA is promoted on the
  first young PTE seen, with neither flag set beforehand.
- `lru_gen_set_refs()` in `mm/vmscan.c`, called only from
  `folio_check_references()` and `walk_update_folio()`:

| Folio state | Effect | Returns |
|---|---|---|
| neither flag, exec file folio | clears `LRU_REFS_FLAGS`, sets `PG_workingset` | true |
| neither flag, other | sets `PG_referenced`, zeroes `LRU_REFS_MASK` | false |
| `folio_lru_refs()` > 1 | clears `LRU_REFS_FLAGS`, sets `PG_workingset` | true |
| any other state | calls `folio_mark_accessed()` | true |

- Last row: covers `PG_referenced` with a zero counter, and `PG_workingset`
  without `PG_referenced`; `lru_gen_set_refs()` returns true, so the folio is
  activated, without itself setting `PG_workingset`.
- Comment against code, `LRU_REFS_MASK`: the comment says it is not used for
  page table accesses; `lru_gen_set_refs()` reads it and, through
  `folio_mark_accessed()`, can increment it.
- Comment against code, promotion: the comment says later accesses set
  `PG_workingset`; on the rmap path that needs a non-zero counter or an exec
  file folio.
- Shared bits: accesses through file descriptors raise the same counter, so
  they count toward the `folio_lru_refs()` > 1 test.
- `folio_add_lru()` during a fault (`lru_gen_in_fault()`, no `PF_MEMALLOC`):
  sets `PG_active` if `PG_workingset` is set, else sets `PG_referenced`
  through `folio_mark_accessed()`.
- `lru_gen_refault()`, matching lruvec but not recent: counts
  `WORKINGSET_REFAULT_BASE` and changes no flag; the recent cases are under
  "Refault decision".
