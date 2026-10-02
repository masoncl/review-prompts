- There is no mm/pt_reclaim.c, try_get_and_clear_pmd or try_to_free_pte here;
  the zap path uses `zap_empty_pte_table()` and `zap_pte_table_if_empty()`
  in `mm/memory.c`.
- Zap path, when it reclaims: `pte_table_reclaim_possible()` needs
  `CONFIG_PT_RECLAIM`, `reclaim_pt`, and a range that covers the whole table
  (`end - start >= PMD_SIZE`); any entry left behind (`any_skipped`) cancels
  it.
- `reclaim_pt`: set only by `madvise_dontneed_single_vma()`, so the mm lock
  held is a VMA read lock or the mmap read lock.
- Zap path, free: `pte_free_tlb()` on the caller's gather, after the PTL is
  dropped.
- `retract_page_tables()`: takes no mmap lock and no VMA lock, not even by
  trylock; it holds `i_mmap_rwsem` for read, the pmd lock and the PTL.
- `file_backed_vma_is_retractable()`: skips a VMA with `anon_vma`, with
  `userfaultfd_protected()`, or with `VMA_MAYBE_GUARD_BIT`; it is called
  again under the PTL.
- `collapse_pte_mapped_thp()`: a wrapper; the work and
  `mmap_assert_locked()` are in `try_collapse_pte_mapped_thp()`, which
  returns early for `userfaultfd_protected()`.
- `try_collapse_pte_mapped_thp()`: takes the pmd lock before the PTL for
  step 2 only for a private VMA with `userfaultfd_armed()`; otherwise it
  holds the PTL alone for step 2, drops it, and at step 4 takes the pmd
  lock, then the PTL, with a `pmd_same()` recheck.
