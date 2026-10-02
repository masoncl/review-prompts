- There is no __fpsimd_restore_state() here; `kvm_hyp_handle_fpsimd()` uses
  `fpsimd_load_state()` or `__hyp_sve_restore_guest()`.
- Nested transition: `kvm_arch_vcpu_load_fp()` and `kvm_arch_vcpu_put_fp()`
  both return early when `IN_NESTED_ERET` or `IN_NESTED_EXCEPTION` is set.
- Effect: nothing is saved or flushed and `fp_owner` is unchanged, so a
  guest that owned the registers still owns them after the transition.
- Both early returns warn once if `host_owns_fp_regs()`.
- Other put/load pairs, for example `kvm_reset_vcpu()`, set neither flag and
  do the full FP save and flush.
- `kvm_arch_vcpu_put_fp()`: never writes `fp_owner`; the next
  `kvm_arch_vcpu_load_fp()` sets `FP_STATE_FREE`.
- After a transition with state kept live, traps and vector length follow the
  new context at the next entry: see `__activate_cptr_traps_vhe()` and
  `fpsimd_lazy_switch_to_guest()` in
  `arch/arm64/kvm/hyp/include/hyp/switch.h`.
