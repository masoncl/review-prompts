- `flags` has no lock: it is written at host setup and from EH callbacks
  without `ap->lock`, for example by `sil24_pmp_attach()`.
- `pflags` is protected by `ap->lock`; writes before the port is visible are
  unlocked, for example in `ata_port_alloc()`.
- `pflags` reads are often unlocked, for example the `ATA_PFLAG_UNLOADING`
  test in `ata_scsi_port_error_handler()`.
- **Potentially unsafe usage**: writing `ap->pflags` without `ap->lock`.
  - Unsafe: once interrupts or EH can run for the port;
    `__ata_port_freeze()` and `ata_eh_set_pending()` do plain read-modify-write
    of `pflags` under `ap->lock`.
  - Safe: before the port is visible to anything else, as `ata_port_alloc()`
    does.
- `end_eh`: called with `ap->lock` held and EH ownership still held.
- `post_internal_cmd`: called from `ata_exec_internal()` with `ap->lock`
  dropped; EH ownership is held only if the caller owned it.
- `freeze`: the libata core calls it through `__ata_port_freeze()` under
  `ap->lock`; the shutdown paths `ata_pci_shutdown_one()` and
  `ahci_platform_shutdown()` call it with no libata lock.
- `lost_interrupt`: under `ap->lock` in `ata_scsi_cmd_error_handler()`, before
  EH ownership is taken.
- `port_suspend` and `port_resume`: EH ownership, no `ap->lock`.
- Lock requirements are annotated in this tree, for example
  `__must_hold(ap->lock)` on `ata_scsi_translate()`.
