- `nactive > zone_info->max_active_zones` with `bdev_max_active_zones(bdev) > 0`:
  `btrfs_get_dev_zone_info()` returns `-EIO`.
- Same excess with `bdev_max_active_zones(bdev)` equal to 0: it sets
  `zone_info->max_active_zones` to 0 and goes on. This covers a limit taken
  from `bdev_max_open_zones()`, from the default, or from the clamp.
- `zone_info->max_active_zones` equal to 0: arises only from that fallback.
- `btrfs_get_dev_zone_info()` has no local copy of the limit; it uses
  `zone_info->max_active_zones` only.
- `zone_info->active_zones`: always allocated and filled by the scan, also for
  a device that ends with a zero limit. On such a device it is not updated
  afterwards.
- `call_zone_finish()` on a zero-limit device: returns 0 before
  `REQ_OP_ZONE_FINISH`. `do_zone_finish()` still marks the block group full
  and inactive, so the zone on the device is not finished.
- `btrfs_load_zone_info()` on a zero-limit device: marks the stripe active
  before it looks at the zone, so a block group whose stripes are all on such
  devices has `BLOCK_GROUP_FLAG_ZONE_IS_ACTIVE` from load or creation, even on
  an empty zone.
- `BTRFS_FS_ACTIVE_ZONE_TRACKING`: a flag for the whole file system, set by
  any device that passes the check. Without it,
  `btrfs_check_meta_write_pointer()` does not call `check_bg_is_active()` and
  `btrfs_check_active_zone_reservation()` sets no reserve.
- **Unsafe usage**: failing when the active zones of an existing file system
  exceed the limit btrfs computed while `bdev_max_active_zones()` is 0.
  - Safe: fail only when `bdev_max_active_zones()` is non-zero; otherwise set
    `zone_info->max_active_zones` to 0 and set neither `active_zones_left` nor
    `BTRFS_FS_ACTIVE_ZONE_TRACKING`, as `btrfs_get_dev_zone_info()` does.
- **Unsafe usage**: taking a non-zero `bdev_max_open_zones()`, or the value of
  `zone_info->max_active_zones`, as proof that the device reported a limit.
  - Unsafe: `disk_update_zone_resources()` sets `max_open_zones` itself on a
    device with no limits, and `btrfs_get_max_active_zones()` stores a
    non-zero limit for a device that reported none.
  - Safe: test `bdev_max_active_zones()` at the time of the check, as
    `btrfs_get_dev_zone_info()` does.
