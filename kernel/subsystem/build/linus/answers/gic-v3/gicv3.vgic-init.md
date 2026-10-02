- `kvm_vgic_inject_irq()` (`arch/arm64/kvm/vgic/vgic.c`): does not call
  `vgic_lazy_init()`. When `vgic_initialized()` is false it returns 0 and the
  injection is dropped silently.
- `vgic_lazy_init()` is called only by the userspace entry points, before
  they call `kvm_vgic_inject_irq()`: `kvm_vm_ioctl_irq_line()` in
  `arch/arm64/kvm/arm.c` and `vgic_irqfd_set_irq()` in
  `arch/arm64/kvm/vgic/vgic-irqfd.c`. Both pass up its `-EBUSY` for an
  uninitialised model other than GICv2; `vgic_irqfd_set_irq()` tests
  `vgic_valid_spi()` first and returns `-EINVAL` if that fails.
- In-kernel injectors, for example the timer in
  `arch/arm64/kvm/arch_timer.c`, call `kvm_vgic_inject_irq()` directly: before
  init they get 0, no error and no lazy init, also on GICv2.
- `kvm_arch_set_irq_inatomic()`: before init returns `-EWOULDBLOCK` for
  `KVM_IRQ_ROUTING_IRQCHIP`.
- `vgic_init()`: returns 0 when already initialised. Its only own refusal is
  `-EBUSY` while `kvm->created_vcpus != atomic_read(&kvm->online_vcpus)`.
  Other errors are passed up from what it calls.
- `vgic_init()` itself rejects nothing on the model, the base addresses or
  `nr_spis`. Bases are checked in `vgic_v2_map_resources()` and
  `vgic_v3_map_resources()`; the `nr_spis` range is checked in
  `vgic_set_common_attr()`.
- Per-vCPU step in `vgic_init()`: `kvm_vgic_vcpu_reset()`. There is no
  kvm_vgic_vcpu_enable() in this tree.
- `vgic_v4_init()` gate in `vgic_init()`: `vgic_supports_direct_irqs()`, true
  for direct MSIs or direct SGIs, not `vgic_supports_direct_msis()` alone.
- GICv5 in `vgic_init()`: `vgic_v5_init()` replaces the SPI and GICv4 setup;
  it returns `-EINVAL` if any vCPU has `vcpu_has_nv()`.
- `vgic_v3_attr_regs_access()` before init: `-EBUSY`, except when
  `reg_allowed_pre_init()` is true, which is `GICD_IIDR` and `GICD_TYPER2` in
  `KVM_DEV_ARM_VGIC_GRP_DIST_REGS`.
