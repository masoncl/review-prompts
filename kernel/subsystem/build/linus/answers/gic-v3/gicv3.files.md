| Job | File in this tree |
|---|---|
| MSI parent glue | `drivers/irqchip/irq-gic-its-msi-parent.c` (no "v3" in the name); shared with the GICv5 ITS |
| fsl-mc MSI glue | no file of its own in `drivers/irqchip/`; handled in `its_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c` |
| GICv4 vPE and vSGI irqchips | `drivers/irqchip/irq-gic-v3-its.c`; `drivers/irqchip/irq-gic-v4.c` defines no `struct irq_chip`, it holds the API that KVM calls |
| Priority header | `include/linux/irqchip/arm-gic-v3-prio.h` |
| GICv3 register encodings | split: `SYS_ICC_IAR1_EL1` and most other GICv3 EL1 encodings are hand-written in `arch/arm64/include/asm/sysreg.h`; `ICH_HCR_EL2`, `ICH_VTR_EL2`, `ICH_VMCR_EL2` and the GICv5 registers are in `arch/arm64/tools/sysreg` |
| User-visible system register table | `gic_v3_icc_reg_descs[]` in `arch/arm64/kvm/vgic-sys-reg-v3.c`, one level above `vgic/`; there is no such file inside `arch/arm64/kvm/vgic/` |
| Guest trap table for the ICC registers | `sys_reg_descs[]` in `arch/arm64/kvm/sys_regs.c`; not the table userspace reads |
| KVM virtual GIC, per file | glob `arch/arm64/kvm/vgic/`; the rows below are the files that are easy to miss |
| KVM nested GICv3 | `arch/arm64/kvm/vgic/vgic-v3-nested.c` |
| KVM debugfs | `arch/arm64/kvm/vgic/vgic-debug.c` |
| KVM GICv5, and GICv3 guests on a GICv5 host | `arch/arm64/kvm/vgic/vgic-v5.c`; `vgic_v5_probe()` registers the GICv3 device when the host has `ARM64_HAS_GICV5_LEGACY` |
| Hypervisor save and restore, GICv5 | `arch/arm64/kvm/hyp/vgic-v5-sr.c`, beside `arch/arm64/kvm/hyp/vgic-v3-sr.c`; both are built into VHE and nVHE |
