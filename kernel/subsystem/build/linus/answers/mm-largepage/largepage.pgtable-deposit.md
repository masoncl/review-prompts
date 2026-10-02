- `has_deposited_pgtable()` in `mm/huge_memory.c`: the test `zap_huge_pmd()`
  uses; it is static.
- `has_deposited_pgtable()` conditions, in order:
  1. `arch_needs_pgtable_deposit()`: every huge PMD has one.
  2. huge zero PMD: has one unless the VMA is DAX.
  3. otherwise: only if the folio is anonymous, which covers migration and
     device-private PMDs of anonymous folios.
- `arch_needs_pgtable_deposit()`: overridden only by powerpc book3s64, true
  when radix is not enabled.
- `insert_pmd()` (DAX, PFN map, huge zero in a DAX VMA): deposits only when
  `arch_needs_pgtable_deposit()`.
- The three operations use different tests:

| Operation | Test for a deposit |
|---|---|
| `zap_huge_pmd()` | `has_deposited_pgtable()`, by entry and folio |
| `__split_huge_pmd_locked()` | by VMA: anonymous always withdraws; otherwise only `arch_needs_pgtable_deposit()` |
| `move_huge_pmd()` | `pmd_move_must_withdraw()` |

- `pmd_move_must_withdraw()`, generic: PMD locks differ and
  `vma_is_anonymous()`; powerpc hash returns true always.
- `move_pages_huge_pmd()`: moves the deposit to the destination on every
  successful move.
- Order: `zap_huge_pmd()` withdraws only after the PMD is cleared, and
  `__split_huge_pmd_locked()`, for a present PMD, only after it is cleared or
  invalidated; `hash__pmdp_huge_get_and_clear()` zeroes the deposited table.
- **Potentially unsafe usage**: installing an anonymous huge PMD without
  `pgtable_trans_huge_deposit()` and `mm_inc_nr_ptes()`.
  - Unsafe: when the PMD was none and no table was added to its
    `pmd_huge_pte()` list for it; `__split_huge_pmd_locked()` withdraws
    unconditionally in an anonymous VMA, and the generic
    `pgtable_trans_huge_withdraw()` has no NULL test on `pmd_huge_pte()`.
  - Safe: when the entry replaced already had a deposit, as
    `do_huge_zero_wp_pmd()` does over a huge zero PMD and
    `remove_migration_pmd()` does over a migration PMD.
  - Safe: `move_huge_pmd()` when `pmd_move_must_withdraw()` is false; the old
    and new PMD share one `pmd_huge_pte()` list, so the deposit of the old
    entry serves the new one.
  - Safe: `collapse_huge_page()` deposits the old PTE table without
    `mm_inc_nr_ptes()`; that table was already counted.
