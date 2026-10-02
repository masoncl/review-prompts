- Decision: `gic_init_bases()` disables `supports_deactivate_key` when
  `is_hyp_mode_available()` is false; nothing else changes it.
- `gic_check_eoimode()` is the GICv2 driver's, in
  `drivers/irqchip/irq-gic.c`; here no devicetree region takes part.
- `is_hyp_mode_available()` on arm64: true when every CPU booted at EL2, or
  when `is_pkvm_initialized()`; a host that runs at EL1 after booting at EL2
  uses the split mode.

| Case | Priority drop | Deactivation |
|---|---|---|
| key off | `irq_eoi`: `gic_eoi_irq()` | same `ICC_EOIR1_EL1` write |
| key on | `gic_complete_ack()`, before the flow handler | `irq_eoi`: `gic_eoimode1_eoi_irq()` |
| key on, forwarded | `gic_complete_ack()` | not by the host `irq_eoi` |
| key on, LPI | `gic_complete_ack()` | none |

- `gic_cpu_sys_reg_init()` applies the mode per CPU, at bring-up and again on
  `CPU_PM_EXIT` in `gic_cpu_pm_notifier()`.
- `struct gic_kvm_info` has no field for the EOI mode; this driver never sets
  `no_hw_deactivation`.
- Key on is not enough for KVM to get the info: `gic_of_setup_kvm_info()`
  returns before `vgic_set_kvm_info()` when `irq_of_parse_and_map()` finds
  no maintenance interrupt.
- `gic_acpi_setup_kvm_info()` returns before `vgic_set_kvm_info()` when
  `gic_acpi_collect_virt_info()` or `acpi_register_gsi()` fails.
- Key off: `kvm_arm_init()` tests the same `is_hyp_mode_available()` and
  returns -ENODEV, so KVM does not initialise at all.
