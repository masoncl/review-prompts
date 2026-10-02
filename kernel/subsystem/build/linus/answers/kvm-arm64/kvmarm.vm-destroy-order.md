- Order inside `kvm_arch_destroy_vm()`, after it frees `pmu_filter` and
  `supported_cpus`: `kvm_vgic_destroy()`, `pkvm_destroy_hyp_vm()` (only with
  `is_protected_kvm_enabled()`), `kvm_uninit_stage2_mmu()`,
  `kvm_destroy_mpidr_data()`, free of `sysreg_masks`, `kvm_destroy_vcpus()`,
  `kvm_unshare_hyp()` of the `struct kvm`, `kvm_destroy_nested()`,
  `kvm_arm_teardown_hypercalls()`.
- Stage-2 on the `kvm_destroy_vm()` path: already torn down by
  `kvm_arch_flush_shadow_all()`, reached through
  `kvm_mmu_notifier_release()`, at the latest from
  `mmu_notifier_unregister()`, before `kvm_arch_destroy_vm()`; the call
  inside finds `mmu->pgt` `NULL`.
- Stage-2 on the `kvm_create_vm()` error path that never registered the
  notifier: the call inside `kvm_arch_destroy_vm()` is the only teardown.
- pKVM dependency runs against the in-function order:
  `pkvm_pgtable_stage2_destroy_range()` issues `__pkvm_start_teardown_vm` and
  uses `kvm->arch.pkvm.handle`; `__pkvm_destroy_hyp_vm()` then issues
  `__pkvm_finalize_teardown_vm`, which fails unless `is_dying`, and zeroes
  the handle.
- With the handle zero, `pkvm_pgtable_stage2_destroy_range()` returns at
  once, so stage-2 teardown that had not run before `pkvm_destroy_hyp_vm()`
  reclaims nothing.
- `pkvm_destroy_hyp_vm()` before `kvm_destroy_vcpus()`:
  `__pkvm_finalize_teardown_vm` unpins each host vCPU, its SVE state and the
  host `struct kvm`; `kvm_arm_vcpu_destroy()` and the later
  `kvm_unshare_hyp()` unshare them.
- `kvm_vgic_destroy()`: runs `__kvm_vgic_vcpu_destroy()` on each vCPU;
  `kvm_arch_vcpu_destroy()` later runs it again on each vCPU through
  `kvm_vgic_vcpu_destroy()`.
