- `call_on_irq_stack()` masks all of DAIF with `save_and_disable_daif`, in
  two windows.
- First window: from entry up to `restore_irq` just before `blr x1`.
- Second window: from the return of `func` up to `restore_irq` before `ret`.
- `func` runs with the caller's DAIF.
- Old SP: not stored; it is recovered from x29, which points at the frame
  record pushed on the old stack.
- Old x18: stored by `scs_save` in the task's `thread_info` and reloaded by
  `scs_load_current`, not kept in the frame record.
- Each call starts at `irq_stack_ptr + IRQ_STACK_SIZE` and at the base of
  `irq_shadow_call_stack_ptr`.
- **Unsafe usage**: taking an IRQ or FIQ between loading x18 with another
  shadow stack and moving SP off the task stack.
  - Unsafe: `do_interrupt_handler()` sees `on_thread_stack()` true and calls
    `call_on_irq_stack()`, whose `scs_save` overwrites the task's saved SCS
    pointer with the foreign x18.
  - Safe: all of DAIF masked across both moves, as `call_on_irq_stack()`
    and `cpu_switch_to()` do with `save_and_disable_daif`.
- **Unsafe usage**: calling `call_on_irq_stack()` while already on the IRQ
  stack, or from preemptible context.
  - Unsafe: SP and x18 are reset to the start of the per-CPU stacks, over
    frames still in use.
  - Safe: `do_interrupt_handler()`, which tests `on_thread_stack()` first
    and runs with IRQs masked.
  - Safe: `do_softirq_own_stack()`; `do_softirq()` and `__irq_exit_rcu()`
    reach it only when `in_interrupt()` is false, with IRQs disabled.
