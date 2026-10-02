- Paths are relative to `arch/arm64/kvm/`.
- Ioctl entry points `kvm_arch_vm_ioctl()` and `kvm_arch_vcpu_ioctl()` and the
  run loop `kvm_arch_vcpu_ioctl_run()`: `arm.c`.
- PMU: `pmu-emul.c` and `pmu.c`.
- GICv2, GICv3, ITS and GICv4: `vgic/vgic-v2.c`, `vgic/vgic-v3.c`,
  `vgic/vgic-its.c` and `vgic/vgic-v4.c`.

| Job | File | Easy to miss in this tree |
|---|---|---|
| Exit handling | `handle_exit.c` | Hyp runs first: `hyp_exit_handlers[]` in `hyp/vhe/switch.c` and `hyp/nvhe/switch.c`. Protected VMs use `pvm_exit_handlers[]` in `hyp/nvhe/switch.c` instead. |
| System register emulation | `sys_regs.c` | `kvm_handle_sys_reg()` calls `triage_sysreg_trap()` in `emulate-nested.c` first for every guest, nested or not; on a host with `ARM64_HAS_FGT` it injects UNDEF for bits set in `kvm->arch.fgu[]`. Protected VMs: `kvm_handle_pvm_sysreg()` in `hyp/nvhe/sys_regs.c`. |
| Feature-to-register-bit tables | `config.c` | Arrays of `struct reg_bits_to_feat_map`, named like `hfgrtr_feat_map[]`, wrapped in `struct reg_feat_map_desc`. Also cover, for example, `SCTLR_EL1`, `SCTLR_EL2`, `TCR2_EL2`, `MDCR_EL2`, `VTCR_EL2` and the GICv5 `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2`, `ICH_HFGITR_EL2`. Read through `compute_fgu()` and `get_reg_fixed_bits()`; `kvm_vcpu_load_fgt()` is here too. `compute_fgu()` runs for every VM from `kvm_calculate_traps()`. |
| Stage-2 fault handling | `mmu.c` | `kvm_handle_guest_abort()` ends by picking one of three resolvers: `pkvm_mem_abort()` (protected VM), `gmem_abort()` (memslot with guest_memfd), `user_mem_abort()`. On a shadow stage-2 with `nested_stage2_enabled` it calls `kvm_walk_nested_s2()` in `nested.c` first. |
| Reset | `reset.c` | System register reset values are in `sys_regs.c`: `kvm_reset_vcpu()` calls `kvm_reset_sys_regs()`. |
| PSCI and other hypercalls | `psci.c`, `hypercalls.c`, `pvtime.c`, `trng.c` | There is no kvm_hvc_call_handler(); the entry is `kvm_smccc_call_handler()`. `hyp/nvhe/psci-relay.c` handles the host's own PSCI calls, not the guest's. |
| Exception injection | `inject_fault.c` | There is no kvm_inject_dabt(); use `kvm_inject_sea()`, or inline `kvm_inject_sea_dabt()` and `kvm_inject_sea_iabt()` in `arch/arm64/include/asm/kvm_emulate.h`. `kvm_inject_exception()` is static in `hyp/exception.c`. |
| Timer | `arch_timer.c` | Hyp side is both `hyp/nvhe/timer-sr.c` and `hyp/vhe/timer-sr.c`; the VHE file holds only `__kvm_timer_set_cntvoff()`. |
| Debug | `debug.c` | There is no kvm_arm_setup_debug(); `kvm_vcpu_load_debug()` and `kvm_vcpu_put_debug()` do that job. `KVM_SET_GUEST_DEBUG` is `kvm_arch_vcpu_ioctl_set_guest_debug()` in `guest.c`. |
| FP/SIMD | `fpsimd.c` | There is no fpsimd.S under `hyp/`; hyp code calls the inline `fpsimd_save_state()` and `sve_save_state()` family in `arch/arm64/include/asm/fpsimd.h`. No SME guest state: `kvm_arch_vcpu_ctxsync_fp()` sets `sme_state` to `NULL`. |
| Nested virtualisation | `nested.c`, `emulate-nested.c`, `at.c`, `vgic/vgic-v3-nested.c` | `pauth.c` belongs here too: `kvm_auth_eretax()`, built only with `CONFIG_ARM64_PTR_AUTH`. |
| Host side of pKVM | `pkvm.c` | Also holds the host's stage-2 back end: `KVM_PGT_FN()` in `mmu.c` picks the `pkvm_pgtable_stage2_map()` family whenever `is_protected_kvm_enabled()`. |
| GICv3 CPU interface registers | `vgic-sys-reg-v3.c` | At the top level, not in `vgic/`. Serves userspace access only (`vgic_v3_cpu_sysregs_uaccess()`); guest ICC traps are emulated by `__vgic_v3_perform_cpuif_access()` in `hyp/vgic-v3-sr.c`, or by `access_gic_sgi()`, `access_gic_sre()` and `access_gic_dir()` in `sys_regs.c`. |
| GICv5 model | `vgic/vgic-v5.c`, `hyp/vgic-v5-sr.c` | `vgic_v5_probe()` registers `KVM_DEV_TYPE_ARM_VGIC_V5`, a real GICv5 guest, and with `ARM64_HAS_GICV5_LEGACY` also `KVM_DEV_TYPE_ARM_VGIC_V3`. A v5 guest has no SPIs: `vgic_init()` skips `kvm_vgic_dist_init()`. `KVM_DEV_TYPE_ARM_VGIC_V5` is not registered under pKVM; `vgic_v5_init()` rejects nested vCPUs. Guest trap handlers such as `access_gicv5_ppi_enabler()` are in `sys_regs.c`. |
