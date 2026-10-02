- Refused by `kvm_arch_prepare_memory_region()` for a protected VM, all with
  `-EPERM`:

| What | When |
|---|---|
| `KVM_MR_DELETE`, `KVM_MR_MOVE` | only once `pkvm_hyp_vm_is_created()` |
| `new->flags` with `KVM_MEM_LOG_DIRTY_PAGES` or `KVM_MEM_READONLY` | always, including `KVM_MR_FLAGS_ONLY` |

- `KVM_MR_FLAGS_ONLY` and `KVM_MR_CREATE` without those flags are not refused
  by this test for a protected VM, before or after creation.
- `kvm_arch_prepare_memory_region()` does not refuse dirty logging or
  read-only slots for a non-protected VM under pKVM.
- `kvm_arch_prepare_memory_region()` has no pKVM test in its VMA loop and
  none on `guest_memfd` slots; a `VM_PFNMAP` slot is not refused on account
  of pKVM at this point.
- Refused for a protected VM at fault time, in `pkvm_mem_abort()`:
  - backing whose folio is not swap-backed (page cache of a regular file):
    `-EIO`; anonymous and shmem memory pass.
  - backing that `pin_user_pages()` cannot pin with `FOLL_LONGTERM |
    FOLL_WRITE`: `-EFAULT`.
  - a page beyond the memlock limit: error from `account_locked_vm()`.
- Protected VM mappings: `PAGE_SIZE` and `KVM_PGTABLE_PROT_RWX` only;
  `pkvm_pgtable_stage2_map()` returns `-EINVAL` otherwise.
- Protected VM pages stay pinned until `__pkvm_pgtable_stage2_reclaim()` at
  teardown; `kvm_unmap_gfn_range()`, `kvm_age_gfn()`, `kvm_test_age_gfn()`
  and `kvm_stage2_unmap_range()` do nothing for one.
- Refused for every VM once pKVM is on:
  - `kvm_phys_addr_ioremap()`: `-EPERM`.
  - device or non-cacheable mappings: `__pkvm_host_share_guest()` returns
    `-EINVAL` for any `prot` bit outside `KVM_PGTABLE_PROT_RWX`.
  - physical ranges that are not memory or are `MEMBLOCK_NOMAP`: `-EPERM`
    from `check_range_allowed_memory()`.
  - block mappings other than `PMD_SIZE`: see
    `fault_supports_stage2_huge_mapping()` and
    `__guest_check_transition_size()`.
  - `KVM_CAP_ARM_MTE` and eager page splitting: see "Restrictions on
    protected VMs"; `pkvm_pgtable_stage2_split()` warns and returns
    `-EINVAL`.
