- Conditions counted as active: four, not three. The switch in
  `btrfs_get_dev_zone_info()` also has `BLK_ZONE_COND_ACTIVE`.
- `BLK_ZONE_COND_ACTIVE`: the case that is hit on a zoned device.
  `btrfs_get_dev_zones()` reads through `blkdev_report_zones_cached()`, which
  reports implicitly open, explicitly open and closed zones under this one
  condition.
- `bdev_max_open_zones()` and `bdev_max_active_zones()`: return what the block
  layer stored, which may differ from what the device reported. See
  `disk_update_zone_resources()` in `block/blk-zoned.c`.
- Device with neither limit, a zone write plug pool and more than
  `BLK_ZONE_WPLUG_DEFAULT_POOL_SIZE` (128) sequential zones:
  `bdev_max_open_zones()` returns 128, `bdev_max_active_zones()` returns 0.
- Limit that is >= the number of sequential zones:
  `disk_update_zone_resources()` resets it to 0 although the device reported
  a limit; when both limits are then 0, the bullet above applies to
  `bdev_max_open_zones()`.
- `blk_validate_zoned_limits()` in `block/blk-settings.c`: returns `-EINVAL`
  for `max_open_zones > max_active_zones`, only when `max_active_zones` is
  non-zero.
