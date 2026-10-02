- `btrfs_is_zoned()` in `fs/btrfs/fs.h`: `IS_ENABLED(CONFIG_BLK_DEV_ZONED)`
  and `fs_info->zone_size > 0`; there is no BTRFS_FS_ZONED flag, and
  `device->zone_info` does not decide it.
- `btrfs_fs_incompat(fs_info, ZONED)`: the gate for both
  `btrfs_get_dev_zone_info()` and `btrfs_check_zoned_mode()`; device type
  never turns zoned mode on, and without the flag `btrfs_check_zoned_mode()`
  returns `-EINVAL` if any device is zoned.
- `fs_info->zone_size` has two writers: `btrfs_check_zoned_mode()` and
  `calculate_emulated_zone_size()`.
- `calculate_emulated_zone_size()` runs from `btrfs_get_dev_zone_info()` for
  a non-zoned device while `fs_info->zone_size` is 0, so with such a device
  `btrfs_is_zoned()` is already true before `btrfs_check_zoned_mode()` runs
  in `open_ctree()`.
- Emulated zone size: the length of a dev extent from `fs_info->dev_root`;
  there is no BTRFS_EMULATED_ZONE_SIZE and no fixed default.
- Zoned and non-zoned devices in one fs: accepted only if the dev extent
  length equals the zoned devices' zone size; otherwise
  `btrfs_check_zoned_mode()` fails on unequal zone sizes.
- Host-aware and host-managed: fs/btrfs does not distinguish them; the only
  device test is `bdev_is_zoned()`.
- Device with no `bdev` (missing): skipped by
  `btrfs_get_dev_zone_info_all_devices()` and by the loop in
  `btrfs_check_zoned_mode()`.
- Device added or used as replace target after mount:
  `btrfs_check_device_zone_type()` in `fs/btrfs/zoned.h` admits any non-zoned
  device on a zoned fs, and a zoned one only with equal zone size.
- Without `CONFIG_BLK_DEV_ZONED`: `btrfs_get_dev_zone_info()` and
  `btrfs_check_zoned_mode()` are stubs in `fs/btrfs/zoned.h`; the
  `-EOPNOTSUPP` in the `btrfs_check_zoned_mode()` stub is behind
  `btrfs_is_zoned()`, which is constant false there.
- `btrfs_check_zoned_mode()` failures besides unequal zone sizes,
  `MIXED_GROUPS` and `NODATACOW`: `blk_validate_limits()` on the stacked
  limits; zone size not aligned to `BTRFS_STRIPE_LEN`; the `SPACE_CACHE`
  mount option (`btrfs_check_mountopts_zoned()`).
- `btrfs_check_zoned_mode()` tests no feature flag other than `ZONED` and
  `MIXED_GROUPS`, and no active-zone limit.
- Zone size not a power of two: `btrfs_get_dev_zone_info()` has only
  `ASSERT(is_power_of_two_u64(zone_sectors))`, no error return; for a zoned
  device `btrfs_sb_log_location_bdev()` returns `-EINVAL`, which fails
  `btrfs_read_disk_super()`.
- Device size not a multiple of the zone size: not rejected; `nr_zones` is
  rounded up to count the last partial zone.
- Zone report for a zoned device: `btrfs_get_dev_zones()` calls
  `blkdev_report_zones_cached()`, not `blkdev_report_zones()`; a report of
  zero zones returns `-EIO`.
- Superblock log check: skipped for a mirror whose zone pair does not fit in
  `nr_zones`, and when the first zone of the pair is conventional.
- Superblock log check otherwise: any `sb_write_pointer()` error except
  `-ENOENT` becomes `-EUCLEAN`; the invalid states are in the table comment
  in `sb_write_pointer()`.
- `calculate_emulated_zone_size()` errors also fail
  `btrfs_get_dev_zone_info()`: `-ENOMEM`, a tree search error, or `-EUCLEAN`
  when no item is found.
