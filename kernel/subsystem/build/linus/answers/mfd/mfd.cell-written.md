- `drivers/mfd/88pm800.c`: `onkey_devs` and `regulator_devs` are
  `static const`; `rtc_devs` is the only cell array there that is not.
- `drivers/mfd/intel-lpss.c`: the per-device copy is made in
  `intel_lpss_assign_devs()`; `intel_lpss_probe()` then writes only `swnode`
  and `ignore_resource_conflicts` into it.
- `intel_lpss_idma64_cell`: not copied by the driver; `intel_lpss_probe()`
  registers it straight from the `static const` object.
- **Unsafe usage**: writing a member of a file-scope cell on only some paths
  of probe; the cell keeps what an earlier probe wrote, and
  `platform_device_add_data()` then copies `pdata_size` bytes from the old
  `platform_data` pointer.
  - Safe: write every member that probe can set on every path, including the
    value that clears it, as `as3711_i2c_probe()` does.
  - Safe: copy a `static const` template for each device and write the copy,
    as `intel_lpss_assign_devs()` does with `devm_kmemdup()`.
  - Safe: build the cells for each probe on the stack, as `sky81452_probe()`
    does, or on the heap and free them after the add, as
    `skl_int3472_tps68470_probe()` does; `mfd_add_device()` has taken its own
    copy by then.
