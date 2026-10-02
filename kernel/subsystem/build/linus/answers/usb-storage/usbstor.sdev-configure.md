- No `sdev` field is forced for every device type. The unconditional
  settings sit in the `TYPE_DISK` branch; the else branch for a non-disk
  device sets only `use_10_for_ms`, plus `no_read_disc_info` with
  `US_FL_NO_READ_DISC_INFO`.
- `use_10_for_ms` for a disk: set only when the subclass is neither
  `USB_SC_SCSI` nor `USB_SC_CYP_ATACB`.
- `last_sector_bug`: unconditional for disks. `us->use_last_sector_hacks` is
  the one skipped by `US_FL_FIX_CAPACITY`, `US_FL_CAPACITY_OK`,
  `US_FL_SCM_MULT_TARG` or a non-Bulk protocol.
- `try_rc_10_first`: set for disks unless `US_FL_NEEDS_CAP16`.
- `skip_ms_page_3f`: set only for a disk with `US_FL_NO_WP_DETECT` or
  `US_FL_ALWAYS_SYNC`.
- `US_FL_NOT_LOCKABLE`: tested outside the type branch, for any device type.
- Not done in `sdev_configure()`: it does not write `scsi_level`,
  `use_10_for_rw` or the DMA alignment. `.dma_alignment = 511` is in the
  template; `pdt_1f_for_no_lun` is set in `target_alloc()` for `USB_SC_UFI`.
- `lim->max_hw_sectors` normally arrives holding the template's 240, then
  the first matching case applies:
  1. `US_FL_MAX_SECTORS_64` or `US_FL_MAX_SECTORS_MIN`: `min()` of the
     current value and 64, or `PAGE_SIZE >> 9` with `US_FL_MAX_SECTORS_MIN`.
  2. `TYPE_TAPE`: 0x7FFFFF.
  3. speed `USB_SPEED_SUPER` or above: 2048.
  4. otherwise unchanged.
- After that, for every device: clamped to `dma_max_mapping_size()` of
  `us->pusb_dev->bus->sysdev`, in sectors.
- The comment in `sdev_configure()` about `sdev_init()`: it covers the whole
  `TYPE_DISK`/else block. The reason given is that `sdev_init()` is called
  before the device type is known; it adds that these settings therefore
  cannot be overridden through scsi devinfo.
