- Helper: `kvm_vgic_create()` calls `kvm_timer_init_vm()`
  (`arch/arm64/kvm/arch_timer.c`) for `KVM_DEV_TYPE_ARM_VGIC_V5` only.
- When: after private IRQ allocation succeeded, under `config_lock`; an
  earlier failure leaves the timer PPIs untouched.
- What it sets: every entry of `kvm->arch.timer_data.ppi[]` to
  `get_vgic_ppi(kvm, default_ppi[i])`.
- Values: the ID field keeps `default_ppi[]` (30, 27, 28, 26);
  `get_vgic_ppi()` only adds `GICV5_HWIRQ_TYPE_PPI` in the type field.
