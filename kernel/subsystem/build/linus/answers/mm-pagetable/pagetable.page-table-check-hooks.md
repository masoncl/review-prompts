- Hook names: there is no page_table_check_pte_set() and no
  page_table_check_zero() here. The PTE set hook is
  `page_table_check_ptes_set()`; the free/alloc check is
  `__page_table_check_zero()`, reached through `page_table_check_free()` and
  `page_table_check_alloc()`.
- Set hooks `page_table_check_ptes_set()`, `page_table_check_pmds_set()`,
  `page_table_check_puds_set()`: take `(mm, addr, pointer, entry, nr)`.
  `page_table_check_pmd_set()` and `page_table_check_pud_set()` are macros
  that pass `nr` = 1.
- Clear hooks: take `(mm, addr, old entry)`.
- `pte_user_accessible_page()` and the pmd/pud forms: take `(mm, addr, entry)`.
- Set hook on a populated slot: runs the clear accounting for the old entries
  it reads through the pointer, then counts the new one. A helper that
  replaces an entry in place calls the set hook only.
- Anon write test in `page_table_check_set()`: looks only at the write bit of
  the entry being installed. A read-only second mapping of an anon page whose
  first mapping is writable passes.
- Write test: runs only inside a set hook. x86 `ptep_set_access_flags()`
  stores with `set_pte()`, so a write upgrade there is not tested.
- Flag checks `page_table_check_pte_flags()`, `page_table_check_pmd_flags()`:
  `WARN_ON_ONCE()`, not `BUG_ON()`. They fire for a uffd-marked entry that is
  writable, or a uffd-marked swap entry that is a writable migration or
  device-private entry. `__page_table_check_puds_set()` has no flag check.
- Not counted even when user-accessible: PTEs with `pte_special()`, PMDs that
  map the huge zero folio (`page_table_check_huge_zero_pmd()`), and pfns
  failing `pfn_valid()`.
- `PageSlab()` page reaching `page_table_check_set()`,
  `page_table_check_clear()` or `__page_table_check_zero()`: `BUG_ON()`.
- `set_pmd_at()`, `set_pud_at()`: no generic definition; each architecture
  defines its own and must call the hook itself.
- Generic `ptep_set_wrprotect()` in `include/linux/pgtable.h`: goes through
  `set_pte_at()`, so it runs the set hook. The x86, arm64 and riscv overrides
  do not.
- arm64: the hooks are inside `__set_ptes_anysz()` and
  `__ptep_get_and_clear_anysz()`, so `__set_ptes()`, `__set_pmds()`,
  `__set_puds()` and `__ptep_get_and_clear()` are already hooked. `__set_pte()`
  and `__pte_clear()` are raw. A leading underscore does not tell which.
- In-place update that makes a counted entry non-accessible: must be
  accounted as a clear. Generic `pmdp_invalidate()` in
  `mm/pgtable-generic.c` gets it from the set hook in `pmdp_establish()`.
- `page_table_check_pte_clear_range()`: needed because a table PMD fails
  `pmd_user_accessible_page()`, so the PMD clear hook counts nothing for the
  PTEs below it. Pass the old PMD value after the slot is cleared, before the
  table is freed, as `retract_page_tables()` in `mm/khugepaged.c` does.
- `ARCH_SUPPORTS_PAGE_TABLE_CHECK`: also selected by s390, and by powerpc only
  `if !HUGETLB_PAGE`.
- **Unsafe usage**: calling a set hook after the new entry is stored. The hook
  then un-counts the new page instead of the old one.
  - Safe: hook first, then store, as `set_ptes()` in
    `include/linux/pgtable.h`; `__page_table_check_ptes_set()` reads the old
    entries with `ptep_get()`.
- **Unsafe usage**: calling a hook for a change that a callee already
  reported. A set hook ahead of a hooked setter counts the page twice; a
  second clear makes `page_table_check_clear()` hit `BUG_ON()` on a negative
  count.
  - Safe: rely on the hooked callee, as `ptep_clear_flush()` in
    `mm/pgtable-generic.c` relies on `ptep_get_and_clear()`.
- **Potentially unsafe usage**: writing a user entry with a raw store,
  `xchg()` or cmpxchg and no hook.
  - Unsafe: when the write changes the pfn, or changes what
    `pte_user_accessible_page()` (or the pmd/pud form) returns, in an mm other
    than `init_mm`. The counts drift and a later `page_table_check_clear()` or
    `__page_table_check_zero()` hits `BUG_ON()`.
  - Safe: when pfn and user-accessibility stay the same, as x86
    `ptep_set_wrprotect()`. `__page_table_check_ptes_set()` and
    `__page_table_check_pte_clear()` count by `pte_pfn()` and only for entries
    that pass `pte_user_accessible_page()`.
