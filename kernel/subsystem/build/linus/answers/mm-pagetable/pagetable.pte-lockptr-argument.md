- What is read: with `CONFIG_SPLIT_PTE_PTLOCKS`, only the value `*pmd`; the
  address of the entry is not used, so a pointer to a stack copy is valid.
- Without `CONFIG_SPLIT_PTE_PTLOCKS`: the argument is ignored and
  `&mm->page_table_lock` is returned, so a wrong argument shows no symptom.
- **Potentially unsafe usage**: `pte_lockptr(mm, pmd)` on the live PMD entry.
  - Unsafe: when nothing keeps the entry unchanged between the test that it
    points to a PTE table and the call; `pmd_page()` of a none, huge or
    non-present entry yields a lock in an unrelated page.
  - Safe: on a stack copy read once and validated, as `__pte_offset_map()`
    with `pte_offset_map_lock()` do in `mm/pgtable-generic.c`.
  - Safe: on the live entry while holding `pmd_lock()` and after validating
    under it, as `retract_page_tables()` does with `check_pmd_state()`;
    writers of the entry such as `pmd_install()` take that lock.
- **Unsafe usage**: `pte_lockptr()` on a table constructed for `init_mm`;
  `pagetable_pte_ctor()` never initialises that lock.
  - Safe: take no PTE lock for `init_mm`, as `apply_to_pte_range()` in
    `mm/memory.c` does with `pte_offset_kernel()`.
- `pmd_lockptr()` is the opposite: with `CONFIG_SPLIT_PMD_PTLOCKS`,
  `pmd_pgtable_page()` masks the address of the entry, so it needs the
  pointer into the live PMD table, never a copy.
- Call sites: four in the tree; other code gets the lock from
  `pte_offset_map_lock()`, `pte_offset_map_ro_nolock()` or
  `pte_offset_map_rw_nolock()`.
