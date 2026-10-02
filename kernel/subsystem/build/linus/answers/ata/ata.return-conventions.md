- Return types: `ata_exec_internal()`, `ata_read_log_page()` and
  `ata_dev_set_feature()` are declared `unsigned int` and return a mask;
  `ata_dev_read_id()`, `ata_dev_reread_id()`, `ata_dev_configure()` and
  `ata_dev_revalidate()` are declared `int` and return an errno; see the
  definitions in `drivers/ata/libata-core.c`.
- `ata_dev_read_id()`: never returns `-EAGAIN`; its values are 0, `-ENODEV`
  (unsupported class), `-ENOENT`, `-EIO` and `-EINVAL`.
- `ata_dev_read_id()` returns `-ENOENT` in three cases: `AC_ERR_NODEV_HINT`
  set; both IDENTIFY flavours failed with `err_mask == AC_ERR_DEV` and
  `ATA_ABORTED`; an ATA device on an `ATA_HOST_IGNORE_ATA` host.
- `ata_dev_read_id()` on a SEMB-signature device whose IDENTIFY fails: returns
  0 and sets `*p_class` to `ATA_DEV_SEMB_UNSUP`; a caller must look at the
  class as well as the return value.
- `ata_dev_configure()`: returns `-EAGAIN` from `ata_do_link_spd_quirk()`;
  returns 0 when the device is not enabled and when it disables the device
  itself (`ATA_QUIRK_DISABLE`, ATAPI not allowed).
- **Potentially unsafe usage**: returning an `AC_ERR_*` mask from a function
  declared `int`.
  - Unsafe: when a caller tests the result with `< 0`, or passes it on to
    `ata_eh_handle_dev_fail()`, whose `switch` matches negative errnos only.
  - Safe: when no caller reads the result, as with `eject_tray()` in
    `drivers/ata/libata-zpodd.c`, whose only caller `zpodd_post_poweron()`
    discards it.
