- Pre-init precondition: vCPU 0 must exist; `vgic_v3_parse_attr()` returns
  `-EINVAL` for `KVM_DEV_ARM_VGIC_GRP_DIST_REGS` otherwise.
- `reg_allowed_pre_init()`: does not look at the direction, so the read
  handler `vgic_mmio_read_v3_misc()` also runs before init for `GICD_IIDR`
  and `GICD_TYPER2`.
- There is no vgic_uaccess_write_iidr() here; the `GICD_IIDR` case is inside
  `vgic_mmio_uaccess_write_v3_misc()`.
- `GICD_IIDR` write: any difference from the current value outside
  `GICD_IIDR_REVISION_MASK` gives `-EINVAL`.
- `GICD_IIDR` write after init: accepted; that case has no
  `vgic_initialized()` test.
- `GICD_TYPER2` write, in order: same value as read back returns 0; a changed
  value after init gives `-EBUSY`; a change outside `GICD_TYPER2_nASSGIcap`
  gives `-EINVAL`; a non-zero value without `system_supports_direct_sgis()`
  gives `-EINVAL`.
- `GICD_TYPER2` write stores `nassgicap` in `struct vgic_dist`, not
  `nassgireq`; clearing it is allowed on any host.
- `spis` before init: NULL until `kvm_vgic_dist_init()` runs from
  `vgic_init()`, while `nr_spis` may already be non-zero from
  `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`.
- **Unsafe usage**: allowing in `reg_allowed_pre_init()` an offset whose read
  or write handler reaches `spis` of `struct vgic_dist`; `vgic_get_irq()`
  indexes it for any SPI INTID below `nr_spis + VGIC_NR_PRIVATE_IRQS`.
  - Safe: a handler that touches only scalar fields of `struct vgic_dist`, as
    the `GICD_IIDR` and `GICD_TYPER2` cases of
    `vgic_mmio_uaccess_write_v3_misc()` do.
- **Unsafe usage**: a userspace write handler that takes `config_lock`, or
  falls through to a guest handler that takes it; `vgic_v3_attr_regs_access()`
  calls the handler with `kvm->lock`, every vCPU mutex and `config_lock` held.
  - Safe: `vgic_mmio_uaccess_write_v3_misc()` has its own `GICD_CTLR` case
    and reaches `vgic_mmio_write_v3_misc()` only for `GICD_TYPER`, which
    returns without locking.
  - Safe: `vgic_mmio_uaccess_write_cactive()` calls
    `__vgic_mmio_write_cactive()` directly, where the guest handler
    `vgic_mmio_write_cactive()` takes the lock first.
- **Unsafe usage**: a userspace write handler changing, once
  `vgic_initialized()` is true, a field that `vgic_init()` has read.
  - Safe: the `GICD_TYPER2` case returns `-EBUSY` for a changed value;
    `vgic_init()` reads `nassgicap` through `vgic_supports_direct_irqs()` to
    decide whether `vgic_v4_init()` runs.
  - Safe: `implementation_rev` after init; it is read only when a register is
    read, for GICv3 in `vgic_mmio_read_v3_misc()` and
    `vgic_mmio_read_v3r_ctlr()`.
