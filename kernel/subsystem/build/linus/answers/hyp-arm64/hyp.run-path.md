- Pointer check under pKVM: `__get_host_hyp_vcpus()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c` requires a loaded hyp vCPU whose
  `host_vcpu` equals `kern_hyp_va()` of x1; otherwise both pointers are NULL
  and the run returns `-EINVAL`.
- x1 under pKVM: compared, never dereferenced; host state is reached through
  `hyp_vcpu->host_vcpu`.
- Refusals in `handle___kvm_vcpu_run()`: exactly two, both `-EINVAL`: the
  pointer check above, then (pKVM only) `system_supports_sme()` with non-zero
  `SYS_SVCR`, tested before `flush_hyp_vcpu()`.
- `handle___kvm_vcpu_run()`: has no test of `is_dying` and none of pending
  requests.
- `handle___pkvm_vcpu_load()`: writes no return register, so a refused load
  is not reported; with no hyp vCPU loaded the next run returns `-EINVAL`.
- `handle___vgic_v3_save_aprs()` and `handle___vgic_v3_restore_vmcr_aprs()`:
  `get_host_hyp_vcpus_from_vgic_v3_cpu_if()` applies the same check after
  `container_of()` on the passed `struct vgic_v3_cpu_if`.
