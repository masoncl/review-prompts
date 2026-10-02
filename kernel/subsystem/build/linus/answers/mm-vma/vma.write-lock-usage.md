- `mmap_write_downgrade()`: calls `vma_end_write_all()` just as
  `mmap_write_unlock()` does, so every VMA write lock ends at a downgrade.
- `hugepage_vma_revalidate()`: tests `thp_vma_suitable_order()` with
  `PMD_ORDER` whatever order is collapsed, so the one VMA that
  `collapse_huge_page()` write-locks covers the whole PTE table.
- `collapse_huge_page()`: frees no page table; it deposits the PTE table with
  `pgtable_trans_huge_deposit()` at PMD order, and re-installs it with
  `pmd_populate()` at a smaller order or on failure.
- `collapse_huge_page()` takes an `order`; below PMD order it keeps
  `anon_vma_lock_write()` until the PMD is re-installed, at PMD order it drops
  it after `__collapse_huge_page_isolate()`.
- PTE lock in `collapse_huge_page()`: taken by `pte_offset_map_lock()` on the
  saved `_pmd`, after `tlb_remove_table_sync_one()`;
  `__collapse_huge_page_isolate()` runs with it held.
- There is no __replace_page() here; `__uprobe_write()` in
  `kernel/events/uprobes.c` changes the one PTE, under the PTE lock that
  `folio_walk_start()` took.
- `uprobe_write()`: can free a PTE table; when `__uprobe_write()` returns a
  positive value (unregister zapped the page and the file folio is
  PMD-mappable) it calls `collapse_pte_mapped_thp()`.
- Callers of `uprobe_write()` hold the mmap write lock: for example
  `register_for_each_vma()`, `unapply_uprobe()` and x86
  `arch_uprobe_optimize()` take it; none calls `vma_start_write()`.
- `ptdump_walk_pgd()`: write-locks `mm` and, when `mm` is not `init_mm`, also
  `init_mm`; `walk_page_range_debug()` asserts both.
- `ptdump_walk_pgd()` is read-only: the callbacks use `ptep_get()`,
  `pmdp_get()` and the like, and `walk_pte_range()` maps a user PTE table with
  `pte_offset_map()`, without the PTE lock.
- ptdump's mm: x86 walks `current->mm`, user range included
  (`ptdump_walk_pgd_level_debugfs()`, called from
  `arch/x86/mm/debug_pagetables.c`); write mode is needed for the reason
  under "Freeing page tables".
- **Potentially unsafe usage**: under the mmap write lock, clearing a PMD
  entry that points to a PTE table, with no `vma_start_write()` on the VMA.
  - Unsafe: when the table still holds entries or is put back later; a
    per-VMA-lock fault fills the empty PMD through `__pte_alloc()`, and
    `collapse_huge_page()` warns on `!pmd_none()` before `pmd_populate()`,
    under `CONFIG_DEBUG_VM`.
  - Unsafe: when the table is freed at once with `pte_free()`; a walker
    inside `pte_offset_map_lock()` still holds it.
  - Safe: after `vma_start_write()` and `anon_vma_lock_write()`, as
    `collapse_huge_page()` does.
  - Safe: without `vma_start_write()`, when the folio lock is held, every
    entry was cleared under the PTE lock, the PMD is cleared under the PMD and
    PTE locks, and the table goes to `pte_free_defer()`, as
    `try_collapse_pte_mapped_thp()` does; `pte_offset_map_lock()` in
    `mm/pgtable-generic.c` holds `rcu_read_lock()` and rechecks the PMD.
