- Locks: `hyp_fixmap_map()` takes none, asserts none and checks nothing about
  the PA. What keeps the page in its state is the caller's business.
- `hyp_poison_page()`: both callers hold the host and the guest component
  lock. `__tracing_enable_event()` holds no lock; its page is hyp rodata.
- In-tree pairs: `hyp_poison_page()` and `__apply_guest_page()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`, and `__tracing_enable_event()`.
  `fix_host_ownership_walker()` does not use the fixmap.
- **Unsafe usage**: calling `hyp_fixmap_map()` before `hyp_create_fixmap()`
  has run.
  - Unsafe: in non-protected nVHE, or before `__pkvm_init_finalise()`. The
    slot's `ptep` is NULL and `fixmap_map_slot()` dereferences it.
  - Safe: `hyp_poison_page()`. Its hypercalls are above
    `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`, which `handle_host_hcall()` rejects
    until `kvm_protected_mode_initialized` is set;
    `pkvm_ownership_selftest()` runs after `hyp_create_fixmap()` in
    `__pkvm_init_finalise()`.
  - Safe: `__tracing_enable_event()`, although its hypercall is below
    `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`. Its only host caller,
    `hyp_trace_enable_event()` in `arch/arm64/kvm/hyp_trace.c`, issues it
    only when `is_protected_kvm_enabled()`, and is registered from
    `init_subsystems()`, after `init_hyp_mode()` has run `__pkvm_init`.
- **Potentially unsafe usage**: accessing `PAGE_SIZE` bytes from the returned
  pointer.
  - Unsafe: when the PA is not page-aligned. The pointer includes the offset,
    and the slot maps one page, so the access runs past the slot.
  - Safe: when the PA is page-aligned, as in `hyp_poison_page()`.
    `__pkvm_host_force_reclaim_page_guest()` masks with `PAGE_MASK`;
    `get_valid_guest_pte()` returns `kvm_pte_to_phys()` of a last-level PTE.
- **Unsafe usage**: holding a `hyp_fixblock_map()` mapping and a
  `hyp_fixmap_map()` mapping at once.
  - Unsafe: without `HAS_FIXBLOCK` (`PAGE_SHIFT >= 16`), `hyp_fixblock_map()`
    is `hyp_fixmap_map()` on the same per-CPU slot. The second map retargets
    the first.
  - Safe: one mapping at a time, as in the loop of `__apply_guest_page()`.
- **Potentially unsafe usage**: ending a `hyp_fixblock_map()` with
  `hyp_fixmap_unmap()`.
  - Unsafe: when the map returned `PMD_SIZE`, that is with `HAS_FIXBLOCK`.
    `hyp_fixblock_map()` then returns holding `hyp_fixblock_lock`, which only
    `hyp_fixblock_unmap()` releases; the next `hyp_fixblock_map()` on any CPU
    spins.
  - Safe: when the map returned `PAGE_SIZE`, that is without `HAS_FIXBLOCK`,
    where `hyp_fixblock_map()` took no lock and `hyp_fixblock_unmap()` is
    `hyp_fixmap_unmap()`. `__apply_guest_page()` tests the returned
    `map_size` against `PMD_SIZE` to pick `hyp_fixblock_unmap()` or
    `hyp_fixmap_unmap()`.
