- Build macros: `vgic_v5_make_ppi()`, `vgic_v5_make_spi()`,
  `vgic_v5_make_lpi()`; each takes the bare ID.
- Take-apart macro: `vgic_v5_get_hwirq_id()` returns the bare ID.
- `vgic_v5_set_hwirq_id()`: places the ID field only; the result has type 0
  and is not a usable interrupt ID.
- `get_vgic_ppi()`: a macro in `include/kvm/arm_arch_timer.h`, not a function
  in `arch/arm64/kvm/arch_timer.c`; it open-codes the two `FIELD_PREP()` and
  returns the number unchanged for other models.
- Timer: `kvm_timer_init_vm()` stores the typed ID in
  `kvm->arch.timer_data.ppi[]`; every user reads it with `timer_irq()`.
- PMU: `kvm_arm_pmu_v3_init()` stores `KVM_ARMV8_PMU_GICV5_IRQ`, a typed
  literal, in `irq_num`; `kvm_pmu_update_state()` passes it on.
- **Unsafe usage**: passing a bare ID for a GICv5 guest.
  - Unsafe: to `kvm_vgic_set_irq_ops()`, `kvm_vgic_map_phys_irq()` or, once
    the vgic is initialised, `kvm_vgic_unmap_phys_irq()`: the lookup returns
    `NULL` and they `BUG_ON()` it.
  - Unsafe: to `kvm_vgic_get_map()`, `kvm_vgic_reset_mapped_irq()` or, once
    the vgic is initialised, `kvm_vgic_map_is_active()`: they dereference the
    `NULL` result.
  - Unsafe: to `kvm_vgic_inject_irq()` or `kvm_vgic_set_owner()`: once the
    vgic is initialised they return `-EINVAL`, so nothing is injected and no
    owner is set.
  - Safe: a typed ID from `timer_irq()`, as `kvm_timer_enable()` passes;
    `__irq_is_ppi()` in `vgic_get_vcpu_irq()` defines what the lookup
    accepts.
