- `PageAnonExclusive()` on a hugetlb tail page: reads the head page's bit, no
  warning.
- `SetPageAnonExclusive()` and `ClearPageAnonExclusive()` on a hugetlb tail
  page: `VM_BUG_ON_PGFLAGS()`.
- `__folio_add_anon_rmap()`: takes `enum pgtable_level`; there is no
  RMAP_LEVEL_PMD here, the value is `PGTABLE_LEVEL_PMD`.
- `PGTABLE_LEVEL_PMD` with `RMAP_EXCLUSIVE`: sets the bit only on the `page`
  argument, so the caller passes the head page.
- `folio_move_anon_rmap()`: writes `folio->mapping` only; it does not set the
  flag.
- Write-fault reuse of a large PTE-mapped folio: `do_wp_page()` calls
  `SetPageAnonExclusive()` on `vmf->page` alone, under the page table lock,
  without the folio lock and without `folio_move_anon_rmap()`.
- `__folio_remove_rmap()`: does not clear the flag, so an unmapped page of a
  large folio can keep a stale set bit.
- Stale bits: `__split_folio_to_order()` drops them only from the pages that
  become new heads.
- `folio_try_share_anon_rmap_pte()` and `folio_try_share_anon_rmap_pmd()`:
  need the entry cleared or invalidated first, not flushed;
  `try_to_migrate_one()` defers the TLB flush when `should_defer_flush()`.
- Device-private folio: `__folio_try_share_anon_rmap()` clears the flag with
  no pin test, and `__folio_try_dup_anon_rmap()` skips the pin test.
- Fork, PTE batch: `__folio_try_dup_anon_rmap()` returns `-EBUSY` before it
  clears anything if the folio may be pinned and any page in the range is
  exclusive.
- Fork, after that `-EBUSY`: `copy_present_ptes()` returns `-EAGAIN`, then
  retries one page at a time with a preallocated folio.
- PMD split with `freeze`: `__split_huge_pmd_locked()` clears the head flag
  with `folio_try_share_anon_rmap_pmd()`, adds no PTE rmap, and writes the
  exclusivity into each PTE migration entry.
- PMD split with `freeze`, share fails: it splits as if `freeze` were false
  and leaves the failure to `try_to_migrate_one()`.
- PMD split of a migration entry: exclusivity comes from the entry type; page
  flags are not touched.
- **Unsafe usage**: `ClearPageAnonExclusive()` on a mapped page outside the
  rmap helpers.
  - Safe: `folio_try_share_anon_rmap_pte()` after the entry is cleared, as
    `try_to_migrate_one()` does; `__folio_try_share_anon_rmap()` holds the
    barriers that pair with `gup_must_unshare()`.
  - Safe: `folio_try_dup_anon_rmap_ptes()` at fork with the source entry
    still present, under `write_protect_seq`; `folio_needs_cow_for_dma()`
    asserts it.
  - Safe: `__ClearPageAnonExclusive()` on a folio whose reference count is
    zero, as `free_huge_folio()` does.
