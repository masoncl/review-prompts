- `kvm_io_bus_register_dev()`: does not wait; it publishes the new bus and
  frees the old one with `call_srcu()` and `__free_bus()`.
- `kvm_io_bus_unregister_dev()`: waits with `synchronize_srcu_expedited()`,
  then frees.
- `kvm_destroy_vm()`: calls `srcu_barrier(&kvm->srcu)` before
  `cleanup_srcu_struct(&kvm->srcu)`, for those pending `call_srcu()`
  callbacks.
- Order in `kvm_destroy_vm()`: `cleanup_srcu_struct(&kvm->irq_srcu)` first,
  with no barrier, then the barrier and cleanup of `srcu`.
- Memslots: the old set is not freed; it becomes the inactive set in
  `__memslots` and is reused. What is freed is slot objects: the replaced
  `struct kvm_memory_slot` in `kvm_commit_memory_region()`, and the temporary
  INVALID copy in `kvm_set_memslot()`.
- `kvm_set_irq_routing()`: calls `synchronize_srcu_expedited()` on `irq_srcu`
  after it drops `irq_lock`, not under it.
- `kvm_get_bus()` in `include/linux/kvm_host.h`: update side accessor, needs
  `slots_lock`; readers use `kvm_get_bus_srcu()`.
