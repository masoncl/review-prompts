- `__switch_to()` in `arch/arm64/kernel/process.c`: issues `dsb(ish)`; it
  does not test or clear `TIF_LAZY_MMU_PENDING` and has no `isb()` of its own.
- Preempted task: the flag stays set in its thread flags; `dsb(ishst)` and
  `isb()` are issued when that task itself next flushes, possibly on another
  CPU.
- Interrupt handler: `is_lazy_mmu_mode_active()` in `include/linux/sched.h`
  is false under `in_interrupt()`, so its own stores get `emit_pte_barriers()`
  at once; the interrupted task's flag is untouched.
- Callers use `lazy_mmu_mode_enable()`, `lazy_mmu_mode_disable()`,
  `lazy_mmu_mode_pause()` and `lazy_mmu_mode_resume()` in
  `include/linux/pgtable.h`; generic and arm64 code reach the `arch_` hooks
  only through these.
- State: `enable_count` and `pause_count` in `current->lazy_mmu_state`;
  `arch_enter_lazy_mmu_mode()` is empty on arm64.
- `lazy_mmu_mode_disable()`: emits pending barriers at every nesting level,
  not only the outermost; so does the first `lazy_mmu_mode_pause()`.
- In interrupt context all four calls do nothing; while paused,
  `lazy_mmu_mode_enable()` and `lazy_mmu_mode_disable()` do nothing and a
  nested pause or resume only changes `pause_count`.
- Sleeping inside a section is allowed on arm64: `split_kernel_leaf_mapping()`
  in `arch/arm64/mm/mmu.c` holds a mutex and allocates inside one.
- **Unsafe usage**: accessing a kernel address whose valid entry was written
  in the current lazy MMU section, before the pending barriers are emitted.
  - Unsafe: the access can take a translation fault; `__do_kernel_fault()`
    recovers through `is_spurious_el1_translation_fault()`, with a
    rate-limited warning.
  - Safe: access after `lazy_mmu_mode_disable()`, as callers of
    `vmap_pte_range()` do.
  - Safe: store inside `lazy_mmu_mode_pause()` / `lazy_mmu_mode_resume()`, as
    `kasan_populate_vmalloc_pte()` in `mm/kasan/shadow.c`; the store then gets
    immediate barriers.
  - Safe: arm64's `ptep_try_set()`, defined under `CONFIG_ARM64_CONTPTE`,
    which calls `emit_pte_barriers()` directly and ignores the mode; without
    the option the generic stub in `include/linux/pgtable.h` stores nothing.
