- `pkvm_load_hyp_vcpu()` returns NULL when: this CPU's `loaded_hyp_vcpu` is
  set (tested before the lock); the lookup returns NULL; the VM `is_dying`;
  `vcpu_idx` is at or above `hyp_vm->kvm.created_vcpus`; the slot is NULL;
  `hyp_vcpu->loaded_hyp_vcpu` is set.
- Load before the hyp VM exists: fails, since the slot holds
  `RESERVED_ENTRY`; the host's `kvm_arch_vcpu_load()` does not look at the
  result.
- No vCPU loaded, handlers that return a value: `-EINVAL`, for example
  `handle___pkvm_host_donate_guest()` and
  `handle___pkvm_vcpu_in_poison_fault()`.
- No vCPU loaded, handlers that return nothing: silent return, for example
  `handle___pkvm_vcpu_sync_state()` and, under pKVM,
  `handle___vgic_v3_save_aprs()`.
- `handle___pkvm_host_donate_guest()`: also `-EINVAL` when the loaded vCPU
  is not protected; share, relax-perms and mkyoung when it is protected.
- Memcache topup: no hypercall; `pkvm_refill_memcache()` runs inside the
  donate and share handlers.
