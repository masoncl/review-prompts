- `kvm_pend_exception()`: its only check is `WARN_ON()` of `INCREMENT_PC`; a
  second call replaces the target.
- `INCREMENT_PC` is the low bit of `EXCEPT_MASK`: the second
  `kvm_pend_exception()` warns when the first target has that bit set, for
  example `EXCEPT_AA64_EL1_SERR` or `EXCEPT_AA32_IABT`, and is silent after
  `EXCEPT_AA64_EL1_SYNC` or `EXCEPT_AA64_EL2_SYNC`.
- There is no kvm_adjust_pc() here; callers use `__kvm_adjust_pc()` directly
  or through `kvm_call_hyp()`.
- `kvm_inject_exception()`: implements only `EXCEPT_AA64_EL1_SYNC`,
  `EXCEPT_AA64_EL1_SERR`, `EXCEPT_AA64_EL2_SYNC`, `EXCEPT_AA64_EL2_IRQ` and
  `EXCEPT_AA64_EL2_SERR` for AArch64; any other value is dropped and the flags
  are still cleared.
- Commit point on nVHE: `__kvm_vcpu_run()` calls `__kvm_adjust_pc()` before
  the guest sysregs are restored, so the ELR and SPSR it wrote to memory are
  loaded.
- Commit point on VHE: `__kvm_vcpu_run_vhe()` calls it after
  `__activate_traps()` and before `sysreg_restore_guest_state_vhe()`.
- Return to userspace: `kvm_arch_vcpu_ioctl_run()` commits at `out:` with
  `kvm_call_hyp(__kvm_adjust_pc, vcpu)` before `vcpu_put()`; nothing stays
  pending across the return.
- `out:` is also reached by the `!vcpu->wants_to_run` path, after
  `kvm_handle_mmio_return()` may have called `kvm_incr_pc()`.
- Under pKVM that call runs `__kvm_adjust_pc()` on the host's vCPU, not on
  the hyp vCPU; see `handle___kvm_adjust_pc()`.
- `commit_pending_events()` in `arch/arm64/kvm/guest.c`: commits a pending
  exception at once for `KVM_SET_VCPU_EVENTS` and clears `vcpu->mmio_needed`.
