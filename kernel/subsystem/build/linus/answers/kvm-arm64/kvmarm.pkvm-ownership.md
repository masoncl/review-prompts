- Where each state lives:

| Component | Storage | Lock |
|---|---|---|
| Host | `__host_state` in `struct hyp_page` (`hyp_vmemmap`) | `host_mmu.lock` |
| Hypervisor | `__hyp_state_comp` in `struct hyp_page`, stored complemented | `pkvm_pgd_lock` |
| Guest | software bits of the guest stage-2 PTE | `lock` of `struct pkvm_hyp_vm` |

- Neither the host stage-2 PTE nor the hyp stage-1 PTE holds the state at run
  time; `fix_host_ownership_walker()` in `arch/arm64/kvm/hyp/nvhe/setup.c`
  reads the hyp stage-1 software bits once at init to fill `hyp_vmemmap`.
- `enum pkvm_page_state` has five values; besides the three stored ones there
  are `PKVM_NOPAGE` and `PKVM_POISON`.
- Guest `PKVM_NOPAGE` and `PKVM_POISON` are not stored in software bits;
  `guest_get_page_state()` infers them from an invalid PTE and from
  `KVM_GUEST_INVALID_PTE_TYPE_POISONED`.
- Host `PKVM_NOPAGE` is stored in `__host_state`.
- Lock order: `host_mmu.lock` first, then `pkvm_pgd_lock` or the guest
  `lock`; `vm_table_lock` is taken before `host_mmu.lock` where both are held
  (`__pkvm_host_force_reclaim_page_guest()`, `__pkvm_init_vcpu()`).
- `__host_check_page_state_range()`: asserts `host_mmu.lock` and fails with
  `-EPERM` for a range that is not memory or is `MEMBLOCK_NOMAP`.
- The assertions are real only with `CONFIG_NVHE_EL2_DEBUG`; see
  `hyp_assert_lock_held()`.
- Page donated to a protected guest: host state `PKVM_NOPAGE`, guest PTE
  `PKVM_PAGE_OWNED`, and the host stage-2 holds an invalid PTE of type
  `KVM_HOST_INVALID_PTE_TYPE_DONATION` with owner `PKVM_ID_GUEST` plus the VM
  handle and gfn; see `host_stage2_encode_gfn_meta()`.
- Shares with a non-protected guest are counted per page in
  `host_share_guest_count` of `struct hyp_page`, not in `refcount`.
- `refcount` of `struct hyp_page` counts, for example, hyp pins
  (`hyp_pin_shared_mem()`) and hyp VM references.
- `__pkvm_host_share_guest()`: a block share increments the count of every
  page in the block; `-EBUSY` at `U32_MAX`; `-EPERM` for a page that is
  `PKVM_PAGE_SHARED_OWNED` with a zero count (shared with the hypervisor or
  FF-A).
- `__pkvm_host_unshare_guest()`: the host state returns to `PKVM_PAGE_OWNED`
  only when the count reaches zero.
