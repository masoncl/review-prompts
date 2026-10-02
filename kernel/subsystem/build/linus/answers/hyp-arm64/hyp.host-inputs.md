- Registers versus memory: models have this right; hypercall registers are
  saved per CPU by `__host_exit`, host-owned and shared memory can be
  rewritten by another CPU at any point of a hypercall.
- `flush_hyp_vcpu()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: re-reads the
  host `struct kvm_vcpu` on every run. Besides the register context it takes
  `mdcr_el2`, `iflags` and `vsesr_el2` unmasked, for protected vCPUs too;
  from `hcr_el2` it takes only `HCR_TWI`, `HCR_TWE` and `HCR_VSE`.
- `handle_host_hcall()`: after `kvm_protected_mode_initialized`, of the ids
  in `host_hcall[]` it rejects only those below
  `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`. Every later entry of `host_hcall[]` stays
  callable by the host, in any order, on any CPU.
- `pkvm_load_hyp_vcpu()`: stops two CPUs from loading one hyp vCPU. It does
  not stop another CPU from writing the host `struct kvm_vcpu` behind it.
- Frozen at de-privilege, not host-changeable afterwards: values the host
  wrote into hyp data, rodata, bss and per-CPU sections before init, for
  example `kvm_init_params`, `hyp_memory[]` and `kvm_host_psci_config`.
  `fix_host_ownership()` in `arch/arm64/kvm/hyp/nvhe/setup.c` makes those
  pages hyp-owned.
