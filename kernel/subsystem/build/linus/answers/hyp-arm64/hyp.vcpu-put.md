- `handle___pkvm_vcpu_put()`: has no `is_protected_kvm_enabled()` test; it
  acts on `pkvm_get_loaded_hyp_vcpu()` if that is not NULL.
- Non-protected vCPU: put calls `sync_hyp_vcpu_state()`, which copies
  registers to the host vCPU, unless the host vCPU has
  `PKVM_HOST_STATE_DIRTY` set.
- Host after put: `kvm_arch_vcpu_put()` sets `PKVM_HOST_STATE_DIRTY` for a
  non-protected VM, so the next `flush_hyp_vcpu()` copies host state in.
- `hyp_page_ref_dec()`: has `BUG_ON(!p->refcount)`, so a
  `pkvm_put_hyp_vcpu()` that finds the VM's count at zero is fatal at EL2. A
  second `__pkvm_vcpu_put` hypercall is not: `pkvm_get_loaded_hyp_vcpu()` is
  then NULL and `handle___pkvm_vcpu_put()` does nothing.
- **Unsafe usage**: calling `pkvm_put_hyp_vcpu()` with a vCPU that is not
  this CPU's loaded one.
  - Safe: pass `pkvm_get_loaded_hyp_vcpu()`, as `handle___pkvm_vcpu_put()`
    does; `pkvm_put_hyp_vcpu()` writes NULL to this CPU's `loaded_hyp_vcpu`
    whatever it is given.
