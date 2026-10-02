- Locks: the caller holds `kvm->slots_lock` (asserted).
  `kvm->arch.config_lock` is taken inside and dropped before
  `kvm_io_bus_register_dev()`, so the bus call runs under `slots_lock` only.
- Rollback in `vgic_register_all_redist_iodevs()`: unregisters the vCPUs
  before the failing one. The failing vCPU itself was never put on the bus.
- Rollback in `vgic_v3_set_redist_base()`: retakes `config_lock` and calls
  `vgic_v3_free_redist_region()`, which clears `vgic_cpu.rdreg` of every vCPU
  that points to the region and frees it.
- `vgic_unregister_redist_iodev()`: only removes the device from the bus. It
  does not reset `rd_iodev.base_addr`, and nothing in the rollback resets
  `rdreg_index`.
- `rd_iodev.base_addr` is set back to `VGIC_ADDR_UNDEF` only in
  `kvm_vgic_vcpu_init()` and `__kvm_vgic_vcpu_destroy()`.
- Successfully created vCPU: the `vgic_unregister_redist_iodev()` call is in
  `kvm_vgic_destroy()`, in the loop after `config_lock` is dropped.
  `__kvm_vgic_vcpu_destroy()` skips it, because `kvm_get_vcpu_by_id()`
  returns that vCPU.
- That call in `kvm_vgic_destroy()` finds no bus: `kvm_destroy_vm()` has
  already destroyed the buses and set `kvm->buses[]` to NULL, so
  `kvm_io_bus_unregister_dev()` returns 0 at its `!bus` test.
- vCPU whose creation failed: unregistered in `__kvm_vgic_vcpu_destroy()`,
  reached through `kvm_vgic_vcpu_destroy()` with `slots_lock` only.
- Paths that reach it for a failed vCPU: the two error exits of
  `kvm_arch_vcpu_create()`, and `kvm_arch_vcpu_destroy()` from the error
  labels of `kvm_vm_ioctl_create_vcpu()` in `virt/kvm/kvm_main.c`.
