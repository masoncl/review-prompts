- Register context (`arch.ctxt`):

| Guest | `flush_hyp_vcpu()` | `sync_hyp_vcpu()` |
|---|---|---|
| Protected | whole `arch.ctxt`, host to hyp, every run | whole `arch.ctxt`, hyp to host, every run |
| Non-protected | `__copy_vcpu_state()` only if `PKVM_HOST_STATE_DIRTY` | only `regs.pc` and `regs.pstate` |

- `__copy_vcpu_state()`: copies `regs`, the four `spsr_` fields, `fp_regs`
  and `sys_regs[]`, but skips `CNTVOFF_EL2`, `CNTV_CVAL_EL0`, `CNTV_CTL_EL0`,
  `CNTP_CVAL_EL0` and `CNTP_CTL_EL0`.
- Copied host to hyp on every run for both kinds: `arch.mdcr_el2` (whole),
  `arch.iflags`, `arch.vsesr_el2`, `arch.pid`, debug state
  (`flush_debug_state()`), and from the vGIC `vgic_hcr`, `used_lrs` (clamped
  to `hyp_gicv3_nr_lr`) and that many `vgic_lr[]`.
- Copied hyp to host on every run for both kinds: `arch.fault`,
  `arch.iflags`, debug state, `vgic_hcr`, `vgic_vmcr`, used `vgic_lr[]`.
- `fpsimd_sve_flush()` copies nothing; it marks FP state as host-owned.
- Full sync request: `handle_exit_pkvm_state()` in
  `arch/arm64/kvm/handle_exit.c` issues `__pkvm_vcpu_sync_state` for a
  non-protected VM when the exit is `ARM_EXCEPTION_TRAP`,
  `ARM_EXCEPTION_EL1_SERROR` or has `ARM_SERROR_PENDING()`.
- `handle_exit_pkvm_state()` runs first in `handle_exit_early()`, with
  preemption off, before any exit handler reads guest registers.
- `handle___pkvm_vcpu_sync_state()`: does nothing for a protected vCPU or
  when no hyp vCPU is loaded.
- `handle___pkvm_vcpu_put()`: also does the full sync for a non-protected
  vCPU, unless `PKVM_HOST_STATE_DIRTY` is set.
- After an exit that is not a trap or SError (for example
  `ARM_EXCEPTION_IRQ`), the host's `arch.ctxt` of a non-protected vCPU is
  stale except for `pc` and `pstate`.
