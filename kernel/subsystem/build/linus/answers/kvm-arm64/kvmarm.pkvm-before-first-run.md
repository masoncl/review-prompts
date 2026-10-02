- `kvm_arch_vcpu_load()` issues `__pkvm_vcpu_load` on every load once pKVM is
  on; before creation `pkvm_load_hyp_vcpu()` finds nothing and
  `handle___pkvm_vcpu_load()` returns without an error.
- `pkvm_get_loaded_hyp_vcpu()`: NULL unless a `__pkvm_vcpu_load` succeeded on
  this CPU and no `__pkvm_vcpu_put` followed. A load cannot succeed before the
  hyp VM exists, or after another vCPU's first run created the hyp VM but
  before this vCPU's own `__pkvm_init_vcpu`.
- Handlers that use the loaded hyp vCPU and return `-EINVAL` on NULL:
  - `handle___pkvm_host_share_guest()`,
    `handle___pkvm_host_relax_perms_guest()` and
    `handle___pkvm_host_mkyoung_guest()`: also `-EINVAL` if the hyp vCPU is
    protected.
  - `handle___pkvm_host_donate_guest()`: also `-EINVAL` if the hyp vCPU is
    not protected.
  - `handle___pkvm_vcpu_in_poison_fault()`.
- `handle___pkvm_vcpu_put()` and `handle___pkvm_vcpu_sync_state()`: return
  silently on NULL.
- `pkvm_pgtable_stage2_mkyoung()` on the host wraps the hypercall in
  `WARN_ON()`, so a NULL loaded vCPU there produces a warning.
- **Unsafe usage**: an ioctl or capability that calls
  `pkvm_pgtable_stage2_map()`, `pkvm_pgtable_stage2_relax_perms()` or
  `pkvm_pgtable_stage2_mkyoung()` for a vCPU that has not been through
  `kvm_arch_vcpu_run_pid_change()`.
  - Unsafe: no hyp vCPU is loaded on this CPU, so each hypercall returns
    `-EINVAL` and nothing is mapped.
  - Safe: the stage-2 fault path (`user_mem_abort()`, `gmem_abort()`,
    `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`), which runs inside
    `kvm_arch_vcpu_ioctl_run()` after `pkvm_create_hyp_vm()`,
    `pkvm_create_hyp_vcpu()` and then `vcpu_load()`.
  - Safe: `pkvm_pgtable_stage2_unmap()`, `pkvm_pgtable_stage2_wrprotect()`
    and `pkvm_pgtable_stage2_test_clear_young()` before first run; their
    hypercalls name the VM by handle and need no loaded hyp vCPU, and before
    the hyp VM exists `pgt->pkvm_mappings` is empty, so they issue no
    hypercall.
- Order matters: a `vcpu_load()` done before creation is not repaired by
  creation; only `handle___pkvm_vcpu_load()` sets the loaded hyp vCPU.
- `__guest_check_pgtable_memcache()`: share and donate return `-ENOMEM`
  unless the hyp vCPU's memcache holds `kvm_mmu_cache_min_pages()` pages,
  even when the map allocates nothing.
- Creating the hyp VM early fixes what `__pkvm_init_vm` copies, for example
  the vCPU count, `vcpu_features` and, for a non-protected VM, `arch.flags`;
  `vm_copy_id_regs()` returns `-EINVAL` unless the host has
  `KVM_ARCH_FLAG_ID_REGS_INITIALIZED`.
