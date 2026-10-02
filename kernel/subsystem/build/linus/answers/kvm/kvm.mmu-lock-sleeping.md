- **Potentially unsafe usage**: calling `kvm_mmu_memory_cache_alloc()` under
  `mmu_lock`.
  - Unsafe: more calls than the `min` passed to the last top-up, with no test
    of the object count before them; on an empty cache it hits `WARN_ON()`,
    falls back to `GFP_ATOMIC | __GFP_ACCOUNT`, and `BUG_ON()` fires if that
    fails.
  - Safe: top up for the worst case before taking the lock, as
    `mmu_topup_memory_caches()` in `arch/x86/kvm/mmu/mmu.c` does;
    `__kvm_mmu_topup_memory_cache()` guarantees `min` objects.
  - Safe: test `kvm_mmu_memory_cache_nr_free_objects()` against the worst
    case under the lock before each use, as
    `need_topup_split_caches_or_resched()` does before
    `shadow_mmu_split_huge_page()`.
- `__kvm_mmu_topup_memory_cache()`: guarantees `min` objects, not capacity; it
  returns 0 at once when `nobjs >= min`, and returns 0 after a failed
  allocation if `min` was reached.
- `__kvm_mmu_topup_memory_cache()` also returns `-EIO`: zero capacity, a
  capacity that differs from an earlier top-up, or `init_value` combined with
  `kmem_cache` or `gfp_zero`.
- Memory cache helpers: compiled only where the arch defines
  `KVM_ARCH_NR_OBJS_PER_MEMORY_CACHE`; s390 and powerpc do not.
- Caches are not all per vCPU: x86 `split_desc_cache`,
  `split_page_header_cache` and `split_shadow_page_cache` are per VM and
  `topup_split_caches()` asserts `slots_lock`; `kvm_phys_addr_ioremap()` in
  `arch/arm64/kvm/mmu.c` uses one on the stack.
- x86 TDP MMU eager split: `tdp_mmu_split_huge_pages_root()` always drops
  `mmu_lock` before `tdp_mmu_alloc_sp_for_split()`, which uses
  `GFP_KERNEL_ACCOUNT`; there is no attempt under the lock.
