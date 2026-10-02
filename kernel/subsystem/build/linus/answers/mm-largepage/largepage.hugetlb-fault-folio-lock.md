- The lock holder that matters: `hugetlb_wp()` on the `cow_from_owner` path
  keeps the anon folio locked while it drops and retakes the fault mutex.
- `cow_from_owner`: set only when `folio_test_anon(old_folio)`, so only anon
  folios are ever locked across that window.
- `hugetlb_no_page()`: unlocks a page cache folio before it calls
  `hugetlb_wp()`; a new anon folio stays locked.
- **Potentially unsafe usage**: a blocking folio lock while the fault mutex
  is held.
  - Unsafe: on an anon folio that is already mapped; the sleeper holds the
    mutex that `hugetlb_wp()` needs to retake before it can unlock.
  - Safe: on a page cache folio, as `hugetlb_no_page()` and
    `remove_inode_single_folio()` do; `hugetlb_wp()` never drops the mutex
    for a folio that is not anon.
  - Safe: on a new anon folio not yet mapped, as `hugetlb_no_page()` does;
    the `cow_from_owner` path of `hugetlb_wp()` only runs on a folio found
    under a present PTE.
