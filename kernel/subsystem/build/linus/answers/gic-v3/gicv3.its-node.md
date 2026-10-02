- `struct its_node` has two locks: `lock` (`raw_spinlock_t`) and
  `dev_alloc_lock` (`struct mutex`).
- `its_lock` in `drivers/irqchip/irq-gic-v3-its.c` is a file-scope raw
  spinlock, not a field of `struct its_node` and not a mutex.
- `cmd_lock` is a field of KVM's `struct vgic_its` in
  `include/kvm/arm_vgic.h`, not of `struct its_node`; there is no
  its_dev_lock in this tree.
- `lock` covers both the command queue (`cmd_write`, the slots,
  `GITS_CWRITER`) and `its_device_list`; there is no separate device-list
  lock.
- `dev_alloc_lock` is the only lock in the node that may be held across a
  sleep.
- `dev_alloc_lock` is taken in `its_msi_prepare()` and `its_msi_teardown()`
  of `drivers/irqchip/irq-gic-v3-its.c`.
- `its_irq_domain_free()` takes neither lock of the node.
- `its_init_vpe_domain()` calls `its_create_device()` for the proxy device
  without `dev_alloc_lock`.
- `its_restore_enable()` resets `cmd_write` and `GITS_CWRITER` holding only
  `its_lock`, not `lock`.
- `its_nodes` links nodes through the `entry` field.
- `its_lock` is taken in `its_probe_one()`, `its_cpu_init_collections()`,
  `its_save_disable()` and `its_restore_enable()`.
- Other walks of `its_nodes` do not take `its_lock`, for example
  `its_send_vmovp()`, `get_its_list()` and `its_alloc_vpe_table()`.
- `its_nodes` only grows: `its_probe_one()` holds the only `list_add()` to
  it, and nothing unlinks a node.
- `vmovp_lock` is a file-scope raw spinlock, taken only in
  `its_send_vmovp()` and only when `its_list_map` is non-zero.
- `lock` is the innermost lock: commands are sent with `its_lock`,
  `vmovp_lock`, `vpe_lock` or `vmapp_lock` held.
