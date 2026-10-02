- `__kvm_mmu_prepare_zap_page()` in `arch/x86/kvm/mmu/mmu.c`: sets
  `sp->role.invalid = 1` on every page it zaps, root or not.
- `__kvm_mmu_prepare_zap_page()` asserts nothing about the bit; its only
  assertion is `lockdep_assert_held_write(&kvm->mmu_lock)`.
- Zapping an already invalid page is an expected path: `mmu_free_root_page()`
  calls `kvm_mmu_prepare_zap_page()` when `root_count` reaches zero on an
  invalid root, and `kvm_mmu_free_roots()` then commits the list.
- Hash list: an invalid page stays hashed until `kvm_mmu_free_shadow_page()`.
- Lookup: `for_each_valid_sp()` skips the page through `is_obsolete_sp()`,
  before `kvm_mmu_find_shadow_page()` compares `role.word`.
- There is no kvm_mmu_get_page() function here, only the tracepoint
  `trace_kvm_mmu_get_page()`; `__kvm_mmu_get_shadow_page()` does the lookup or
  the allocation.
- `kvm_mmu_child_role()`: copies the parent role, does
  `WARN_ON_ONCE(role.invalid)`, then clears `role.invalid` in the child role.
- TDP MMU: `kvm_tdp_mmu_invalidate_roots()` sets the bit on roots only, and
  does not zap them.
- An invalid TDP MMU root stays on `kvm->arch.tdp_mmu_roots` until the final
  `kvm_tdp_mmu_put_root()`, and keeps its SPTEs until they are zapped, for
  example by `tdp_mmu_zap_root()`.
- Root iteration through `tdp_mmu_root_match()` in
  `arch/x86/kvm/mmu/tdp_mmu.c` skips invalid roots unless the root types
  include `KVM_INVALID_ROOTS`.
- `tdp_mmu_init_child_sp()`: copies the parent role and lowers `level`; it
  neither warns on nor clears `role.invalid`.
- `kvm_tdp_mmu_put_root()`: `KVM_BUG_ON()` if the final reference is put on a
  root that is not invalid.
