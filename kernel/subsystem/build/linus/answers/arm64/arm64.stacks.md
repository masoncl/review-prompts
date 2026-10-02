- Range test: `stackinfo_on_stack()` in
  `arch/arm64/include/asm/stacktrace/common.h`, on a `struct stack_info`
  from a `stackinfo_get_irq()`-style getter in
  `arch/arm64/include/asm/stacktrace.h`.
- `stackinfo_on_stack()` returns `false` for `stackinfo_get_unknown()`,
  which the SDEI getters become without `CONFIG_ARM_SDE_INTERFACE`.
- Named wrappers: only `on_irq_stack()`, `on_task_stack()` and
  `on_thread_stack()`. There is no on_overflow_stack, on_sdei_stack or
  on_accessible_stack.
- Getters for the IRQ, overflow and SDEI stacks read this CPU's pointer;
  `kunwind_stack_walk()` in `arch/arm64/kernel/stacktrace.c` uses them only
  under `STACKINFO_CPU()` and `STACKINFO_SDEI()`.
- EFI runtime stack: one global stack, `efi_rt_stack_top`, allocated by
  `arm64_efi_rt_init()` in `arch/arm64/kernel/efi.c` with
  `arch_alloc_vmap_stack(THREAD_SIZE, ...)`.
- EFI runtime stack: getter `stackinfo_get_efi()` under `CONFIG_EFI`;
  `current_in_efi()` in `arch/arm64/include/asm/efi.h` says the task is on
  it.
- EFI runtime stack: no shadow call stack; `__efi_rt_asm_wrapper` saves x18
  and, under `CONFIG_SHADOW_CALL_STACK`, restores it if firmware changed it.
- IRQ stack: allocated only by `arch_alloc_vmap_stack()`, in
  `init_irq_stacks()`.
- `overflow_stack`: defined unconditionally in `arch/arm64/kernel/traps.c`.
- SDEI stacks: allocated in `sdei_arch_get_entry_point()`, called from
  `sdei_probe()` in `drivers/firmware/arm_sdei.c`, not from `init_IRQ()`.
- SDEI shadow call stacks: `sdei_shadow_call_stack_normal_ptr` and
  `sdei_shadow_call_stack_critical_ptr`, allocated by `init_sdei_scs()`
  only when `scs_is_enabled()`.
