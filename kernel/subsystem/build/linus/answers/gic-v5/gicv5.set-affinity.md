- Target CPU: with `force`, `cpumask_first()` of the mask, online or not;
  without, `cpumask_any_and()` of the mask and `cpu_online_mask`.
- Return value on success: `IRQ_SET_MASK_OK_DONE`.
- CPU with no IAFFID: `gicv5_irs_cpu_to_iaffid()` prints an error and returns
  `-ENODEV`, not `-EINVAL`; the callback returns it before `GIC CDAFF` and
  before the effective affinity is updated.
- `gicv5_irs_cpu_to_iaffid()`: tests only the `valid` flag of `cpu_iaffid`; it
  has no present or online test.
- `cpu_iaffid`: filled at IRS probe, not at CPU bring-up, by
  `gicv5_irs_of_init_affinity()` or `gic_acpi_parse_iaffid()`; a CPU whose
  IAFFID exceeds the IRS IAFFID bits is left invalid.
- **Potentially unsafe usage**: calling `gicv5_iri_irq_set_affinity()` without
  `force` and with a mask that holds no online CPU.
  - Unsafe: the callback does not range-check the result of
    `cpumask_any_and()` before `gicv5_irs_cpu_to_iaffid()` indexes per-CPU
    data with it.
  - Safe: through `irq_do_set_affinity()` in `kernel/irq/manage.c`, which
    passes only a mask already reduced to online CPUs when `force` is false.
