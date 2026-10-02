- HCR_EL2 for the host: taken from per-CPU `kvm_init_params.hcr_el2`, not from
  a constant. `cpu_prepare_hyp_mode()` in `arch/arm64/kvm/arm.c` seeds it with
  `HCR_HOST_NVHE_PROTECTED_FLAGS` (which adds `HCR_TSC`), then `HCR_ATA` or
  `HCR_TID5`, then `HCR_E2H` with `ARM64_KVM_HVHE`.
- EL2 registers are not all free of host-chosen values:
  - CNTVOFF_EL2: `handle___kvm_timer_set_cntvoff()` writes hypercall
    register 1 to it unchecked, and the call stays allowed after init.
  - MDCR_EL2 during a guest run: `__activate_traps()` writes
    `vcpu->arch.mdcr_el2`, which `flush_hyp_vcpu()` copied from the host.
  - HCR_EL2 during a guest run: bits `HCR_TWI`, `HCR_TWE` and `HCR_VSE` of
    the hyp vCPU's `arch.hcr_el2` come from the host; the rest from
    `pkvm_vcpu_init_traps()`.
  - VSESR_EL2: `___activate_traps()` can write the host-supplied
    `vsesr_el2` when `HCR_VSE` is set and the CPU has `ARM64_HAS_RAS_EXTN`.
- Host-written EL1 and EL0 registers that EL2 code reads, for example:
  `inject_host_exception()` reads SCTLR_EL1 and VBAR_EL1 to build the
  injected exception; `enter_vmid_context()` reads TCR_EL1 under
  `ARM64_WORKAROUND_SPECULATIVE_AT`; `handle___kvm_vcpu_run()`, under pKVM
  and when `system_supports_sme()`, reads SVCR and refuses to run if it is
  non-zero.
