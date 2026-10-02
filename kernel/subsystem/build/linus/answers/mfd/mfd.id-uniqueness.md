- Scope of uniqueness: the whole platform bus, including platform devices that
  no MFD parent created.
- Duplicate under the same parent: `kobject_add()` in `device_add()` fails.
- Duplicate under different parents: `sysfs_create_link()` in
  `bus_add_device()` fails; both cases return `-EEXIST` and log through
  `sysfs_warn_dup()`.
- `insert_resource()` in `platform_device_add()`: fails when a range partly
  overlaps one already inserted, whatever the names are; an identical or
  nested range is accepted.
- `mfd_add_devices()` on failure: calls `mfd_remove_devices(parent)`, which
  removes every MFD child of the parent, also those added by earlier calls.
  - Cells with `level` `MFD_DEP_LEVEL_HIGH` are left in place.
  - When the failing cell is the first of the call, nothing is removed.
- **Potentially unsafe usage**: a constant `id` argument, such as 0 or
  `PLATFORM_DEVID_NONE`.
  - Unsafe: with a constant other than `PLATFORM_DEVID_AUTO`, when a second
    instance of the parent is registered; its first child fails with
    `-EEXIST` in `bus_add_device()`.
  - Safe: `PLATFORM_DEVID_AUTO`, as `mfd_add_hotplug_devices()` in
    `include/linux/mfd/core.h` passes; `platform_devid_ida` makes each name
    unique.
  - Safe: a base allocated per instance, as from `intel_lpss_devid_ida` in
    `drivers/mfd/intel-lpss.c`, and freed only after the children are
    removed, as `intel_lpss_remove()` does; the sums `base + cell->id` of two
    instances must differ for cells of the same `name`, since
    `platform_device_add()` builds the name from the sum.
- **Potentially unsafe usage**: two cells of one parent with the same `name`.
  - Unsafe: with a base other than `PLATFORM_DEVID_AUTO` and equal `cell->id`;
    the second cell fails with `-EEXIST` in `kobject_add()`.
  - Safe: distinct `cell->id` values, as in `lm3533_bl_devs` in
    `drivers/mfd/lm3533-core.c`; `platform_device_add()` puts the sum in the
    name. This holds with a `PLATFORM_DEVID_NONE` base too, where the names
    are `<name>` and `<name>.<k-1>`.
  - Safe: `PLATFORM_DEVID_AUTO`, where `platform_device_add()` allocates a
    separate number for each cell, as for `vexpress_sysreg_cells` in
    `drivers/mfd/vexpress-sysreg.c`.
