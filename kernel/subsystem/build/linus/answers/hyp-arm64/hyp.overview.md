- Protected mode only: `pkvm_pgtable`, `host_mmu`, `hyp_vmemmap`, `vm_table`,
  `hpool` and `host_s2_pool` are set up from `__pkvm_init()`, which
  `arch/arm64/kvm/arm.c` calls only under `is_protected_kvm_enabled()`.
  Without it the hyp stage-1 is the host-owned `hyp_pgtable` in
  `arch/arm64/kvm/mmu.c`, and `handle___kvm_vcpu_run()` runs the host's
  `struct kvm_vcpu` directly.
- `struct pkvm_hyp_vm` / `struct pkvm_hyp_vcpu`: with pKVM enabled every VM,
  protected or not, gets its `struct pkvm_hyp_vm` at its first vCPU run, and
  each vCPU its `struct pkvm_hyp_vcpu` at that vCPU's own first run;
  `handle___kvm_vcpu_run()` returns `-EINVAL` unless the loaded hyp vCPU
  matches the host vCPU passed in.
- Protected VM memory is donated (`__pkvm_host_donate_guest()`, host loses
  access); non-protected VM memory is shared (`__pkvm_host_share_guest()`,
  host keeps access). Each hypercall handler rejects the other kind of VM.
- `struct hyp_page` records a state, not the other party. For a page whose
  host state is `PKVM_NOPAGE`, hyp text excepted, the owner is in the host
  stage-2 invalid PTE: type `KVM_HOST_INVALID_PTE_TYPE_DONATION`, an
  `enum pkvm_component_id`, and for a guest its handle and gfn; see
  `host_stage2_set_owner_metadata_locked()`.
- Host state `PKVM_PAGE_SHARED_OWNED` has three meanings: shared with hyp
  (hyp state is `PKVM_PAGE_SHARED_BORROWED`), shared with non-protected
  guests (`host_share_guest_count` is non-zero), or shared over FF-A
  (`__pkvm_host_share_ffa()`, no counterpart recorded).
- Host-side `struct kvm_pgtable` of a guest under pKVM is not a page table:
  its page-table fields share a union with `pkvm_mappings`, and only
  `pkvm_mappings` (interval tree of `struct pkvm_mapping`) and `mmu` are
  set. `KVM_PGT_FN()` in `arch/arm64/kvm/mmu.c` routes stage-2 calls to the
  `pkvm_pgtable_stage2_map()` family in `arch/arm64/kvm/pkvm.c`.
- `struct kvm_nvhe_init_params` stays live after init: `__deactivate_traps()`
  in `arch/arm64/kvm/hyp/nvhe/switch.c` reloads `hcr_el2` from it each time
  `__kvm_vcpu_run()` returns to the host,
  `arch/arm64/kvm/hyp/nvhe/psci-relay.c` passes it to CPU_ON and suspend
  entry, and `__pkvm_prot_finalize()` writes `vttbr`, `vtcr` and `hcr_el2`
  into it.
- `struct kvm_cpu_context`: a third per-CPU instance, `kvm_hyp_ctxt`, exists
  beside the host one in `struct kvm_host_data` and the one in each vCPU.
- Lock order: `vm_table_lock`, then `host_mmu.lock`, then `pkvm_pgd_lock` or
  the VM `lock`; `enum pkvm_component_id` lists host, hyp, guest in that
  order.
- EL2 tracing: `struct hyp_trace_buffer` in `arch/arm64/kvm/hyp/nvhe/trace.c`,
  built under `CONFIG_NVHE_EL2_TRACING`, loaded from a host-supplied
  `struct hyp_trace_desc` by `__tracing_load()`.
- There is no `struct` named kvm_hyp_req, kvm_iommu or hyp_arm_smmu, and no
  IOMMU code under `arch/arm64/kvm/`.
- There is no __kvm_call_hyp(); the host issues hypercalls with
  `kvm_call_hyp_nvhe()` in `arch/arm64/include/asm/kvm_host.h`.
- There is no pkvm_handle_psci(); `kvm_host_psci_handler()` serves host
  SMCs, and protected-guest HVCs go to `kvm_handle_pvm_hvc64()`, which
  returns anything it does not list to the host.
