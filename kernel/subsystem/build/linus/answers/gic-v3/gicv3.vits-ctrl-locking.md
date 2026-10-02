- `vgic_its_ctrl()` order: `kvm->lock`, all vCPU mutexes through
  `kvm_trylock_all_vcpus()`, `kvm->arch.config_lock`, `its->its_lock`.
- `vgic_its_attr_regs_access()`: the same first three; it takes no ITS mutex
  itself, the register handlers take `cmd_lock` or `its_lock` themselves, for
  example `vgic_mmio_write_its_cbaser()`.
- `-EBUSY`: a literal in both functions; `kvm_trylock_all_vcpus()` itself
  returns `-EINTR`.
- There is no save_its_tables_in_progress flag; `vgic_write_guest_lock()` in
  `arch/arm64/kvm/vgic/vgic.h` sets `dist->table_write_in_progress` around
  each write.
- Documented sequence in `Documentation/virt/kvm/devices/arm-vgic-its.rst`:
  1. guest memory and vCPUs
  2. redistributors
  3. ITS base address
  4. GITS_CBASER
  5. all other GITS registers except GITS_CTLR
  6. `KVM_DEV_ARM_ITS_RESTORE_TABLES`
  7. GITS_CTLR
  8. KVM_IRQFD assignments for MSIs
- GITS_IIDR: not a step of its own; the documentation requires it only before
  `KVM_DEV_ARM_ITS_RESTORE_TABLES`.
- `vgic_mmio_write_its_cbaser()`: zeroes `creadr` and `cwriter`, which is why
  GITS_CREADR follows GITS_CBASER.
- Enabled ITS: writes to GITS_CBASER and GITS_BASER are ignored, and
  `vgic_mmio_uaccess_write_its_creadr()` returns `-EBUSY`, which is why
  GITS_CTLR is the last register restored.
- `vgic_mmio_write_its_baser()`: a changed value frees the device or
  collection list, so GITS_BASER precedes the table restore.
- GITS_CWRITER from userspace: uses `vgic_mmio_write_its_cwriter()`, the
  guest's handler, which processes commands if the ITS is enabled.
