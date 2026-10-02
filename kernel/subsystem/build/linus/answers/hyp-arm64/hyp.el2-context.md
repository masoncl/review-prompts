- `handle_trap()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: has no SVE or FP
  case; an `ESR_ELx_EC_SYS64` trap goes to `handle_host_mte()`, which injects
  an UNDEF into the host or returns false, and `handle_trap()` then falls
  through to `BUG()`.
- SError: unmasked for one `isb` in `__guest_exit`
  (`arch/arm64/kvm/hyp/entry.S`), only without `ARM64_HAS_RAS_EXTN` and when
  ISR_EL1.A is set.
- That window is inside the `handle_trap()` call chain: `handle_host_hcall()`
  -> `handle___kvm_vcpu_run()` -> `__kvm_vcpu_run()` -> `__guest_enter`, with
  the guest vector installed.
- IRQ and FIQ masking is relied on by `__vgic_v3_get_gic_config()` in
  `arch/arm64/kvm/hyp/vgic-v3-sr.c`: on nVHE it sets `HCR_AMO | HCR_FMO |
  HCR_IMO` without touching DAIF.
- Per-CPU data is not always private to its CPU: `psci_cpu_on()` in
  `arch/arm64/kvm/hyp/nvhe/psci-relay.c` writes the target CPU's
  `cpu_on_args` through `per_cpu_ptr()`, serialised by
  `try_acquire_boot_args()`.
- There is no __hyp_per_cpu symbol; `__hyp_per_cpu_offset()` is in
  `arch/arm64/kvm/hyp/nvhe/hyp-smp.c`.
- Host memory can change under a read from another CPU: hyp copies a field
  once, for example the `READ_ONCE()` reads of `host_vcpu` and `host_kvm`
  fields in `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- Kernel tracepoints are absent, but `handle_trap()` calls
  `trace_hyp_enter()` and `trace_hyp_exit()`: hyp's own events from
  `HYP_EVENT()` in `arch/arm64/kvm/hyp/include/nvhe/trace.h`, empty inlines
  without `CONFIG_NVHE_EL2_TRACING`.
- `CONFIG_UBSAN_KVM_EL2`: builds nVHE objects with UBSAN in trap mode; a hit
  is a `brk` that ends in `hyp_panic()`.
