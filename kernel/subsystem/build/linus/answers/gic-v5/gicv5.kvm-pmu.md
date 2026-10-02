- `KVM_ARMV8_PMU_GICV5_IRQ`: `0x20000017` in `include/kvm/arm_pmu.h`, PPI 23
  as a typed ID.
- `KVM_ARM_VCPU_PMU_V3_IRQ`: userspace passes the typed value;
  `pmu_irq_is_valid()` compares for equality, so any other typed ID gets
  `-EINVAL`; a bare 23 gets `-EINVAL` from the `irq_is_ppi()` and
  `irq_is_spi()` test before it.
- No IRQ set: `kvm_arm_pmu_v3_init()` stores `KVM_ARMV8_PMU_GICV5_IRQ` for a
  GICv5 guest and goes on; for other models it returns `-ENXIO`.
- `kvm_arm_pmu_v3_init()`: returns `-ENODEV` if the vgic is not initialised,
  before it looks at the IRQ.
- `kvm_arm_pmu_irq_initialized()`: tests `irq_num != 0`, which holds for the
  typed value.
