- `invalid_host_el2_vect` in `arch/arm64/kvm/hyp/nvhe/host.S`: makes no
  loaded-vCPU test and never goes to `__guest_exit_panic`; it branches
  straight to `hyp_panic`.
- Stack overflow test in `invalid_host_el2_vect`: on the `NVHE_STACK_SHIFT`
  bit of SP; on overflow it switches to `overflow_stack` and branches to
  `hyp_panic_bad_stack()`, which only calls `hyp_panic()`.
- There is no __hyp_panic and no __kvm_vector_install here; the panic targets
  are `hyp_panic` and `__guest_exit_panic`, and `__activate_traps()` writes
  the per-CPU `kvm_hyp_vector` to VBAR_EL2.
- `__kvm_hyp_init` in `arch/arm64/kvm/hyp/nvhe/hyp-init.S` is another table,
  installed by `hyp_install_host_vector()` in `arch/arm64/kvm/arm.c`; every
  EL2 slot is `ventry .`, so an EL2 exception under it spins and never reaches
  `hyp_panic()`.
- Guest table, `el2_sync` and `el2_error`: both call
  `kvm_unexpected_el2_exception()`; with no fixup it stores ELR_EL2 in
  `kvm_hyp_ctxt` and returns to `__guest_exit_restore_elr_and_panic`, which
  reloads ELR_EL2 and falls into `__guest_exit_panic`.
- `el2_sync` tests SPSR_EL2.IL first: if set it leaves through `__guest_exit`
  with `ARM_EXCEPTION_IL` and does not panic.
- Two different "vCPU loaded" tests: `__guest_exit_panic` reads `kvm_hyp_ctxt`
  through `get_loaded_vcpu`, set only between `__guest_enter` and
  `__guest_exit`; `hyp_panic()` reads `host_ctxt->__hyp_running_vcpu`, set for
  the whole of `__kvm_vcpu_run()`.
- `hyp_panic()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: does not call
  `__debug_switch_to_host()`; with `__hyp_running_vcpu` set its only restore
  calls are `__timer_disable_traps()`, `__deactivate_traps()`,
  `__load_host_stage2()` and `__sysreg_restore_state_nvhe()`.
- `__hyp_do_panic` called from `hyp_panic()`, so with a non-NULL `host_ctxt`:
  joins `__host_exit` at `__host_enter_for_panic`, which is after the kernel
  ptrauth key restore done at `__host_enter_restore_full`; host x0-x7 are
  replaced by the panic arguments.
- `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`, not `CONFIG_NVHE_EL2_DEBUG`, makes
  `__hyp_do_panic` clear `HCR_VM` and do `tlbi vmalls12e1`.
