- There is no __kvm_handle_hva_range() here; `kvm_handle_hva_range()` in
  `virt/kvm/kvm_main.c` is the hva walker and returns `kvm_mn_ret_t`.
- `on_lock` of `kvm_mmu_notifier_invalidate_range_start()`:
  `kvm_mmu_invalidate_start()`.
- `range->lockless`: the only field that changes locking;
  `kvm_handle_hva_range()` then never takes `mmu_lock` and calls the handler
  under SRCU alone.
- A lockless handler may lock for itself: s390 `kvm_age_gfn()` and
  `kvm_test_age_gfn()` take `mmu_lock` for read.
- `range->may_block`: only copied into `struct kvm_gfn_range`; no effect on
  when `kvm_handle_hva_range()` locks.
- `kvm_age_hva_range()`: sets `lockless` from
  `CONFIG_KVM_MMU_LOCKLESS_AGING`, which x86 and s390 select.
- `lockless` with a non-null `on_lock`: `WARN_ON_ONCE()` and return before
  any handler is called.
- Flush with `lockless`: `kvm_flush_remote_tlbs()` runs with no `mmu_lock`
  held.
- `kvm_mmu_notifier_clear_flush_young()`: `flush_on_ret` is
  `!IS_ENABLED(CONFIG_KVM_ELIDE_TLB_FLUSH_IF_YOUNG)`; x86 selects that
  option, so no x86 aging callback flushes.
