| Architecture | `kvm_arch_has_default_irqchip()` | Library creates at `__vm_create()` |
|---|---|---|
| x86 | true | `vm_create_irqchip()` |
| arm64 | `request_vgic && kvm_supports_vgic_v3()` | GICv3, same condition |
| s390 | true | nothing |
| riscv | `kvm_check_cap(KVM_CAP_IRQCHIP)` | nothing |
| loongarch | false (weak default) | nothing |

- riscv: overrides the weak default in
  `tools/testing/selftests/kvm/lib/riscv/processor.c`; the kernel answers
  `KVM_CAP_IRQCHIP` with `kvm_riscv_aia_available()`.
- riscv, s390, loongarch: the library has no `kvm_arch_vm_post_create()`
  override, so a true return does not mean the library created a device.
- arm64 result: process-wide, not per VM. It reads the static `request_vgic`
  and probes a throwaway VM in `kvm_supports_vgic_v3()`; it does not read
  `vm->arch.has_gic`.
- x86 `vm_create_irqchip()`: if `KVM_CREATE_IRQCHIP` fails with `ENOTTY` it
  enables `KVM_CAP_SPLIT_IRQCHIP` with 24 pins instead, so the VM may have
  no in-kernel IOAPIC or PIC.
- `__vgic_v3_setup()`: its comment says it must run after all vCPUs exist;
  the library calls it from `kvm_arch_vm_post_create()` before any vCPU.
  Only `vgic_v3_setup()` asserts the vCPU count.
- **Unsafe usage**: on arm64, creating a vGIC with `vgic_v3_setup()` or
  `kvm_create_device()` on a VM from `__vm_create()` while the default vGIC
  is enabled; `kvm_vgic_create()` returns `-EEXIST`.
  - Safe: call `test_disable_default_vgic()` before the VM is created, as
    `main()` in `tools/testing/selftests/kvm/arm64/vgic_irq.c` does.
  - Safe: create the VM with `vm_create_barebones()`, as
    `vm_gic_create_barebones()` in
    `tools/testing/selftests/kvm/arm64/vgic_init.c` does.
