- Guest entry points: `dispatch_mmio_read()` and `dispatch_mmio_write()` in
  `arch/arm64/kvm/vgic/vgic-mmio.c`, installed in `kvm_io_gic_ops`; there is
  no vgic_mmio_read() or vgic_mmio_write() in this tree.
- `IODEV_REDIST` guest access: the handler gets `iodev->redist_vcpu`, the
  owner of the frame, not the vCPU that trapped.
- Redistributor access through `vgic_uaccess()`: the on-stack device built by
  `vgic_v3_redist_uaccess()` leaves `redist_vcpu` NULL, so the handler gets
  the vCPU chosen by the attribute.
- Userspace slots: `REGISTER_DESC_WITH_BITS_PER_IRQ()` (in
  `arch/arm64/kvm/vgic/vgic-mmio.h`) and
  `REGISTER_DESC_WITH_BITS_PER_IRQ_SHARED()` (in
  `arch/arm64/kvm/vgic/vgic-mmio-v3.c`) also take `uaccess_read` and
  `uaccess_write` arguments; passing NULL selects the guest handler.
- `REGISTER_DESC_WITH_BITS_PER_IRQ_SHARED()`: expands to two regions; the
  first, covering the private IRQs, is hard-wired to `vgic_mmio_read_raz()` and
  `vgic_mmio_write_wi()` for guest and userspace alike.
- Userspace access with no region, or one that fails `check_region()`:
  `vgic_uaccess_read()` stores 0 and returns 0, `vgic_uaccess_write()` returns
  0; neither returns `-ENXIO`.
- `-ENXIO` for an unknown offset: comes from `vgic_v3_has_attr_regs()`, which
  serves only `vgic_v3_has_attr()`, and from the ITS path.
- Userspace width: `vgic_uaccess_read()` and `vgic_uaccess_write()` always
  pass `sizeof(u32)`, so an offset that is not 4-byte aligned is RAZ/WI with
  return 0.
- `uaccess_write` return value: becomes the result of `vgic_uaccess()`; the
  fallback to `write` returns 0.
- ITS userspace access: `vgic_its_attr_regs_access()` in
  `arch/arm64/kvm/vgic/vgic-its.c` calls neither `vgic_uaccess()` nor
  `check_region()`; it calls `vgic_find_mmio_region()` directly.
- ITS access length: 8 if the region has `VGIC_ACCESS_64bit`, else 4.
- ITS errors: misaligned offset gives `-EINVAL`; no region, or ITS base not
  set, gives `-ENXIO`.
- ITS callbacks: writes use `uaccess_its_write` if set, else `its_write`;
  reads always use `its_read`, `uaccess_read` is not consulted.
