- `struct hyp_page` has no `flags` field: ownership is the bit-fields
  `__host_state` and `__hyp_state_comp`, used through `get_host_state()`,
  `set_host_state()`, `get_hyp_state()`, `set_hyp_state()`.
- Guest state: not in `struct hyp_page`; it is in PTE software bits, read
  with `pkvm_getstate()`.
- Hyp stage-1 lock: `pkvm_pgd_lock` in `arch/arm64/kvm/hyp/nvhe/mm.c`;
  there is no pkvm_pgtable_lock.
- `set_hyp_state()` after init: reached only through
  `__hyp_set_page_state_range()`, and each of its callers holds
  `host_mmu.lock` as well as `pkvm_pgd_lock`.
- `__host_state` and `__hyp_state_comp`: adjacent 4-bit bit-fields; host
  state writers such as `__pkvm_host_share_ffa()` hold only `host_mmu.lock`.
- `host_share_guest_count`: written in `__pkvm_host_share_guest()` and
  `__pkvm_host_unshare_guest()` with `host_mmu.lock` and the VM's `lock`
  both held; `host_mmu.lock` is the one shared by all VMs.
- `refcount` of a page that is in no pool: not under a pool lock; see
  "Pool locking".
- Size: 8 bytes, enforced by
  `BUILD_BUG_ON(sizeof(struct hyp_page) != sizeof(u64))` inside
  `hyp_phys_to_page()` in `arch/arm64/kvm/hyp/include/nvhe/memory.h`;
  there is no assert next to the struct.
- `STRUCT_HYP_PAGE_SIZE`: generated from
  `arch/arm64/kvm/hyp/hyp-constants.c`.
- `hyp_back_vmemmap()`: in `arch/arm64/kvm/hyp/nvhe/mm.c`; its argument is
  the physical address of the backing memory, not a page count.
- Backing memory: `vmemmap_base`, taken with `hyp_early_alloc_contig()` in
  `divide_memory_pool()`; `recreate_hyp_mappings()` passes it on.
- Backed entries: only the vmemmap pages that cover a `hyp_memory[]` region;
  `hyp_phys_to_page()` makes no range check, so the pointer for any other
  address may be unmapped.
- Guard before dereference: for example `check_range_allowed_memory()` in
  `__host_check_page_state_range()`, `addr_is_memory()` in
  `host_stage2_adjust_range()`.
- There is no hyp_pfn_to_page(); `hyp_phys_to_page()` and
  `hyp_virt_to_page()` are the lookups.
