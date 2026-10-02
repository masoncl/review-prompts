- `gic_insn(0, CDEOI)`: issued in `gicv5_handle_irq()`, straight after the
  `gsb_ack()` and `isb()` that follow the acknowledge.
- Order for one interrupt: acknowledge, drop, flow handler and action, then
  CDDI from `irq_eoi`.
- The handler therefore runs with the running priority already dropped and
  the interrupt not yet deactivated.
- Reason in the comment above it: to be able to receive the next interrupts
  when a handler runs long or the CPU directly enters a guest.
