- Exported: only `sysfs_group_change_owner()` and
  `sysfs_groups_change_owner()`, both `EXPORT_SYMBOL_GPL()`.
- Not exported, so not callable from a module: `device_change_owner()`,
  `sysfs_change_owner()`, `sysfs_file_change_owner()`,
  `sysfs_link_change_owner()`.
- `struct class` has no `dev_attrs` member; `dev_groups` is its only set of
  device groups.
- Power groups: `dpm_sysfs_change_owner()` in `drivers/base/power/sysfs.c`
  leaves out `pm_qos_resume_latency_attr_group` and
  `pm_qos_flags_attr_group`.
- Files and the group from `device_add_attrs()` that
  `device_attrs_change_owner()` leaves out: `dev_attr_waiting_for_supplier`,
  `dev_attr_removable`, `dev_attr_physical_location_group`.
- Hidden attribute: `sysfs_group_attrs_change_owner()` calls `is_visible`,
  `is_visible_const` or `is_bin_visible` with the index `create_files()` uses;
  0 skips the entry.
- `SYSFS_GROUP_INVISIBLE` from a callback during the walk: stops the walk of
  that array, and the remaining entries keep the old owner.
- Node missing while the callback reports it visible, or the group has no
  callback: `-ENOENT`, and the whole walk fails.
- Hidden named directory: `sysfs_group_change_owner()` looks the directory up
  before any callback and returns `-ENOENT` when it is absent.
- **Unsafe usage**: a named group that can return `SYSFS_GROUP_INVISIBLE`, in
  a set the walk covers on a device whose owner can change; while hidden,
  `device_change_owner()` fails with `-ENOENT`.
  - Safe: an unnamed group whose callback returns 0 for the entries left out
    at creation, as `netdev_phys_group` in `net/core/net-sysfs.c`;
    `sysfs_group_attrs_change_owner()` skips those entries.
