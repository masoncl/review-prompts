- `kvm_get_kvm_safe()`: called only by debugfs `open` handlers (for example
  `kvm_debugfs_open()`, `kvm_mmu_rmaps_stat_open()`) and by
  `vfio_device_get_kvm_safe()` in `drivers/vfio/vfio_main.c`.
- `vm_list` walkers: take no reference at all; those in
  `virt/kvm/kvm_main.c` hold `kvm_lock` for the whole walk, for example
  `vm_stat_get()`.
- A VM on `vm_list` can already have `users_count` zero: `kvm_destroy_vm()`
  removes it under `kvm_lock` only after the last put.
- `kvm_put_kvm_no_destroy()`: every caller undoes a `kvm_get_kvm()` taken for
  an `anon_inode_getfd()` that then made no fd; nothing in `kvm_destroy_vm()`
  teardown calls it.
- `virt/kvm/async_pf.c`: does not call `kvm_get_kvm()`; async page fault work
  holds no VM reference.
- File descriptors holding a reference also include the VM and vCPU stats fds
  (`kvm_vm_stats_release()`, `kvm_vcpu_stats_release()`) and a guest_memfd
  file (`kvm_gmem_release()` in `virt/kvm/guest_memfd.c`).
- powerpc adds two anon inode fds: the fds from `kvm_vm_ioctl_get_htab_fd()`
  and `kvm_vm_ioctl_create_spapr_tce()`.
- irqfd and ioeventfd: hold no VM reference; `virt/kvm/eventfd.c` never calls
  `kvm_get_kvm()`, and `kvm_vm_release()` tears irqfds down with
  `kvm_irqfd_release()`.
- **Unsafe usage**: taking the VM reference for a new fd after the fd is
  installed; userspace can close it at once and the release handler calls
  `kvm_put_kvm()`.
  - Safe: `kvm_get_kvm()` before `anon_inode_getfd()`, undone with
    `kvm_put_kvm_no_destroy()` on failure, as `kvm_ioctl_create_device()`
    does; `kvm_device_release()` is the put it pairs with.
  - Safe: `kvm_get_kvm()` between file creation and `fd_install()`, with no
    undo needed, as `kvm_vm_ioctl_get_stats_fd()` and `__kvm_gmem_create()`
    do.
