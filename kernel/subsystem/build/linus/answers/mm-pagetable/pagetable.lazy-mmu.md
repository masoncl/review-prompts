- Locks and preemption: the four helpers take no lock and do not touch
  preemption themselves; only the arch hooks they call may (see the
  sleeping rule below); `apply_to_pte_range()` and `vmap_pte_range()` take no
  lock before they enter the section for `init_mm`.
- Read-back on Xen PV: `xen_batched_set_pte()` in `arch/x86/xen/mmu_pv.c`
  queues the write and memory is not updated, so `ptep_get()` returns the old
  entry until the flush.
- Nesting: counted in generic code, in `enable_count` and `pause_count` of
  `struct lazy_mmu_state` (`include/linux/mm_types_task.h`), a field of
  `struct task_struct`; code in a section may call code that opens its own.
- `lazy_mmu_mode_pause()` and `lazy_mmu_mode_resume()`: defined beside
  `lazy_mmu_mode_enable()`; between them enable and disable do nothing.
- Making a write take effect mid-section from generic code: use pause/resume,
  or a nested enable/disable pair; `arch_flush_lazy_mmu_mode()` has no generic
  stub, so generic code that calls it builds only where the architecture
  defines it.
- `pte_fn_t` callbacks of `apply_to_page_range()`: run with the mode active;
  `apply_to_pte_range()` enables it around the loop and never pauses.
- `kasan_populate_vmalloc_pte()` and `kasan_depopulate_vmalloc_pte()`: pause
  around their own `ptep_get()` and PTE write; that is where the pause pattern
  is, not in `apply_to_pte_range()`.
- Interrupt entry: nothing flushes or pauses the interrupted task's batch;
  the helpers return at once and `is_lazy_mmu_mode_active()` returns false,
  so writes made from the interrupt are not batched.
- `in_interrupt()`: also true while bottom halves are disabled, so a section
  opened under `spin_lock_bh()` batches nothing.
- Context switch on Xen PV: `xen_start_context_switch()` calls
  `__task_lazy_mmu_mode_pause()` on `prev`, `xen_end_context_switch()` calls
  `__task_lazy_mmu_mode_resume()` on `next`; no thread flag is used.
- arm64 `TIF_LAZY_MMU_PENDING`: only records that barriers are owed; whether
  the mode is active comes from `is_lazy_mmu_mode_active()`.
- `is_lazy_mmu_mode_active()`: defined in `include/linux/sched.h` only under
  `CONFIG_ARCH_HAS_LAZY_MMU_MODE`, with no stub, so a caller builds only
  under that option.
- **Potentially unsafe usage**: sleeping inside a section.
  - Unsafe: in generic code; `arch_enter_lazy_mmu_mode()` calls
    `preempt_disable()` on sparc and on powerpc when `radix_enabled()` is
    false.
  - Safe: leave the outermost section before sleeping and re-enter after, as
    `madvise_cold_or_pageout_pte_range()` does around `split_folio()`; only
    the outermost `lazy_mmu_mode_disable()` calls
    `arch_leave_lazy_mmu_mode()`.
  - Safe: arm64-only code, where `arch_enter_lazy_mmu_mode()` is empty, as in
    `split_kernel_leaf_mapping()` in `arch/arm64/mm/mmu.c`.
- **Unsafe usage**: `lazy_mmu_mode_enable()` and its
  `lazy_mmu_mode_disable()` called with different `in_interrupt()` values, for
  example enable, then `spin_lock_bh()`, then disable; the disable returns
  before it decrements `enable_count` and `arch_leave_lazy_mmu_mode()` never
  runs.
  - Safe: both calls inside the same lock, as `zap_pte_range()` does; the
    `in_interrupt()` test at the top of both helpers defines the requirement.
