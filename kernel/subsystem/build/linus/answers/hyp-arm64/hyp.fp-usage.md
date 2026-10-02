- **Potentially unsafe usage**: touching FP, SVE or ZCR registers at EL2
  without `__deactivate_cptr_traps()` and `isb()` first.
  - Unsafe: while a trap that `__activate_cptr_traps()` set for that register
    may still be in effect, that is until the clearing write is followed by
    `isb()`; the EL2 access traps.
  - Safe: in `kvm_hyp_handle_fpsimd()`, which clears and synchronises before
    its first access.
  - Safe: in `fpsimd_sve_sync()`, which runs after `__deactivate_traps()` and
    issues its own `isb()`.
  - Safe: in `fpsimd_lazy_switch_to_host()` on VHE, where
    `__kvm_vcpu_run_vhe()` issues `isb()` after `__deactivate_traps()`.
  - Safe: in `fpsimd_lazy_switch_to_host()` on nVHE, which acts only when
    `guest_owns_fp_regs()` and touches ZCR only when `vcpu_has_sve()`;
    `__activate_cptr_traps()` leaves neither access trapped in that state.
- **Potentially unsafe usage**: calling `sve_save_state()` or
  `sve_load_state()` without writing ZCR first.
  - Unsafe: when the live VL differs from the VL the buffer was sized for;
    the helpers read `sve_get_vl()` and misplace or overrun the buffer.
  - Safe: host buffer after writing `sve_vq_from_vl(kvm_host_sve_max_vl) - 1`
    to ZCR_EL2, as `__hyp_sve_save_host()` does; `pkvm_host_sve_state_size()`
    defines the size.
  - Safe: guest buffer after setting ZCR_EL2 to `vcpu_sve_max_vq(vcpu) - 1`,
    as `__hyp_sve_restore_guest()` does; `vcpu_sve_state_size()` defines the
    size.
  - Safe: `fpsimd_save_user_state()`, which compares `sve_get_vl()` with the
    bound `sve_vl` before saving.
- **Potentially unsafe usage**: returning to the host with guest-owned SVE
  registers without `fpsimd_lazy_switch_to_host()`.
  - Unsafe: without pKVM, where the host later saves the guest's state;
    `fpsimd_save_user_state()` warns and sends SIGKILL when the live VL is not
    the vCPU's `sve_max_vl`.
  - Safe: under pKVM, where `fpsimd_sve_sync()` saves the guest state and sets
    `FP_STATE_HOST_OWNED` before returning, as `sync_hyp_vcpu()` does.
- **Unsafe usage**: calling `__activate_cptr_traps()` at the end of the
  handler before `fp_owner` is `FP_STATE_GUEST_OWNED`.
  - Safe: set the owner first, as `kvm_hyp_handle_fpsimd()` does;
    `__activate_cptr_traps()` sets the FP trap whenever `guest_owns_fp_regs()`
    is false.
- Host restore: `fpsimd_sve_sync()` is the only restore of what
  `kvm_hyp_save_fpsimd_host()` saved, and tests the same conditions
  (`system_supports_sve()`, `kvm_has_fpmr()`).
- Host save form: chosen by `system_supports_sve()`, a system-wide test; the
  guest load is chosen by `vcpu_has_sve()`.
- `FPEXC32_EL2`: `kvm_hyp_save_fpsimd_host()` and `fpsimd_sve_sync()` do not
  touch it; the guest's value is saved by `__fpsimd_save_fpexc32()` in
  `__kvm_vcpu_run()` when the guest owns the registers.
- SME without pKVM: `kvm_arch_vcpu_load_fp()` only warns on a non-zero
  `SYS_SVCR`.
