- vCPU register state of a protected VM: not protected from the host in this
  tree. `flush_hyp_vcpu()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` copies the
  host's `arch.ctxt` into the hyp vCPU before every run and `sync_hyp_vcpu()`
  copies it back; `Documentation/virt/kvm/arm/pkvm.rst` lists "CPU state
  isolation" as Unimplemented.
- DMA: nothing under `arch/arm64/kvm/` programs an IOMMU;
  `Documentation/virt/kvm/arm/pkvm.rst` lists "DMA isolation using an IOMMU"
  as Unimplemented.
- pVM memory: a page is protected only once it is donated, which happens
  lazily on a guest stage-2 fault (`pkvm_pgtable_stage2_map()` in
  `arch/arm64/kvm/pkvm.c` calling `__pkvm_host_donate_guest`).
- Host access to a donated pVM page: the host can destroy the page but not
  read it. `__pkvm_host_force_reclaim_page_guest()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` zeroes it with `hyp_poison_page()`,
  marks the guest PTE `KVM_GUEST_INVALID_PTE_TYPE_POISONED` and returns the
  page to the host.
- SMCs that are neither PSCI nor FF-A: `handle_host_smc()` passes them to EL3
  with the host's x0-x17 unchanged, through `default_host_smc_handler()`.
  Apart from the two refusals at the top of `handle_host_smc()` (non-zero SMC
  immediate, upper 32 bits of the id set), no code filters them; the comment
  in `kvm_host_ffa_handler()` gives the assumption that firmware exposes no
  access to arbitrary non-secure memory.
- `Documentation/virt/kvm/arm/pkvm.rst`: says nothing about side channels,
  availability, physical attacks or EL3. It lists the isolation mechanisms
  and their status.
