- `smp_rmb()` between the two reads: only in `mmu_invalidate_retry()`;
  `mmu_invalidate_retry_gfn()` has none, and
  `mmu_invalidate_retry_gfn_unsafe()` has none.
- `mmu_invalidate_retry()`: no lockdep assertion.
  - Book3S HV HPT calls it under `lock_rmap()` and not `mmu_lock`, in
    `kvmppc_book3s_hv_page_fault()` and `kvmppc_do_h_enter()`.
- `mmu_invalidate_retry_gfn()`: `lockdep_assert_held()`, so read or write.
- `mmu_invalidate_retry_gfn()` with count non-zero and a range field still
  `INVALID_GPA`: `WARN_ON_ONCE()` and return 1.
- `mmu_invalidate_retry_gfn_unsafe()`: `READ_ONCE()` on the count and the
  sequence only; the range fields are plain reads and may be stale.
- Users outside x86 of the gfn form, for example: loongarch
  `kvm_map_page()`, riscv `kvm_riscv_mmu_dirty_log_write_fault_fast()`, s390
  `kvm_s390_faultin_gfn()`.
- riscv `kvm_riscv_mmu_map()` and arm64 `kvm_s2_fault_map()`, `gmem_abort()`
  and `kvm_translate_vncr()`: use `mmu_invalidate_retry()`.
- `mmu_invalidate_retry_gfn_unsafe()` users, for example: x86
  `kvm_mmu_faultin_pfn()`, before and after the lookup, and s390
  `kvm_s390_faultin_gfn()`.
