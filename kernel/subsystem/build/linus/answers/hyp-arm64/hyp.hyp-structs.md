- EL2 copy holding host pointers: `hyp_vcpu->vcpu.arch.sve_state` points at
  the host's pinned SVE buffer; for a non-protected vCPU the timer
  `offset.vm_offset` pointers point into `hyp_vm->host_kvm`. See
  `pkvm_vcpu_init_sve()` and `init_pkvm_hyp_vcpu()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c`.
- `__get_host_hyp_vcpus()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`: turns a
  host vCPU pointer from a register into the pair (host vCPU, hyp vCPU).
  Under pKVM it returns NULL for both unless the loaded hyp vCPU's
  `host_vcpu` equals the pointer.
- `hyp_vcpu` NULL with a non-NULL host vCPU: pKVM is off, and the handler
  runs on the host's `struct kvm_vcpu` directly, as `handle___kvm_vcpu_run()`
  does.
- `container_of(vcpu, struct pkvm_hyp_vcpu, vcpu)`: valid only when `vcpu`
  is the embedded copy; `pkvm_memshare_call()` uses it on the vCPU that
  `__kvm_vcpu_run()` was given.
- Copies between host and hyp vCPU: not only `flush_hyp_vcpu()` and
  `sync_hyp_vcpu()`. For example `handle___pkvm_vcpu_load()` copies `fgt`
  for a non-protected vCPU, `handle___pkvm_vcpu_put()` and
  `handle___pkvm_vcpu_sync_state()` call `sync_hyp_vcpu_state()`, and
  `pkvm_refill_memcache()` reads the host memcache.
- `READ_ONCE()` on host fields: not uniform. Most of `flush_hyp_vcpu()` and
  of `pkvm_init_features_from_host()` use plain assignment; `READ_ONCE()` is
  on, for example, `created_vcpus`, `arch.pkvm.handle`, `vcpu_idx`,
  `sve_max_vl`.
- `hyp_vm->host_kvm` and `hyp_vcpu->host_vcpu`: stored as hyp VAs;
  `handle___pkvm_init_vm()` and `handle___pkvm_init_vcpu()` apply
  `kern_hyp_va()` before the call.
