- `vcpu_reset_hcr()`: called from `kvm_arch_vcpu_ioctl_vcpu_init()`, not from
  `kvm_reset_vcpu()`.
- Base value: `HCR_GUEST_FLAGS` from `vcpu_reset_hcr()`, assigned only while
  `vcpu_has_run_once()` is false.
- `vcpu_set_hcr()`: only ORs bits in and clears `HCR_RW`; it sets `HCR_TID5`
  when the VM has no MTE.
- At each `kvm_arch_vcpu_load()`: `HCR_TWI`, `HCR_TWE`, and through
  `vcpu_set_pauth_traps()` `HCR_API` and `HCR_APK`.
- `vcpu_set_pauth_traps()`: does nothing when `is_protected_kvm_enabled()`.
- At run time, for example: `HCR_TVM` in `kvm_set_way_flush()` and
  `kvm_toggle_cache()`, `HCR_VSE` in `kvm_inject_serror_esr()`, `HCR_VI` and
  `HCR_VF` in `vcpu_interrupt_line()`.
- At write time: `___activate_traps()` adds `HCR_TVM` under
  `ARM64_WORKAROUND_CAVIUM_TX2_219_TVM`, without storing it.
- nVHE exit: restores the per-CPU `kvm_init_params` value, built in
  `cpu_prepare_hyp_mode()` from `HCR_HOST_NVHE_FLAGS` or
  `HCR_HOST_NVHE_PROTECTED_FLAGS`.
- pKVM: every VM, protected or not, runs on the hyp vCPU's own `hcr_el2`,
  built by `pkvm_vcpu_reset_hcr()` in `pkvm_vcpu_init_traps()`.
- Protected guest: `pvm_init_traps_hcr()` then adds traps from the hyp ID
  registers.
- From the host, at load: `handle___pkvm_vcpu_load()` takes `HCR_TWI` and
  `HCR_TWE` for a protected vCPU.
- From the host, at each run: `flush_hyp_vcpu()` takes `HCR_TWI`, `HCR_TWE`
  and `HCR_VSE`; no other host bit reaches the hyp copy.
