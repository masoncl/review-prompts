- `gic_eoimode1_chip` differs from `gic_chip` in three callbacks only:
  `.irq_mask`, `.irq_eoi` and `.irq_set_vcpu_affinity`;
  `.irq_get_irqchip_state` is the same function in both.
- `gic_eoimode1_eoi_irq()`: deactivates (`gic_write_dir()`); it does not
  drop priority.
- `gic_eoimode1_mask_irq()`: masks, then clears the active state with
  `GICD_ICACTIVER` when the interrupt is forwarded.
- `irq_set_vcpu_affinity()` on an interrupt of `gic_chip`: returns -ENOSYS
  when no chip above it in the hierarchy has the callback.
- `gic_irq_set_vcpu_affinity()`: uses `vcpu` only as set-or-clear; it stores
  nothing but the forwarded flag.
- Forwarded state is per interrupt and persistent: for example
  `kvm_timer_hyp_init()` sets it once for the host timer PPIs.
- While forwarded, `gic_eoimode1_eoi_irq()` never deactivates, also when the
  handler ran with no guest loaded; KVM changes the active state itself with
  `irq_set_irqchip_state()`, see `set_timer_irq_phys_active()`.
- PPI, EPPI and SGI: `handle_percpu_devid_irq()` with either chip; there is
  no handle_percpu_devid_fasteoi_irq() in this tree.
- LPIs are mapped by `gic_irq_domain_map()` too (`LPI_RANGE`), with the
  selected chip and `handle_fasteoi_irq()`, as parent of the ITS domain.
- `IRQCHIP_SUPPORTS_NMI`: not in either initialiser;
  `gic_enable_nmi_support()` sets it at boot on the selected chip only.
