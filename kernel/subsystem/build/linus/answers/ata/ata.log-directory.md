- `ata_dev_configure()`: calls `ata_clear_log_directory()` as its first step
  after the enabled test, so the first `ata_log_supported()` call of each run,
  including each revalidation, reads the directory from the device again.
- `ata_dev_init()`: zeroes `dev->gp_log_dir` too; it lies between
  `ATA_DEVICE_CLEAR_BEGIN` and `ATA_DEVICE_CLEAR_END`.
- Callers: `ata_log_supported()` is static in `drivers/ata/libata-core.c` and
  every caller is reached from `ata_dev_configure()`; EH code in
  `drivers/ata/libata-sata.c` reads logs without consulting the directory.
- Cache test in `ata_read_log_directory()`: the cached version word must be
  0x0001; a device with any other version word is read again on every
  `ata_log_supported()` call.
- Wrong version word: `ata_dev_warn_once()`, return 0, the directory is used,
  no quirk is set.
- `ATA_FLAG_NO_LOG_PAGE` on the port: every directory read fails, so
  `ata_log_supported()` returns 0 for every log.
