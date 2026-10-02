- `error_handler` must be non-NULL after `ata_finalize_port_ops()`:
  `ata_scsi_port_error_handler()` is its only caller and has no NULL test.
- The entry copy and clear of `eh_info` runs before the call, whether or not
  the handler is then called.
- The handler is skipped, and `ata_eh_finish()` called instead, when
  `ATA_PFLAG_UNLOADING` or `ATA_PFLAG_SUSPENDED` is set, or when
  `ata_adapter_is_online()` is false (PCI channel offline).
- `ata_eh_unload()` runs before `ata_eh_finish()` only when
  `ATA_PFLAG_UNLOADING` is set and `ATA_PFLAG_UNLOADED` is not.
- An ops table with no `.inherits` chain to `ata_base_port_ops` must set
  `error_handler`, `sched_eh` and `end_eh` itself; all three are called
  without a NULL test. For example `ata_dummy_port_ops` and `sas_sata_ops` in
  `drivers/scsi/libsas/sas_ata.c`.
- `ata_sff_port_ops` sets `ata_sff_error_handler()`, and `ata_bmdma_port_ops`
  sets `ata_bmdma_error_handler()`; each ends in the next one down to
  `ata_std_error_handler()`.
- The `error_handler` member is declared
  `__must_hold(&ap->host->eh_mutex)` in `include/linux/libata.h`; handlers
  carry the same annotation, for example `ata_sff_error_handler()`.
