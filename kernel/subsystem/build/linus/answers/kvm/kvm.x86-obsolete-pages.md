- TDP MMU pages: obsolete for `is_obsolete_sp()` when `role.invalid` is set;
  only the generation comparison is skipped for them.
- The generation toggle is in `__kvm_mmu_zap_all_fast_front_half()` in
  `arch/x86/kvm/mmu/mmu.c`, which asserts `slots_lock` and `mmu_lock` held
  for write.
- `__kvm_mmu_zap_all_fast_front_half()` has two callers:
  `kvm_mmu_zap_all_fast()` and `kvm_arch_flush_shadow_memslot()`, the latter
  only when its `zap_all` condition holds.
- Obsolete roots in `kvm_zap_obsolete_pages()`: not skipped, there is no
  `root_count` test in the walk.
- A root with nonzero `root_count`: `__kvm_mmu_prepare_zap_page()` removes it
  from `active_mmu_pages` with `list_del()` and does not put it on the
  invalid list.
- Restart from the tail in `kvm_zap_obsolete_pages()`: makes progress only
  because every page given to `__kvm_mmu_prepare_zap_page()` leaves
  `active_mmu_pages`.
- An invalid page found on `active_mmu_pages` by `kvm_zap_obsolete_pages()`:
  skipped with `WARN_ON_ONCE(sp->role.invalid)` and `continue`, not zapped.
