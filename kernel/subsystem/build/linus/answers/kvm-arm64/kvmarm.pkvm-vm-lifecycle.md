- There is no __pkvm_teardown_vm here; teardown is `__pkvm_start_teardown_vm`,
  then per-page reclaim, then `__pkvm_finalize_teardown_vm`.

| Step | Host function | Hypercall | Host locks taken |
|---|---|---|---|
| Reserve handle, at `KVM_CREATE_VM` | `pkvm_init_host_vm()` | `__pkvm_reserve_vm` | none |
| Create hyp VM, first `KVM_RUN` of any vCPU | `pkvm_create_hyp_vm()` | `__pkvm_init_vm` | `kvm->slots_lock`, then `kvm->arch.config_lock` |
| Create hyp vCPU, first `KVM_RUN` of that vCPU | `pkvm_create_hyp_vcpu()` | `__pkvm_init_vcpu` | `kvm->arch.config_lock` |
| Start teardown, first range of stage-2 free | `pkvm_pgtable_stage2_destroy_range()` | `__pkvm_start_teardown_vm` | none |
| Return guest pages | same | protected: `__pkvm_reclaim_dying_guest_page`; else `__pkvm_host_unshare_guest` | none |
| Finalize, hyp VM was created | `pkvm_destroy_hyp_vm()` | `__pkvm_finalize_teardown_vm` | `kvm->arch.config_lock` |
| Drop handle, hyp VM never created | `pkvm_destroy_hyp_vm()` | `__pkvm_unreserve_vm` | `kvm->arch.config_lock` |

- Both create steps are called from `kvm_arch_vcpu_run_pid_change()` with
  `vcpu->mutex` held by `KVM_RUN`; order is `vcpu->mutex` →
  `kvm->slots_lock` → `kvm->arch.config_lock`.
- `kvm->lock` is not held on any of these paths.
- `kvm->slots_lock` in `pkvm_create_hyp_vm()`: serialises `is_created` against
  `kvm_arch_prepare_memory_region()`.
- Start of teardown: reached from `kvm_arch_flush_shadow_all()` →
  `kvm_uninit_stage2_mmu()`, so it can run from `kvm_flush_shadow_all()` in
  `virt/kvm/kvm_main.c` before `kvm_arch_destroy_vm()`.
- `pkvm_destroy_hyp_vm()` issues finalize or unreserve, never both.
- `__pkvm_start_teardown_vm` and `__pkvm_finalize_teardown_vm`: `-EINVAL`
  while the hyp VM has a reference (a loaded vCPU counts); see
  `get_pkvm_unref_hyp_vm_locked()`.
- After `__pkvm_start_teardown_vm`: `pkvm_load_hyp_vcpu()` returns NULL for
  that VM.
- `__pkvm_init_vm` fails: EL2 returns the donated VM and PGD pages and unpins
  the host `struct kvm`; `__pkvm_create_hyp_vm()` frees both with
  `free_pages_exact()`; the handle stays reserved until
  `pkvm_destroy_hyp_vm()`.
- `__pkvm_init_vcpu` fails: EL2 unpins the host vCPU and returns the page;
  `__pkvm_create_hyp_vcpu()` frees it; the hyp VM and other hyp vCPUs stay.
- `kvm_arch_init_vm()`: nothing after `pkvm_init_host_vm()` can fail; a new
  failure point added after it has to unreserve the handle.
- Hyp VM size is fixed from `created_vcpus` at `__pkvm_init_vm`;
  `register_hyp_vcpu()` returns `-EINVAL` for a `vcpu_idx` at or beyond it.
- `__pkvm_create_hyp_vm()`: `-EINVAL` when `kvm->created_vcpus` is 0.
