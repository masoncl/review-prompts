- `slots_arch_lock`: not in the lockdep expression of `__kvm_memslots()`;
  holding it alone does not satisfy the check.
- `users_count` clause: does not cover VM creation; `kvm_create_vm()` sets
  `users_count` to 1 before `kvm_arch_init_vm()`.
- Init-time code: takes `slots_lock`, as s390 `kvm_arch_init_vm()` does
  around `kvm_set_internal_memslot()`.
- `kvm_free_memslots()`: never calls `__kvm_memslots()`; it walks
  `kvm->__memslots` directly, through `id_node[1]` only.
- Other `slots_lock`-only readers, for example: `kvm_vm_set_mem_attributes()`
  through `kvm_handle_gfn_range()`, and `kvm_mmu_rmaps_stat_show()`.
- **Unsafe usage**: using a slot pointer after a successful
  `kvm_set_internal_memslot()` or `kvm_set_memory_region()` call on that
  slot by the same holder of `slots_lock`.
  - Unsafe: `kvm_commit_memory_region()` frees `old` on `KVM_MR_DELETE`,
    `KVM_MR_MOVE` and `KVM_MR_FLAGS_ONLY`, with `slots_lock` still held.
  - Safe: copy the fields first, as `__x86_set_memory_region()` does with
    `npages` and `userspace_addr` before `kvm_set_internal_memslot()`.
  - Safe: look the slot up again by id after the update, as arm64
    `kvm_mmu_wp_memory_region()` does when called from
    `kvm_arch_commit_memory_region()`.
