- Views differ in one case only: `GICD_CTLR_DS` clear and Group 0 visible to
  the kernel (SCR_EL3.FIQ clear); with DS clear and no Group 0 both views are
  shifted alike and need no compensation.
- `gic_has_group0()`: probes through the PMR (write, read back, restore),
  with `gic_get_pribits()` for the value written; it does not access
  `GICD_CTLR`.
- Results: kept in `cpus_have_group0` and `cpus_have_security_disabled`; there
  is no gic_nonsecure_priorities static key in this tree.
- `dist_prio_irq` and `dist_prio_nmi`: start as `GICV3_PRIO_IRQ` and
  `GICV3_PRIO_NMI`; `gic_prio_init()` replaces them with
  `__gicv3_prio_to_ns()` of themselves when
  `cpus_have_group0 && !cpus_have_security_disabled`.
- The shift does not depend on pseudo-NMI support: `gic_prio_init()` runs
  before `gic_enable_nmi_support()` and tests neither
  `gic_prio_masking_enabled()` nor `gic_supports_nmi()`.
- `FLAGS_WORKAROUND_INSECURE` with DS clear and Group 0: `gic_prio_init()`
  sets `GICD_CTLR_DS`, then re-reads it; the re-read value decides whether the
  shift is applied.
