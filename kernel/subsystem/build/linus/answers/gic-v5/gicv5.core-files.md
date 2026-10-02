| Job | File |
|---|---|
| IRS part of the host driver | `drivers/irqchip/irq-gic-v5-irs.c`, a file of its own beside `drivers/irqchip/irq-gic-v5.c` |
| ACPI probe | no file of its own: `CONFIG_ACPI` blocks in `drivers/irqchip/irq-gic-v5.c`, `drivers/irqchip/irq-gic-v5-irs.c`, `drivers/irqchip/irq-gic-v5-its.c` and `drivers/irqchip/irq-gic-v5-iwb.c`; IWB lookup is `iort_iwb_handle()` in `drivers/acpi/arm64/iort.c` |
| `ICC_` and `ICH_` system register layouts | `arch/arm64/tools/sysreg`; `include/linux/irqchip/arm-gic-v5.h` has none of them |
| Barrier macros `gsb_ack()`, `gsb_sys()` | `arch/arm64/include/asm/barrier.h`; only the encodings `GSB_ACK_BARRIER_INSN` and `GSB_SYS_BARRIER_INSN` are in `arch/arm64/include/asm/sysreg.h` |
| KVM at EL1 | `arch/arm64/kvm/vgic/vgic-v5.c`; it registers `KVM_DEV_TYPE_ARM_VGIC_V5` unless `is_protected_kvm_enabled()`, and `KVM_DEV_TYPE_ARM_VGIC_V3` too on `ARM64_HAS_GICV5_LEGACY` hosts |
| KVM at EL1, outside `vgic-v5.c` | `kvm_arm_vgic_v5_ops` in `arch/arm64/kvm/vgic/vgic-kvm-device.c`; `vgic_v5_setup_private_irq()` in `arch/arm64/kvm/vgic/vgic-init.c`; trap handlers such as `access_gicv5_ppi_enabler()` in `arch/arm64/kvm/sys_regs.c` |
| KVM at hyp | `arch/arm64/kvm/hyp/vgic-v5-sr.c`, built into both the VHE and nVHE objects; hypercall handlers in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` |
| Device tree binding, IWB | `Documentation/devicetree/bindings/interrupt-controller/arm,gic-v5-iwb.yaml` |
| KVM device documentation | `Documentation/virt/kvm/devices/arm-vgic-v5.rst` |
| Selftests | `tools/testing/selftests/kvm/arm64/vgic_v5.c` |
| Selftest helpers | `tools/testing/selftests/kvm/include/arm64/gic_v5.h` has its own copies of `gic_insn()`, `gicr_insn()`, `gsb_ack()`, `gsb_sys()`; there is no GICv5 file under `tools/testing/selftests/kvm/lib/arm64/` |
