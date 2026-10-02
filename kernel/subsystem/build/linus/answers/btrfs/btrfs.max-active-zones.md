- `btrfs_get_max_active_zones()` in `fs/btrfs/zoned.c` does the computation.
  `btrfs_get_dev_zone_info()` calls it before the zone scan.
- Both limits non-zero: the smaller one is used (`min_not_zero()`), not the
  active limit.
- Neither limit reported: `min(zone_info->nr_zones / 4,
  BTRFS_DEFAULT_MAX_ACTIVE_ZONES)`, whatever the number of zones.
- Lower bound: the result is raised to `BTRFS_MIN_ACTIVE_ZONES` with `max()`.
  A small limit does not fail the mount.
- Result of `btrfs_get_max_active_zones()`: never 0, so every device starts
  with a limit.
- Raised limit: `zone_info->max_active_zones` can be larger than the limit the
  device reported.
- `-EINVAL` from `btrfs_get_max_active_zones()`: only for
  `zone_info->nr_zones < BTRFS_MIN_ACTIVE_ZONES`, with the message "not enough
  zones to mount filesystem".
- Non-zoned device with emulated zones: takes the same path and gets a
  non-zero limit. `emulate_report_zones()` reports no active zone, so
  `BTRFS_FS_ACTIVE_ZONE_TRACKING` is set.
