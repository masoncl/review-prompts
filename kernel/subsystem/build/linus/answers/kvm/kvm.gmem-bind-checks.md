- Overlap with an existing binding: `kvm_gmem_bind()` returns `-EEXIST`;
  every other failure after `fget()` returns `-EINVAL`.
- `offset`: type `uoff_t`, so there is no sign test; the range tests are
  `PAGE_ALIGNED(offset)` and `offset + size > i_size_read(inode)` only.
- Wrap of `offset + size`: not tested in `kvm_gmem_bind()`;
  `kvm_set_memory_region()` rejects it with `-EINVAL` before the call.
- `kvm_gmem_release()`: takes `kvm->slots_lock` itself, then
  `filemap_invalidate_lock()` inside it.
- `kvm_gmem_bind()` and `kvm_gmem_unbind()`: neither asserts
  `kvm->slots_lock`; the `lockdep_assert_held()` is in
  `kvm_set_memory_region()`.
- `kvm_gmem_unbind()`: does not call `synchronize_rcu()`; it relies on
  `synchronize_srcu_expedited()` in `kvm_swap_active_memslots()` having run
  before the old memslot is freed.
