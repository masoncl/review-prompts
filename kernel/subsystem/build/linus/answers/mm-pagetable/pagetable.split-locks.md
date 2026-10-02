- Configuration names: there is no USE_SPLIT_PTE_PTLOCKS or
  USE_SPLIT_PMD_PTLOCKS macro; code tests `CONFIG_SPLIT_PTE_PTLOCKS` and
  `CONFIG_SPLIT_PMD_PTLOCKS` (`mm/Kconfig`).
- `Documentation/mm/process_addrs.rst`: still writes USE_SPLIT_PMD_PTLOCKS;
  read it as `CONFIG_SPLIT_PMD_PTLOCKS`.
- `pud_lockptr()`: returns `&mm->page_table_lock` unconditionally; there is
  no split PUD lock.
- Two levels, example: the PMD-then-PTE pattern is in
  `try_collapse_pte_mapped_thp()` and `retract_page_tables()`;
  `collapse_pte_mapped_thp()` is only a wrapper.
- PTE lock already held, PMD lock wanted: only `spin_trylock()` on the PMD
  lock, as `zap_empty_pte_table()` in `mm/memory.c` does.
- When that trylock fails: drop the PTE lock and retake both in order, PMD
  first, then re-scan the table, as `zap_pte_table_if_empty()` does.
