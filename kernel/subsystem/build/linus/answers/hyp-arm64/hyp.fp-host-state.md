- Names: there is no fpsimd_kvm_prepare(), __fpsimd_save_state(),
  __sve_save_state() or __sve_restore_state() here; hyp code uses
  `fpsimd_save_state()`, `fpsimd_load_state()`, `sve_save_state()`,
  `sve_load_state()`, `fpsimd_save_common()` and `fpsimd_load_common()` from
  `arch/arm64/include/asm/fpsimd.h`, the same helpers the host kernel uses.
- Host SVE buffer: `sve_regs` in `struct kvm_host_data`, of the opaque type
  `struct arm64_sve_state`; there is no struct cpu_sve_state.
- Host values outside the buffer: ZCR_EL1 in `ctxt_sys_reg(hctxt, ZCR_EL1)`,
  FPMR in `ctxt_sys_reg(hctxt, FPMR)`, FPSR and FPCR in `host_ctxt.fp_regs`.
- `sve_save_state()` and `sve_load_state()`: take no vector length; they lay
  the buffer out from `sve_get_vl()`, so the ZCR_EL2 write just before the
  call decides the layout. There is no sve_ffr_offset() here.
- ZCR_EL2 for host state: `sve_vq_from_vl(kvm_host_sve_max_vl) - 1`, not
  `ZCR_ELx_LEN_MASK`; see `__hyp_sve_save_host()` and
  `__hyp_sve_restore_host()`.
- `sve_regs`: already a hyp VA once `finalize_init_hyp_mode()` in
  `arch/arm64/kvm/arm.c` has run, so hyp code dereferences it without
  `kern_hyp_va()`; sized by `pkvm_host_sve_state_size()`.
- Under pKVM the host still saves: `kvm_arch_vcpu_load()` calls
  `kvm_arch_vcpu_load_fp()` unconditionally; the EL2 save is in addition.
- `fpsimd_lazy_switch_to_host()`: saves and restores no FP or SVE register
  contents; it stores the guest's ZCR into the vCPU and rewrites ZCR.
- `fpsimd_lazy_switch_to_host()` ZCR values: with `has_vhe()`, ZCR_EL2 gets
  the vCPU's max; otherwise (nVHE and hVHE) ZCR_EL2 gets the host max and
  ZCR_EL1 the vCPU's max.
- Callers of the two lazy switch functions: `__kvm_vcpu_run_vhe()`, and the
  non-pKVM branch of `handle___kvm_vcpu_run()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`; nVHE `__kvm_vcpu_run()` calls neither.
- pKVM branch of `handle___kvm_vcpu_run()`: calls neither lazy switch
  function; `fpsimd_sve_flush()` and `fpsimd_sve_sync()` bracket the run.
- Protected and non-protected guests under pKVM: both run on
  `hyp_vcpu->vcpu`, and the host save and restore are the same for both.
- Protected VM: cannot have SVE (`kvm_pkvm_ext_allowed()` falls to its
  default case for `KVM_CAP_ARM_SVE`), so for the guest only FPSIMD state is
  ever loaded.
- Non-protected VM with SVE under pKVM: `sve_state` is host memory pinned by
  `pkvm_vcpu_init_sve()`, with the VL capped at `kvm_host_sve_max_vl`.
