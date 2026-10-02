- `struct gmem_inode` in `virt/kvm/guest_memfd.c`: holds `policy`,
  `vfs_inode`, `gmem_file_list` and `flags`; the size is `vfs_inode.i_size`.
- `gmem_file_list`: the list that `entry` of `struct gmem_file` links on;
  walk it with `kvm_gmem_for_each_file()`. Nothing in `virt/kvm` uses a
  list in the `struct address_space`.
- Shareability state on the inode: only `GUEST_MEMFD_FLAG_INIT_SHARED` in
  `flags`; `kvm_gmem_is_private_mem()` ignores its `index` argument, so the
  whole inode is private or shared.
- VM reference: taken by `__kvm_gmem_create()`, dropped as the last step of
  `kvm_gmem_release()`. `kvm_gmem_bind()` takes no VM reference and keeps no
  file reference.
- `slot->gmem.file`: a plain `struct file *` written with `WRITE_ONCE()`,
  not `__rcu`; `kvm_gmem_get_file()` takes a reference on it with
  `get_file_active()`.
- `kvm_gmem_release()`: zaps with `__kvm_gmem_invalidate_start()` and
  `__kvm_gmem_invalidate_end()`.
- `kvm_gmem_unbind()` has three cases:
  - `slot->gmem.file` is NULL (release already ran): returns at once.
  - pointer set but `get_file_active()` fails (last `fput()` done,
    `kvm_gmem_release()` has not yet cleared the pointer): clears the
    bindings through `slot->gmem.file->private_data`; safe only because the
    caller holds `kvm->slots_lock`, which `kvm_gmem_release()` needs before
    it frees the `struct gmem_file`.
  - file alive: clears the bindings under `filemap_invalidate_lock()`.
- VM destruction: every `slot->gmem.file` is already NULL, because each file
  holds the VM until `kvm_gmem_release()` has cleared its bindings.
