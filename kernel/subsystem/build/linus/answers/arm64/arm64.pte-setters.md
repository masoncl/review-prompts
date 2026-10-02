- `__set_pte_complete()`: decides from the entry bits with
  `pte_valid_not_user()`, not from the address or the mm.
- `__set_ptes_anysz()`: the common store path for kernel and user entries, at
  PTE, PMD and PUD size.
- `__sync_cache_and_tags()`: called unconditionally, once, before the first
  store, for `nr * stride` pages; its own tests select user-executable and
  tagged user-accessible entries.
- `__set_pte_nosync()` without `__set_pte_complete()`: `init_pte()` in
  `arch/arm64/mm/mmu.c`; the barrier comes from `pte_clear_fixmap()` at the
  end of `alloc_init_cont_pte()`.
- Higher levels differ from the PTE rule:

  | Setter | Barriers queued when |
  |---|---|
  | `set_pmd()` | `pmd_valid()`, user entries included |
  | `set_pud()` | `pud_valid()`, user entries included |
  | `set_p4d()`, `set_pgd()` | always |
  | `set_pmd_at()`, `set_pud_at()` | `pte_valid_not_user()`, through `__set_ptes_anysz()` |

- `set_swapper_pgd()`: used by `set_pmd()`, `set_pud()`, `set_p4d()` and
  `set_pgd()` for entries in `swapper_pg_dir`; the barriers for the entry it
  stores are never deferred: it issues `dsb(ishst)` and `isb()` itself while
  `rodata_is_rw`, and otherwise gets them from `flush_tlb_kernel_range()` in
  `pgd_clear_fixmap()`.
