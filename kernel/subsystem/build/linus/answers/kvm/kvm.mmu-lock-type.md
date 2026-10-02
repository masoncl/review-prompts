- `KVM_HAVE_MMU_RWLOCK`: defined by x86, arm64, riscv and s390; search for the
  name. Other architectures get a spinlock.
- `kvm_mmu_invalidate_start()`, `kvm_mmu_invalidate_range_add()` and
  `kvm_mmu_invalidate_end()`: assert write mode with
  `lockdep_assert_held_write()`, so arch code holding the lock for read may
  not call them.
