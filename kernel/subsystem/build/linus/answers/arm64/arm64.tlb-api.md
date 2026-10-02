- Rows that differ from the older API; all are in
  `arch/arm64/include/asm/tlbflush.h` except `tlb_flush()` in
  `arch/arm64/include/asm/tlb.h`:

| Function | Scope | Walk cache dropped | Waits |
|---|---|---|---|
| `flush_tlb_page()` | one user page, all CPUs | no, leaf only | yes |
| `__flush_tlb_page()` | one user page, level 3 | never | unless `TLBF_NOSYNC` |
| `__flush_tlb_range()` | user range, caller's stride and level | unless `TLBF_NOWALKCACHE` | unless `TLBF_NOSYNC` |
| `__flush_tlb_kernel_pgtable()` | one kernel address, all CPUs | yes | yes, plus `isb()` |
| `local_flush_tlb_all()` | everything, this CPU only | yes | `dsb(nsh)` plus `isb()` |
| `arch_tlbbatch_add_pending()` | user range, level 3 | no | no |
| `arch_tlbbatch_flush()` | no TLBI except the `__repeat_tlbi_sync()` repeat | n/a | yes |
| `tlb_flush()` | the mmu_gather range | if `tlb->freed_tables` or `tlb->unshared_tables` | yes |

- `__flush_tlb_range()`: signature is `(vma, start, end, stride, tlb_level,
  flags)`; it takes no `bool` last-level argument.
- Not defined anywhere in this tree: __flush_tlb_range_nosync(),
  __flush_tlb_page_nosync(), flush_tlb_page_nosync(),
  local_flush_tlb_page_nonotify(), local_flush_tlb_contpte(),
  flush_tlb_pgtable().
- `local_flush_tlb_page()` and `flush_tlb_kernel_page()`: defined by other
  architectures only; arm64 defines neither.
- No-wait, local and no-notify variants: `__flush_tlb_range()` or
  `__flush_tlb_page()` with `TLBF_NOSYNC`, `TLBF_NOBROADCAST`,
  `TLBF_NONOTIFY`; see "Invalidation flags".
- `tlb_flush()` with `tlb->fullmm`: issues `flush_tlb_mm()` only if
  `tlb->freed_tables`, otherwise no invalidation at all.
- `flush_tlb_kernel_range()` leftovers: walk-cache entries for the
  intermediate levels; `__flush_tlb_kernel_pgtable()` drops them for one
  address, and code in `arch/arm64/mm/mmu.c` calls it after clearing a table
  entry and before freeing the table, for example `pmd_free_pte_page()`.
