- Target order: `min_order_for_split()` in `mm/huge_memory.c`; 0 for anon,
  `mapping_min_folio_order()` for a file folio.
- Truncated file folio (`folio->mapping` NULL): `min_order_for_split()` returns
  0; the split then fails with `-EBUSY` in `folio_check_splittable()`.
- Return value on failure: `memory_failure()` returns `-EHWPOISON`, not
  `-EBUSY`.
- `-EBUSY`: is what `soft_offline_in_use_page()` returns; it does not split at
  all when the minimum order is above 0.
- Before the return: `memory_failure()` re-reads `page_folio(p)` and calls
  `kill_procs_now()`, which signals with `forcekill` true.
- Tasks signalled by `kill_procs_now()`: only those `task_early_kill()`
  selects, not every task that maps the page.
  - with `MF_ACTION_REQUIRED`: `current`, if its mm maps the page or, for a
    file folio, has a VMA that covers it;
  - early-kill tasks (`PF_MCE_EARLY` or `sysctl_memory_failure_early_kill`).
- `try_to_split_thp_page()`: always unlocks; calls `put_page()` only when the
  split failed and `release` is true.
- After the failure: `memory_failure()` does not call
  `hwpoison_user_mappings()`; the folio stays in use with `PG_hwpoison` on `p`.
- `PG_has_hwpoisoned` afterwards: for example it makes `do_set_pmd()` refuse a
  PMD mapping and `shmem_file_read_iter()` copy page by page.
