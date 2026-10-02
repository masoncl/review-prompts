- Arguments: hyp virtual addresses; callers convert first with
  `kern_hyp_va()` or `hyp_phys_to_virt()`.
- Alignment: the range is rounded outward to page boundaries; nothing checks
  that it was aligned.
- Checks, under `host_mmu.lock` then `pkvm_pgd_lock`, for every page: the
  range lies in one memory region that is not `MEMBLOCK_NOMAP`
  (`check_range_allowed_memory()`), host state is `PKVM_PAGE_SHARED_OWNED`,
  hyp state is `PKVM_PAGE_SHARED_BORROWED`.
- Error value: `-EINVAL` when the range crosses a region boundary, otherwise
  `-EPERM`; `init_pkvm_hyp_vcpu()` reports a failed pin of the host
  `struct kvm_vcpu` as `-EBUSY`.
- Mapping: `__pkvm_host_share_hyp()` only changes page state. The pin that
  takes `refcount` from 0 to 1 creates the EL2 mapping, and the unpin that
  takes it from 1 to 0 removes it with `kvm_pgtable_hyp_unmap()`.
- Guaranteed while pinned: the page is mapped at EL2, and
  `__pkvm_host_unshare_hyp()` fails with `-EBUSY`
  (`__hyp_check_page_count_range()`).
- `refcount` in `struct hyp_page`: a `u16`; `hyp_page_ref_inc()` hits
  `BUG_ON()` at `USHRT_MAX`, it does not wrap.
- Life of a hyp VM: the host `struct kvm`, pinned in `__pkvm_init_vm()`
  itself and unpinned in `__pkvm_finalize_teardown_vm()`. There is no
  unpin_host_kvm() and no __pkvm_teardown_vm() in this tree.
- Life of a hyp vCPU: the host `struct kvm_vcpu`, and the SVE state buffer
  when the hyp copy has `KVM_ARM_VCPU_SVE` (`pkvm_vcpu_init_sve()`). No
  `struct user_fpsimd_state` area is pinned.
- vCPU pins: dropped only by `unpin_host_vcpus()` at VM teardown, or on the
  error path of `__pkvm_init_vcpu()`; there is no per-vCPU destroy.
- Relying on the `struct kvm` pin: the timer `vm_offset` pointers that
  `init_pkvm_hyp_vcpu()` sets for non-protected vCPUs, and `teardown_mc` and
  `stage2_teardown_mc`, which teardown writes through `hyp_vm->host_kvm`.
