- `madvise_free_huge_pmd()`: ignores the result of `split_folio()`; no retry.
- `try_to_split_thp_page()`: calls `split_huge_page_to_order()`, once; it puts
  the reference on failure only when `release` is true.
- `s390_wiggle_split_folio()` in `arch/s390/kernel/uv.c`: an in-tree retry
  loop; at most two tries, retries on `-EBUSY` only and only for a dirty file
  folio whose mapping can write back, unlocks and runs
  `filemap_write_and_wait_range()` between tries, keeps its reference.
- `lru_add_drain()` between tries: does not release a large folio; see
  "Reference counts at split".
- `madvise_cold_or_pageout_pte_range()`: PTE path does `folio_trylock()` under
  the PTL, then `folio_get()`; PMD path does `folio_get()`, drops the PTL,
  then `folio_lock()`.
- **Potentially unsafe usage**: sleeping in `folio_lock()` on a large folio
  while holding the reference taken for the split.
  - Unsafe: in a loop that retries on failure while other tasks do the same;
    each waiter's reference fails the lock holder's precheck in
    `__folio_split()` with `-EAGAIN`.
  - Safe: `folio_trylock()` under the PTL and back off without taking the
    reference, as `move_pages_pte()` in `mm/userfaultfd.c` does.
  - Safe: a single attempt with no retry, as the PMD path of
    `madvise_cold_or_pageout_pte_range()` does.
- **Potentially unsafe usage**: retrying on `-EBUSY`.
  - Unsafe: when nothing between tries changes the state tested by
    `folio_check_splittable()` or `filemap_release_folio()`.
  - Safe: after writeback has been waited for, as
    `s390_wiggle_split_folio()` does.
- After success: `move_pages_pte()` unlocks, puts and looks the folio up
  again from the PTE; the madvise PTE loops retake `pte_offset_map_lock()`
  and reprocess the same PTE.
