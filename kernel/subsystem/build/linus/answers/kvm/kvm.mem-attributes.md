- Pre pass `on_lock`: `kvm_mmu_invalidate_start()` in
  `virt/kvm/kvm_main.c`.
- `kvm_vm_set_mem_attributes()` does not call `xa_store_range()`; it
  reserves per gfn with `xa_reserve()`, then stores per gfn with
  `xa_store()`.
- Clearing (`attributes` is 0): the `xa_reserve()` loop is skipped, so
  nothing after the early return can fail.
- Pre handler: `kvm_pre_set_memory_attributes()`, which calls
  `kvm_mmu_invalidate_range_add()` and then
  `kvm_arch_pre_set_memory_attributes()`; it is not
  `kvm_mmu_unmap_gfn_range()`.
- Post pass order: `kvm_mmu_invalidate_end()` is the `on_lock`, so it runs
  before the first `kvm_arch_post_set_memory_attributes()` call, in the same
  `mmu_lock` hold.
- Range that overlaps no memslot: `kvm_handle_gfn_range()` takes no
  `mmu_lock` and runs neither `on_lock` nor hook; the xarray is still
  updated and `mmu_invalidate_seq` does not change.
- Hooks: called once per overlapping memslot in each address space, with
  the range clamped to that memslot.
