- `kvm_io_bus_unregister_dev()`: waits in
  `synchronize_srcu_expedited(&kvm->srcu)`.
- `kvm_io_bus_register_dev()`: does not wait; it frees the old bus with
  `call_srcu()`.
- Both bus calls assert `kvm->slots_lock`.
- SRCU readers take `config_lock`: `kvm_handle_guest_abort()` holds
  `kvm->srcu` across `io_mem_abort()`, and MMIO handlers such as
  `vgic_mmio_write_v3_misc()` and `vgic_mmio_read_active()` lock it.
- Locks taken before `config_lock`: `kvm->lock`, `vcpu->mutex`,
  `kvm->slots_lock`, and the `kvm->srcu` read side. `slots_lock` is outside
  `config_lock`, never inside.
- **Unsafe usage**: calling `kvm_io_bus_unregister_dev()`, or
  `vgic_unregister_redist_iodev()`, with `config_lock` held.
  - Unsafe: `synchronize_srcu_expedited()` in `kvm_io_bus_unregister_dev()`
    waits for SRCU readers, and a reader such as `vgic_mmio_read_active()`
    blocks on `config_lock`.
  - Safe: after `config_lock` is dropped and with `slots_lock` still held, as
    the last loop of `kvm_vgic_destroy()` does.
  - Safe: under `slots_lock` only, as `kvm_vgic_vcpu_destroy()` and
    `vgic_register_all_redist_iodevs()` do.
  - Safe: `__kvm_vgic_vcpu_destroy()` called under `config_lock` from
    `kvm_vgic_destroy()`; its `kvm_get_vcpu_by_id()` test is false for every
    vCPU in `kvm->vcpu_array`, so the unregister is not reached.
- **Unsafe usage**: taking `slots_lock` while `config_lock` is held, in order
  to reach a bus call.
  - Safe: `slots_lock` first, then `config_lock`, as `kvm_vgic_addr()`,
    `kvm_vgic_map_resources()` and `kvm_vgic_destroy()` do.
- Registration with `config_lock` held: does not wait for SRCU in this tree.
  `vgic_v2_map_resources()` registers `cpuif_iodev` with both locks held; the
  GICv3 redistributor and the distributor paths drop `config_lock` first.
- `kvm_vgic_destroy()` under both locks: `vgic_debug_destroy()`,
  `__kvm_vgic_vcpu_destroy()` per vCPU, and `kvm_vgic_dist_destroy()`. The
  last one includes `xa_destroy()` of `lpi_xa` and, when
  `vgic_supports_direct_irqs()`, `vgic_v4_teardown()`.
- `kvm_vgic_destroy()` after `config_lock` is dropped: only
  `vgic_unregister_redist_iodev()` per vCPU, for GICv3.
- Distributor, ITS and GICv2 CPU interface frames: no code in
  `arch/arm64/kvm/vgic/` unregisters them. `kvm_destroy_vm()` destroys the
  buses with `kvm_io_bus_destroy()` before it calls `kvm_arch_destroy_vm()`.
