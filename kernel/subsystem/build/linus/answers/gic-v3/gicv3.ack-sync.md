- Regular interrupt in `__gic_handle_irq_from_irqson()`: `gic_unmask_pnmis()`
  runs between `gic_read_iar()` and `gic_complete_ack()`, so with
  `gic_prio_masking_enabled()` a pseudo-NMI can be taken before the priority
  drop and the `isb()`.
- `__gic_handle_irq_from_irqsoff()`: writes the saved PMR back between
  `gic_read_iar()` and `gic_complete_ack()`; it does not touch DAIF.
- `gic_complete_ack()`: the one step that `__gic_handle_irq()` and
  `__gic_handle_nmi()` run between the `gic_irqnr_is_special()` test and
  `generic_handle_domain_irq()` or `generic_handle_domain_nmi()`.
- **Unsafe usage**: reading `ICC_RPR_EL1` to classify the interrupt after
  `gic_complete_ack()`; with `supports_deactivate_key` the EOIR write has
  already dropped the running priority.
  - Safe: read it after `gic_read_iar()` and before `gic_complete_ack()`, as
    `__gic_handle_irq_from_irqson()` does with `gic_rpr_is_nmi_prio()`.
- `gic_deactivate_unhandled()` with `supports_deactivate_key`: writes DIR
  only, through `gic_write_dir()`, and only for `irqnr < 8192`; it does not
  write EOIR again.
- `gic_deactivate_unhandled()` without `supports_deactivate_key`: writes
  `ICC_EOIR1_EL1`, then `isb()`.
- Non-zero return from the handler call: `-EINVAL` from `handle_irq_desc()`
  in `kernel/irq/irqdesc.c` for no mapping; it gets the `WARN_ONCE` and
  `gic_deactivate_unhandled()`.
- Names: `gic_write_eoir` is only a member of `struct gic_common_ops` in the
  KVM selftests, not a kernel function, and there is no ARCH_GICV3_SPECIAL;
  the driver uses `write_gicreg()` on `ICC_EOIR1_EL1` and
  `gic_irqnr_is_special()`.
- `gic_read_iar_common()` in `arch/arm64/include/asm/arch_gicv3.h`: always
  issues `dsb(sy)` after the IAR read; it is not an erratum workaround.
- `gic_read_iar_cavium_thunderx()`: used under
  `ARM64_WORKAROUND_CAVIUM_23154`; returns 0x3ff when `ICC_AP1R0_EL1` did not
  change across the IAR read.
