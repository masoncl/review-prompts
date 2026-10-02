| ioctl on arm64 | No vGIC created | GICv3 created, not initialised |
|---|---|---|
| `KVM_IRQFD` assign | `-EAGAIN` | `-EAGAIN` |
| `KVM_IRQ_LINE`, PPI or SPI type | `-ENXIO` | `-EBUSY` |
| `KVM_SET_GSI_ROUTING`, valid table | 0 | 0 |

- `KVM_IRQFD`: `-EAGAIN` is the first test in `kvm_irqfd_assign()`
  (`virt/kvm/eventfd.c`), taken when `kvm_arch_intc_initialized()` is false;
  arm64 uses the weak `kvm_arch_irqfd_allowed()`, which returns true.
- `KVM_IRQFD` with `KVM_IRQFD_FLAG_DEASSIGN`: not gated; `kvm_irqfd()` sends
  it to `kvm_irqfd_deassign()`.
- `KVM_IRQ_LINE`: both errors are returned by `kvm_vm_ioctl_irq_line()` in
  `arch/arm64/kvm/arm.c`; the `-EBUSY` is the result of its own call to
  `vgic_lazy_init()`.
- `kvm_vgic_inject_irq()`: does not call `vgic_lazy_init()`; on an
  uninitialised vGIC it returns 0 and injects nothing.
- `KVM_IRQ_LINE` with `KVM_ARM_IRQ_TYPE_CPU`: `-ENXIO` when a vGIC exists.
- `KVM_SET_GSI_ROUTING`: no initialisation test; arm64 uses the weak
  `kvm_arch_can_set_irq_routing()`, which returns true.
- Routing table written before initialisation: replaced when `vgic_init()`
  calls `kvm_vgic_setup_default_irq_routing()`.
- VM from `vm_create_barebones()`: has no vGIC, so the "No vGIC created"
  column applies.
- **Potentially unsafe usage**: on arm64, `KVM_IRQFD` assign or
  `KVM_IRQ_LINE` on a VM from `vm_create()` or `__vm_create()` before
  `kvm_arch_vm_finalize_vcpus()` has run.
  - Unsafe: when the VM has the default vGIC; `kvm_arch_vm_post_create()`
    created it and nothing has initialised it yet, so `kvm_irqfd_assign()`
    returns `-EAGAIN` and `vgic_lazy_init()` returns `-EBUSY`.
  - Safe: after `TEST_REQUIRE(kvm_arch_has_default_irqchip())`, create the
    VM with `vm_create_with_one_vcpu()` and an unused vCPU with NULL guest
    code, as `main()` in `tools/testing/selftests/kvm/irqfd_test.c` does;
    `kvm_irqfd_assign()` needs `vgic_initialized()`.
  - Safe: add the vCPUs, call `kvm_arch_vm_finalize_vcpus()`, then issue the
    ioctls; the hook calls `__vgic_v3_init()` when `vm->arch.has_gic` is set.
  - Safe: after `test_disable_default_vgic()`, the test initialises a vGIC of
    its own before the ioctl: with `vgic_v3_setup()`, which calls
    `__vgic_v3_init()`, as `tools/testing/selftests/kvm/arm64/vgic_irq.c`
    does, or with `KVM_DEV_ARM_VGIC_CTRL_INIT` on its own device, as
    `test_vgic_v5_ppis()` in `tools/testing/selftests/kvm/arm64/vgic_v5.c`
    does without ever calling the hook.
