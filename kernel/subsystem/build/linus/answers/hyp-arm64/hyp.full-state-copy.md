- `PKVM_HOST_STATE_DIRTY` and `handle___pkvm_vcpu_sync_state()`: both exist in
  this tree.
- `PKVM_HOST_STATE_DIRTY`: bit 4 of `iflags` in the host's vCPU, defined in
  `arch/arm64/include/asm/kvm_host.h`; set means the host's register copy is
  current and must be flushed to the hyp vCPU.
- Scope: non-protected vCPUs under pKVM only; the host sets it only when
  `!kvm_vm_is_protected()`, EL2 tests it only on the non-protected branch.
- Protected vCPU: whole `arch.ctxt` goes each way on every entry and exit;
  there are no per-exit-class handlers that expose selected registers.
- Host to hyp: `flush_hyp_vcpu()`, when the flag is set.
- Hyp to host: `handle___pkvm_vcpu_sync_state()`, and
  `handle___pkvm_vcpu_put()` when the flag is clear.
- `handle___pkvm_vcpu_sync_state()`: only copies; it does not touch the flag,
  and returns silently with no loaded vCPU or a protected one.
- Host setters, complete list:
  - `kvm_arch_vcpu_run_pid_change()`: set before the hyp vCPU is created.
  - `kvm_arch_vcpu_put()`: set after the `__pkvm_vcpu_put` hypercall.
  - `handle_exit_pkvm_state()` in `arch/arm64/kvm/handle_exit.c`: on
    `ARM_EXCEPTION_TRAP`, `ARM_EXCEPTION_EL1_SERROR` or a pending SError it
    makes the sync hypercall and sets the flag; on any other exit it clears it.
- Register ioctls: make no sync hypercall; they run with the vCPU put
  (`vcpu_load()` is called only in `kvm_arch_vcpu_ioctl_run()`), when the
  host's copy is current.
- `__copy_vcpu_state()`: copies `regs`, the four `spsr_` fields, `fp_regs` and
  `sys_regs[]` from index 1, skipping `CNTVOFF_EL2`, `CNTV_CVAL_EL0`,
  `CNTV_CTL_EL0`, `CNTP_CVAL_EL0`, `CNTP_CTL_EL0`; not
  `__hyp_running_vcpu` or `vncr_array`.
- Flag clear, vCPU loaded (for example after an IRQ exit): the host's
  `arch.ctxt` is stale apart from `regs.pc` and `regs.pstate`; a host write
  to it is not flushed at the next entry and is overwritten at put.
