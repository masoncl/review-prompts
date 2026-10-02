- `contpte_convert()` in `arch/arm64/mm/contpte.c`: always clears all
  `CONT_PTES` entries with `__ptep_get_and_clear()`; the `__flush_tlb_range()`
  before `__set_ptes()` is skipped when `system_supports_bbml3()`.
- `__ptep_set_access_flags()`: inline wrapper in
  `arch/arm64/include/asm/pgtable.h`; the `cmpxchg_relaxed()` loop is in
  `__ptep_set_access_flags_anysz()` in `arch/arm64/mm/fault.c`, shared with
  `pmdp_set_access_flags()` and `huge_ptep_set_access_flags()`.
- `__ptep_set_access_flags_anysz()`: does not call `pgattr_change_is_safe()`;
  it masks `entry` to `PTE_RDONLY | PTE_AF | PTE_WRITE | PTE_DIRTY` itself.
- `__ptep_set_access_flags_anysz()` with `dirty`: flushes the local CPU only
  (`TLBF_NOWALKCACHE | TLBF_NOBROADCAST`); remote stale entries are left to a
  later fault, where `fix_spurious_fault()` in `mm/memory.c` calls
  `flush_tlb_fix_spurious_fault()` or `flush_tlb_fix_spurious_fault_pmd()`,
  from `handle_pte_fault()` and `__handle_mm_fault()`.
- Kernel splits: `split_pud()`, `split_pmd()`, `split_contpmd()` and
  `split_contpte()` in `arch/arm64/mm/mmu.c` overwrite the live entry with
  `set_pmd()`, `__set_pte()`, `__pud_populate()` or `__pmd_populate()`: no
  invalid step, no TLBI. There is no __set_pmd() or __set_pud().
- `stage2_try_break_pte()` in `arch/arm64/kvm/hyp/pgtable.c`: leaves the TLBI
  out when the walk has `KVM_PGTABLE_WALK_SKIP_BBM_TLBI`.
- `ARM64_WORKAROUND_2645198`: on affected CPUs the clear of a user-executable
  entry is followed by a TLBI before the new entry is written; see
  `huge_ptep_modify_prot_start()` in `arch/arm64/mm/hugetlbpage.c`.
- **Potentially unsafe usage**: writing a valid entry of another size (block
  to table, `PTE_CONT` set or cleared) over a valid entry with no invalid
  step.
  - Unsafe: while a CPU that lacks the capability can walk the table.
  - Safe: `split_kernel_leaf_mapping()` splits only when
    `system_supports_bbml3()`, or before capabilities are finalised with one
    CPU online and `page_alloc_available`; `linear_map_requires_bbml3` is
    only set when the boot CPU passed `cpu_supports_bbml3()`.
  - Safe: `linear_map_split_to_ptes()`: every other CPU waits in
    `wait_linear_map_split_to_ptes` on the idmap; the boot CPU calls
    `flush_tlb_kernel_range()` before it releases them.
  - Safe: `arch_kfence_init_pool()`: reaches `range_split_to_ptes()` only
    when `force_pte_mapping()` and `kfence_early_init` are both false, under
    `pgtable_split_lock`; with `kfence_early_init` false,
    `force_pte_mapping()` is false only when BBML3 is supported.
- **Potentially unsafe usage**: a plain store of a valid entry over a valid
  entry in a live user mm.
  - Unsafe: when the new value drops an access or dirty state that hardware
    may set meanwhile; the cases are the first two warnings of
    `__check_safe_pte_update()`, listed under "Changes allowed without
    break-before-make".
  - Safe: a `cmpxchg_relaxed()` loop on the entry, as in
    `__ptep_set_access_flags_anysz()` and `___ptep_set_wrprotect()`.
  - Safe: `__ptep_get_and_clear()` first, fold dirty and young into the new
    value, then set, as `contpte_convert()` does.
- **Potentially unsafe usage**: changing permissions in place on entries that
  have `PTE_CONT`.
  - Unsafe: when only part of the contiguous block is changed.
  - Safe: the whole block; `contpte_wrprotect_ptes()` first unfolds any
    partly covered block with `contpte_try_unfold_partial()`.
  - Safe: `contpte_ptep_set_access_flags()`: updates all `CONT_PTES` entries
    when the write bit is unchanged, and unfolds first when it changes.
