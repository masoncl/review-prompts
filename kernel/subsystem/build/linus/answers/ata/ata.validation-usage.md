- `ata_dev_read_id()`: has no checksum, capacity or geometry check; the only
  validity test of IDENTIFY content is the type test, which returns `-EINVAL`.
- **Potentially unsafe usage**: returning a negative errno from code reached
  from `ata_dev_configure()` because device data fails a check.
  - Unsafe: when the data only serves an optional feature, or is a version or
    reserved field; the retry reads the same data, `ata_eh_handle_dev_fail()`
    clamps `-EINVAL` to one more attempt, and an attached device ends in
    `ata_dev_disable()`, while a new one is never attached.
  - Safe: when no command can be built without the data, as the ATAPI CDB
    length test in `ata_dev_configure()`; `cdb[ATAPI_CDB_LEN]` in
    `struct ata_queued_cmd` defines the upper bound.
  - Safe: when the data says it is another device, as `-ENODEV` from
    `ata_dev_reread_id()`; `ata_eh_handle_dev_fail()` then sets the
    `probe_mask` bit so the slot is probed again.
- **Potentially unsafe usage**: using a device-reported count as a loop bound
  or size.
  - Unsafe: when the count can exceed the buffer it indexes, or a buffer that a
    later consumer fills; `ata_scsiop_inq_b9()` writes `nr_cpr` descriptors
    into `ata_scsi_rbuf` with no check of its own.
  - Safe: `ata_dev_config_cpr()` rejects a count above `ATA_DEV_MAX_CPR` or
    larger than the log it read, warns, and sets `dev->cpr_log` to NULL.
  - Safe: `ata_identify_page_supported()` loops on the `u8` count at offset 8
    over entries from offset 9, which stays inside `dev->sector_buf` of
    `ATA_SECT_SIZE` bytes.
- R/W multiple count in `ata_dev_configure()`: taken only if both values are
  powers of two and the count is within the maximum; otherwise `multi_count`
  stays 0 and nothing fails.
