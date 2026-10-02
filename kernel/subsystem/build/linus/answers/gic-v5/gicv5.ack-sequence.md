- `gicv5_handle_irq()` after a valid acknowledge: `gsb_ack()`, `isb()`, then
  `gic_insn(0, CDEOI)`, then `handle_irq_per_domain()`.
- Invalid acknowledge: returns before `gsb_ack()`, `isb()` and the
  `gic_insn(0, CDEOI)`.
- `handle_irq_per_domain()`: returns `void`; both failure paths log with
  `pr_err_once()`.
- Unknown type: returns with no CDDI; the priority has already been dropped.
- `generic_handle_domain_irq()` returns non-zero: calls `gicv5_hwirq_eoi()`,
  which only deactivates (CDDI); the drop was already done.
