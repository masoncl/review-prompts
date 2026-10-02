- `host_data_ptr()` under pKVM: once `kvm_protected_mode_initialized` is set,
  host code resolves it to the `kvm_host_data` instance defined in
  `arch/arm64/kvm/hyp/vhe/switch.c`, while EL2 uses the nVHE instance, so the
  host and EL2 each have their own `fp_owner`.
- Writers of `fp_owner`: `FP_STATE_FREE` only from `arch/arm64/kvm/fpsimd.c`;
  `FP_STATE_HOST_OWNED` only from `fpsimd_sve_flush()` and
  `fpsimd_sve_sync()`; `FP_STATE_GUEST_OWNED` only from
  `kvm_hyp_handle_fpsimd()`.
- Under pKVM every run starts `FP_STATE_HOST_OWNED`, so the guest's first FP
  access in each `__kvm_vcpu_run()` call traps; state carried across entries
  with only a ZCR reprogram exists only without pKVM.
- `pvm_exit_handlers` in `arch/arm64/kvm/hyp/nvhe/switch.c`: routes
  `ESR_ELx_EC_SVE` to `kvm_handle_pvm_restricted()`, which injects an
  undefined exception; only `ESR_ELx_EC_FP_ASIMD` reaches the handler for a
  protected VM.
- `ESR_ELx_EC_SYS64` in the handler: reached only from
  `kvm_hyp_handle_zcr_el2()` in `arch/arm64/kvm/hyp/vhe/switch.c`, which
  discards the handler's return value and returns false itself.
- Trap clearing in the handler: `__deactivate_cptr_traps()` followed by
  `isb()`; there is no cpacr_clear_set() in this tree.
- Guest FPSIMD load: `fpsimd_load_state()`; there is no
  __fpsimd_restore_state() here.
- Last step of the handler: `__activate_cptr_traps()`, after `fp_owner` is
  set; it keeps SVE trapped for a vCPU without SVE and re-applies a guest
  hypervisor's traps.
- No `isb()` follows that last step; the ERET to the guest synchronises.
