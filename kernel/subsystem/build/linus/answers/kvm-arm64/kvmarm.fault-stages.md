- `user_mem_abort()` in `arch/arm64/kvm/mmu.c` is a chain of four calls:

| Order | Function | `mmu_lock` | Continue when it returns |
|---|---|---|---|
| 1 | `topup_mmu_memcache()`, skipped on some permission faults | not held | 0 |
| 2 | `kvm_s2_fault_pin_pfn()` | not held | 1 |
| 3 | `kvm_s2_fault_compute_prot()` | not held | 0 |
| 4 | `kvm_s2_fault_map()` | takes and drops it | n/a |

- `kvm_s2_fault_pin_pfn()`: 0 means handled (hwpoison signal sent), not
  "continue"; `user_mem_abort()` returns any value other than 1 as is.
- `kvm_s2_fault_compute_prot()`: 1 means an exclusive/atomic abort was
  injected.
- `kvm_s2_fault_pin_pfn()` calls `kvm_s2_fault_get_vma_info()` (VMA lookup
  under `mmap_read_lock()`, size from `kvm_s2_resolve_vma_size()`), then
  `__kvm_faultin_pfn()`.
- `kvm_s2_fault_compute_prot()`, before the lock: holds the `-ENOEXEC` test,
  the exclusive/atomic injection, the `prot` computation including the
  nested adjustments, and the MTE `-EFAULT` refusal.
- `kvm_s2_fault_map()`, under the lock: `mmu_invalidate_retry()`,
  `transparent_hugepage_adjust()`, `sanitise_mte_tags()`, the map or
  relax-perms call, and the page release.
- State passing: there is no struct kvm_s2_fault.
  - `struct kvm_s2_fault_desc`: built once in `kvm_handle_guest_abort()`,
    passed `const` to `user_mem_abort()`, `gmem_abort()` and
    `pkvm_mem_abort()`.
  - `struct kvm_s2_fault_vma_info`: zero-initialised in `user_mem_abort()`,
    written only by stage 2, `const` in stages 3 and 4.
  - `prot`: out-parameter of stage 3, passed by value to stage 4.
- Names: `user_mem_abort()` has no logging_active and no `force_pte` local;
  when `memslot_is_logging()`, `kvm_s2_resolve_vma_size()` sets
  `s2vi->max_map_size` to `PAGE_SIZE`.
- `pkvm_mem_abort()` in `arch/arm64/kvm/mmu.c`: takes every fault that
  reaches the final dispatch of `kvm_handle_guest_abort()` for a
  `kvm_vm_is_protected()` VM, whatever the slot type.
  - It does not sample `mmu_invalidate_seq` or call `mmu_invalidate_retry()`.
  - It calls `pkvm_pgtable_stage2_map()` directly, always `PAGE_SIZE` and
    `KVM_PGTABLE_PROT_RWX`.
- Non-protected VM on a pKVM host: goes through `user_mem_abort()` or
  `gmem_abort()`; `KVM_PGT_FN()` selects the `pkvm_pgtable_stage2_map()`
  family.
