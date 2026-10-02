- Unchanged: an address whose bits from `tag_lsb` up already equal `tag_val`.
  That is every hyp linear-map address, hyp image symbols included.
- Changed: an address whose bits from `tag_lsb` up differ from `tag_val`. The
  idmap always differs, because the region bit is the complement of the
  idmap's.
- `__kvm_vcpu_run()` in `arch/arm64/kvm/hyp/nvhe/switch.c`: does
  `kern_hyp_va(vcpu->arch.hw_mmu)`. It does not convert `mmu->arch`.
- `hw_mmu` under pKVM: `init_pkvm_hyp_vcpu()` in
  `arch/arm64/kvm/hyp/nvhe/pkvm.c` sets it to `&hyp_vm->kvm.arch.mmu`, already
  a hyp VA. `pkvm_load_hyp_vcpu()` does not set it.
- `timer_get_offset()` in `include/kvm/arm_arch_timer.h`: applies
  `KERN_HYP_VA()` to `vm_offset`, which `init_pkvm_hyp_vcpu()` points into
  `hyp_vm->host_kvm` for a non-protected vCPU, already converted in
  `handle___pkvm_init_vm()`.
- `kern_hyp_va(vcpu->kvm)`: for a hyp vCPU `vcpu.kvm` is `&hyp_vm->kvm`. Users
  are, for example, `vcpu_has_sve()` and `arch/arm64/kvm/hyp/vgic-v3-sr.c`.
  `arch/arm64/kvm/hyp/nvhe/tlb.c` does not call `kern_hyp_va()`.
- `kern_hyp_va(vcpu->arch.sve_state)`: `pkvm_vcpu_init_sve()` stores the
  converted pointer, and the SVE save and restore paths convert it again.
