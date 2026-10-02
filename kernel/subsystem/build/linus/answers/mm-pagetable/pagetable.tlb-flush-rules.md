- `ptep_set_access_flags()` on x86 (`arch/x86/mm/pgtable.c`): stores the entry
  only when `dirty` is non-zero; returns non-zero whenever the entry differs,
  stored or not.
- Write-permission upgrade: pass a non-zero `dirty`, as `wp_page_reuse()` does;
  with `dirty` 0 x86 leaves the old entry in place.
- Generic `ptep_set_access_flags()` (`mm/pgtable-generic.c`): on a change calls
  `flush_tlb_fix_spurious_fault()`, whose default in `include/linux/pgtable.h`
  is `flush_tlb_page()`, not a local-only flush.
- `flush_tlb_fix_spurious_fault()` overrides, for example: empty on x86 and
  powerpc book3s64; local-only (`TLBF_NOBROADCAST`) on arm64.
- `handle_pte_fault()` with an unchanged entry: calls `fix_spurious_fault()` in
  `mm/memory.c`, which does nothing when `FAULT_FLAG_TRIED` is set or
  `FAULT_FLAG_WRITE` is clear.
- PMD level: `fix_spurious_fault()` calls `flush_tlb_fix_spurious_fault_pmd()`,
  a no-op by default; arm64 defines it.
- `pte_needs_flush()` generic (`include/asm-generic/tlb.h`): returns `true`
  always, so `change_pte_range()` queues every present entry it commits.
- `pte_needs_flush()` on x86 (`arch/x86/include/asm/tlbflush.h`): `false` when
  the old entry lacks `_PAGE_PRESENT`; otherwise any change of `_PAGE_RW`,
  `_PAGE_NX` or `_PAGE_USER`, in either direction, flushes; so read-only to
  writable through mprotect is flushed.
- x86 `pte_needs_flush()` otherwise skips the flush, among the flags that
  `pte_flags_need_flush()` names, only for: setting `_PAGE_DIRTY` or
  `_PAGE_ACCESSED`, clearing `_PAGE_ACCESSED`, software bits.
- `huge_pmd_needs_flush()` on x86: clearing `_PAGE_ACCESSED` does flush.
- `pte_needs_flush()` on arm64: any difference outside `PTE_SWBITS_MASK` on a
  valid entry flushes, upgrades included.
- `pte_needs_flush()` on powerpc book3s64 radix: the one override that skips a
  pure permission upgrade (`_PAGE_RWX`); it also skips setting `_PAGE_DIRTY`
  or `_PAGE_ACCESSED`.
- Dirty to clean: there is no ptep_clear_flush_dirty() here;
  `page_vma_mkclean_one()` in `mm/rmap.c` uses `ptep_clear_flush()`, then
  `set_pte_at()` with the write-protected clean entry.
- `ptep_clear_flush_young()`: generic flushes with `flush_tlb_page()` when the
  bit was set; the x86 override never flushes; x86 `pmdp_clear_flush_young()`
  does flush.
- `ptep_clear_flush()` generic: flushes only if `pte_accessible()`; on x86 a
  `PROT_NONE` entry is accessible only while `mm->tlb_flush_pending` is
  non-zero.
