- `handle_host_hcall()` has two bounds, both chosen by the static key
  `kvm_protected_mode_initialized` alone:
  - key set: `hcall_min` is `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`, so the early
    region is refused;
  - key clear: `hcall_max` is `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, so every
    pKVM-only call is refused.
- The key is clear for the whole life of a non-protected nVHE or hVHE
  system, and under pKVM until `pkvm_drop_host_privileges()` runs from
  `finalize_pkvm()`, a `device_initcall_sync` in `arch/arm64/kvm/pkvm.c`.
- No pKVM-only handler tests `is_protected_kvm_enabled()` itself; the range
  check is the only gate. A pKVM-only call placed in the common region runs
  on plain nVHE.
- Index 0 (`__KVM_HOST_SMCCC_FUNC___kvm_hyp_init`) has no `HANDLE_FUNC()`
  line, so while the key is clear it is refused as a NULL slot.
- Stub HVCs (x0 below `HVC_STUB_HCALL_NR`): with `ARM64_KVM_PROTECTED_MODE`,
  `__host_hvc` in `arch/arm64/kvm/hyp/nvhe/host.S` skips the stub test, so
  they reach `handle_host_hcall()` and are refused out of range. Without it
  they go to `__kvm_handle_stub_hvc`.
- `handle_host_hcall()` returns `void` and does not use
  `array_index_nospec()`.
- `handle___kvm_vcpu_run()` with x0 success and `-EINVAL` in x1, both only
  under pKVM: when no hyp vCPU is loaded or the pointer is not its
  `host_vcpu`, and when `SVCR` is non-zero on an SME system.
- Handlers that fail without writing x1, for example
  `handle___pkvm_vcpu_load()` and `handle___pkvm_tlb_flush_vmid()` on a bad
  handle: the host cannot tell failure from success.
