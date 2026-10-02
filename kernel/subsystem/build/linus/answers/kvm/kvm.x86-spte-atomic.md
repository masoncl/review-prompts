- `spte_needs_atomic_update()` in `arch/x86/kvm/mmu/spte.c`: has no presence
  test; the caller must check `is_shadow_present_pte()` first.
- `spte_needs_atomic_update()` returns true for `!spte_ad_enabled(spte)`, so
  for every A/D-disabled SPTE, not only one that is access-tracked now.
- `spte_needs_atomic_update()` ignores the Accessed bit only. A clear Dirty
  bit on a writable A/D-enabled SPTE makes the function return true.
- There is no mmu_spte_update_no_track() here; `mmu_spte_update()` in
  `arch/x86/kvm/mmu/mmu.c` picks the form itself.
- `mmu_spte_update()` and `mmu_spte_clear_track_bits()`: call
  `__update_clear_spte_slow()` only when the old SPTE is shadow-present and
  `spte_needs_atomic_update()` is true; a present SPTE that does not need it
  gets `__update_clear_spte_fast()`.
- `__update_clear_spte_slow()` with `CONFIG_X86_64`: one `xchg()` of the SPTE.
- `__update_clear_spte_slow()` without `CONFIG_X86_64`: `xchg()` of the low 32
  bits, then a plain store of the high half.
- Shadow MMU aging: `kvm_rmap_age_gfn_range()` uses `cmpxchg64()` with no
  retry, for A/D SPTEs and for access tracking; it does not call
  `clear_bit()`.
- `__rmap_clear_dirty()`: uses `test_and_clear_bit()` on `PT_WRITABLE_SHIFT`
  when `spte_ad_need_write_protect()` is true, else `mmu_spte_update()`
  through `spte_clear_dirty()`.
- There is no function kvm_tdp_mmu_spte_need_atomic_write(); the test is
  `kvm_tdp_mmu_spte_need_atomic_update()` in `arch/x86/kvm/mmu/tdp_iter.h`.
- TDP MMU aging: `kvm_tdp_mmu_age_spte()` calls `__tdp_mmu_set_spte_atomic()`
  under RCU and ignores a failure.
- `tdp_mmu_clear_spte_bits()`: its one caller is `clear_dirty_pt_masked()`,
  with `mmu_lock` held for write.
- Zap under the read lock, non-mirror SPTE: `tdp_mmu_set_spte_atomic()` writes
  `SHADOW_NONPRESENT_VALUE` directly, with no freeze step; there is no
  tdp_mmu_zap_spte_atomic() here.
- `tdp_mmu_set_spte_atomic()` on a mirror SPTE: `try_cmpxchg64()` to
  `FROZEN_SPTE`, then `__kvm_tdp_mmu_write_spte()` of the new value, or of the
  old value if the external update failed.
- `handle_removed_pt()` with `shared`: loops on
  `kvm_tdp_mmu_write_spte_atomic()` to `FROZEN_SPTE` for every entry, without
  consulting `spte_needs_atomic_update()`.
