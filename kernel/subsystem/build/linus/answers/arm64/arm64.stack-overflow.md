- `THREAD_ALIGN`: `2 * THREAD_SIZE` unconditionally, in
  `arch/arm64/include/asm/memory.h`.
- The check has no `#ifdef` and no `.if \el`; `arch/arm64/Kconfig` selects
  `VMAP_STACK` unconditionally.
- It is in every `kernel_ventry`, including the copies in
  `__bp_harden_el1_vectors`.
- The property is alignment and size, not the allocator: the init task
  stack is placed by `RW_DATA(..., THREAD_ALIGN)` in
  `arch/arm64/kernel/vmlinux.lds.S`.
- `IRQ_STACK_SIZE` and `SDEI_STACK_SIZE` both equal `THREAD_SIZE`.
- Bit `THREAD_SHIFT` of SP set: `kernel_ventry` first moves SP to the top of
  `overflow_stack` and range-tests the old SP against
  `OVERFLOW_STACK_SIZE`.
- Old SP in range: SP and x0 are restored and the normal handler runs.
- Old SP out of range: `__bad_stack`, then `handle_bad_stack()`.
- `overflow_stack` is only `__aligned(16)`, so the bit is arbitrary there.
  SP below the overflow stack is caught only if the bit happens to be set;
  `__bad_stack` then restarts from the top of the overflow stack.
- `panic_bad_stack()`: calls `nmi_panic()`, then `cpu_park_loop()`.
- **Potentially unsafe usage**: SP on a stack whose base is not
  `THREAD_ALIGN`-aligned, or that is larger than `THREAD_SIZE`.
  - Unsafe: while an exception can enter through `kernel_ventry`; a valid SP
    can have bit `THREAD_SHIFT` set and end in `__bad_stack`, or an overflow
    can leave it clear.
  - Safe: allocated with `arch_alloc_vmap_stack()` and at most
    `THREAD_SIZE`, as `init_irq_stacks()` does.
  - Safe: `overflow_stack`, which `kernel_ventry` range-tests itself.
  - Safe: `early_init_stack`, defined in `arch/arm64/kernel/vmlinux.lds.S`
    and used by `primary_entry` and `__primary_switch` in
    `arch/arm64/kernel/head.S` before `__primary_switched` writes
    `vbar_el1`.
