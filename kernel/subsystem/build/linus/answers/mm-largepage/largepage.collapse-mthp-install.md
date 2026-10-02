- `pmdp_collapse_flush()`: runs for every order; a smaller collapse also
  detaches the whole PTE table.
- Install order below PMD order: `pmd_populate()` re-installs the table first,
  then `map_anon_folio_pte_nopf()` writes the PTEs. The table is live while the
  PTEs are written.
- Locks for that install: PMD lock, with the PTE lock taken inside it by
  `spin_lock_nested()` and `SINGLE_DEPTH_NESTING` when the two differ;
  `map_anon_folio_pte_nopf()` calls `update_mmu_cache_range()`, which on MIPS
  (`__update_tlb()`) walks the page table from the pgd, so the table must be
  linked first.
- PMD-order install: `pgtable_trans_huge_deposit()`, then
  `map_anon_folio_pmd_nopf()` in `mm/huge_memory.c`, which also calls
  `deferred_split_folio()`.
- Write barrier: there is no explicit `smp_wmb()` in `collapse_huge_page()`;
  `__folio_mark_uptodate()` supplies it for both orders.
- `map_anon_folio_pte_nopf()` in `mm/memory.c`: adds `nr_pages - 1` folio
  references; the collapse passes `uffd_wp` false.
- anon_vma write lock below PMD order: held until after the install, because
  PTEs outside the range still map folios that rmap can reach.
- mmu notifier range: only the collapsed sub-range, with `MMU_NOTIFY_CLEAR`;
  the TLB flush in `pmdp_collapse_flush()` covers the whole PMD.
- `hugepage_vma_revalidate()`: is passed the PMD-aligned address and requires
  the whole PMD range inside the VMA for every order.
