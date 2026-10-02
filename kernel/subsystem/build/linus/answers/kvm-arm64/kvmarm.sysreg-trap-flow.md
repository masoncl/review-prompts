- Lookup: `get_trap_config()` loads a `union trap_config` from the xarray
  `sr_forward_xa` by encoding; the AArch64 trap path does no `find_reg()`, and
  there is no encoding_to_sr().
- `kvm_handle_sys_reg()`: calls `triage_sysreg_trap()` before it decodes the
  ESR into `struct sys_reg_params`.
- Order of decisions:
  1. `tc.val == 0`: go to step 6.
  2. `tc.fgt` set and the bit set in `kvm->arch.fgu[tc.fgt]`: UNDEF, for every
     VM.
  3. No `vcpu_has_nv()`: go to step 6.
  4. `is_hyp_ctxt()` and not `vcpu_is_host_el0()`: go to step 6.
  5. Guest fine-grained trap (`check_fgt_bit()`), then coarse traps
     (`compute_trap_behaviour()`): forward with `kvm_inject_nested_sync()`.
  6. `tc.sri == 0`: no descriptor, the access is refused here.
  7. `perform_access()`: `REG_HIDDEN` gives UNDEF, then `.access` runs.
- Step 2 on a host without `ARM64_HAS_FGT`: never fires, because
  `populate_nv_trap_config()` does not store the fine-grained part of the
  config; the UNDEF for a disabled feature then comes only from step 7 or the
  access function.
- Step 5 in hyp context at EL0: `check_fgt_bit()` returns false, and a coarse
  trap forwards only if it has `BEHAVE_FORWARD_IN_HOST_EL0`.
- Step 6 in the feature ID space (`in_feat_id_space()`): `kvm_inject_sync()`
  with the original ESR when the VM has `ID_AA64MMFR2_EL1` `IDS`, UNDEF
  otherwise.
- Step 7 comes after step 5: for an NV guest, forwarding to the guest
  hypervisor wins over `REG_HIDDEN`.
- Descriptor table: `sys_reg_descs[sr_idx]` when Op0 is 2 or 3, otherwise
  `sys_insn_descs[sr_idx]`; Rt is written back only for a read with Op0 2 or 3.
- Missing `.access`: `bad_trap()`, which is `WARN_ONCE()` plus UNDEF; there is
  no `BUG_ON()`.
- Read/write direction: not checked by `perform_access()`; access functions
  call `write_to_read_only()` or `read_from_write_only()` themselves.
- `unhandled_cp_access()`: AArch32 coprocessor path only.
