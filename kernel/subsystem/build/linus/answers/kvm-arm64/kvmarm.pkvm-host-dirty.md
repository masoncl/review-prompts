- The mark is `PKVM_HOST_STATE_DIRTY`, a bit of `arch.iflags`, defined in
  `arch/arm64/include/asm/kvm_host.h`; it is used for non-protected VMs only.
- Set by the host in three places: `kvm_arch_vcpu_run_pid_change()` (first
  run), `kvm_arch_vcpu_put()` after `__pkvm_vcpu_put`, and
  `handle_exit_pkvm_state()` after `__pkvm_vcpu_sync_state`.
- Cleared only by `handle_exit_pkvm_state()`, on an exit that needs no sync.
- `flush_hyp_vcpu()` on finding the mark: copies host to hyp with
  `__copy_vcpu_state()`; it does not clear the mark.
- With the mark clear, `flush_hyp_vcpu()` copies no `arch.ctxt`, and
  `handle___pkvm_vcpu_put()` overwrites the host's `arch.ctxt` from the
  hypervisor's.
- Protected vCPU: the mark is ignored; `flush_hyp_vcpu()` copies the host's
  whole `arch.ctxt` on every run.
- **Unsafe usage**: writing `arch.ctxt` of a non-protected vCPU while it is
  loaded and `PKVM_HOST_STATE_DIRTY` is clear, as after an
  `ARM_EXCEPTION_IRQ` exit.
  - Unsafe: the write never reaches the hyp vCPU and is overwritten at the
    next `__pkvm_vcpu_sync_state` or `__pkvm_vcpu_put`.
  - Safe: in a handler called from `handle_exit()` for
    `ARM_EXCEPTION_TRAP`; `handle_exit_pkvm_state()` has synced and set the
    mark. `handle_hvc()` writing results through `kvm_smccc_call_handler()`
    is one.
  - Safe: while the vCPU is not loaded; `kvm_arch_vcpu_put()` set the mark.
    `kvm_handle_mmio_return()` runs before `vcpu_load()` in
    `kvm_arch_vcpu_ioctl_run()`.
  - Safe: before the first run; `kvm_arch_vcpu_run_pid_change()` sets the
    mark.
  - Safe: state that `flush_hyp_vcpu()` copies on every run whatever the
    mark: `arch.iflags`, `HCR_VSE` with `arch.vsesr_el2`, vGIC list
    registers, `arch.mdcr_el2`, debug state.
- Timer registers skipped by `__copy_vcpu_state()` never travel through
  flush or sync for a non-protected vCPU.
