- Publication: `smp_store_release()` in `register_hyp_vcpu()`, paired with
  `smp_load_acquire()` in `pkvm_load_hyp_vcpu()`; both also run under
  `vm_table_lock`.
- Index bound: `hyp_vm->kvm.created_vcpus`, fixed when the hyp VM was
  created; `struct pkvm_hyp_vm` has no vCPU counter and nothing is
  incremented.
- Index: any free slot below the bound, not the next one; an occupied slot
  or an index at or above the bound returns `-EINVAL`.
- SVE pin: `pkvm_vcpu_init_sve()` pins the host buffer for any vCPU whose
  hyp copy has `KVM_ARM_VCPU_SVE`, whatever the VM kind.
- `init_pkvm_hyp_vcpu()` failure after the host vCPU is pinned: unpins the
  host vCPU only; the SVE pin is its last step.
- `register_hyp_vcpu()` failure: `__pkvm_init_vcpu()` calls
  `unpin_host_vcpu()` and `unpin_host_sve_state()`.
